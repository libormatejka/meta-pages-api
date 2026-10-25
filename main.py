import os
import json
import uuid
import requests
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery
from google.oauth2 import service_account

# --- KONFIGURACE Z PROMĚNNÝCH PROSTŘEDÍ ---
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')

GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BQ_DATASET = os.environ.get('BQ_DATASET')

PAGE_TABLE = 'fb_page_daily'
POST_TABLE = 'fb_post_daily'

GRAPH_URL = 'https://graph.facebook.com/v25.0'
PAGE_METRICS = [
    'page_media_view',
    'page_total_media_view_unique',
    'page_post_engagements',
    'page_views_total',
    'page_video_views',
]
POST_METRICS = ['post_media_view', 'post_clicks', 'post_reactions_by_type_total']

PAGE_DAYS_BACK = 3    # metriky stránky se zpětně dopočítávají, přepisujeme poslední dny
POST_DAYS_BACK = 30   # starší příspěvky se skoro nemění

PAGE_SCHEMA = [
    bigquery.SchemaField('date', 'DATE'),
    bigquery.SchemaField('page_id', 'STRING'),
    bigquery.SchemaField('followers_count', 'INT64'),
    *[bigquery.SchemaField(m, 'INT64') for m in PAGE_METRICS],
    bigquery.SchemaField('ingested_at', 'TIMESTAMP'),
]
POST_SCHEMA = [
    bigquery.SchemaField('snapshot_date', 'DATE'),
    bigquery.SchemaField('page_id', 'STRING'),
    bigquery.SchemaField('post_id', 'STRING'),
    bigquery.SchemaField('created_time', 'TIMESTAMP'),
    bigquery.SchemaField('message', 'STRING'),
    bigquery.SchemaField('permalink_url', 'STRING'),
    bigquery.SchemaField('post_media_view', 'INT64'),
    bigquery.SchemaField('post_clicks', 'INT64'),
    bigquery.SchemaField('reactions_total', 'INT64'),
    bigquery.SchemaField('comments_total', 'INT64'),
    bigquery.SchemaField('shares_total', 'INT64'),
    bigquery.SchemaField('reactions_by_type', 'STRING'),
    bigquery.SchemaField('ingested_at', 'TIMESTAMP'),
]


def fb_get(url, params=None):
    response = requests.get(url, params=params, timeout=60)
    if response.status_code != 200:
        # Vypisujeme jen tělo chyby, URL obsahuje token
        print("❌ Chyba z Facebook API:")
        print(response.text)
        response.raise_for_status()
    return response.json()


def fetch_facebook_data(today):
    page_since = (today - timedelta(days=PAGE_DAYS_BACK)).isoformat()
    post_since = (today - timedelta(days=POST_DAYS_BACK)).isoformat()
    until = (today + timedelta(days=1)).isoformat()

    fields = (
        f"followers_count,"
        f"insights.metric({','.join(PAGE_METRICS)}).period(day)"
        f".since({page_since}).until({today.isoformat()}),"
        f"posts.since({post_since}).until({until}).limit(25)"
        f"{{id,created_time,message,permalink_url,"
        f"reactions.summary(true).limit(0),comments.summary(true).limit(0),shares,"
        f"insights.metric({','.join(POST_METRICS)})}}"
    )
    data = fb_get(f"{GRAPH_URL}/{FB_PAGE_ID}",
                  {'fields': fields, 'access_token': FB_ACCESS_TOKEN})

    posts = list(data.get('posts', {}).get('data', []))
    next_url = data.get('posts', {}).get('paging', {}).get('next')
    while next_url:
        page = fb_get(next_url)
        posts.extend(page.get('data', []))
        next_url = page.get('paging', {}).get('next')

    return data, posts


def build_page_rows(data, today, ingested_at):
    rows = {}
    for item in data.get('insights', {}).get('data', []):
        for v in item.get('values', []):
            # end_time je konec dne, data patří předchozímu dni
            end = datetime.strptime(v['end_time'], '%Y-%m-%dT%H:%M:%S%z')
            day = (end - timedelta(days=1)).date().isoformat()
            row = rows.setdefault(day, {
                'date': day, 'page_id': FB_PAGE_ID, 'ingested_at': ingested_at,
            })
            row[item['name']] = v.get('value', 0)

    # followers_count je snímek v okamžiku stažení, ukládáme ho k včerejšku
    yesterday = (today - timedelta(days=1)).isoformat()
    row = rows.setdefault(yesterday, {
        'date': yesterday, 'page_id': FB_PAGE_ID, 'ingested_at': ingested_at,
    })
    row['followers_count'] = data.get('followers_count')
    return list(rows.values())


def build_post_rows(posts, today, ingested_at):
    rows = []
    for p in posts:
        metrics = {}
        for item in p.get('insights', {}).get('data', []):
            values = item.get('values', [])
            metrics[item['name']] = values[0].get('value') if values else None
        by_type = metrics.get('post_reactions_by_type_total') or {}
        rows.append({
            'snapshot_date': today.isoformat(),
            'page_id': FB_PAGE_ID,
            'post_id': p['id'],
            'created_time': p.get('created_time'),
            'message': p.get('message'),
            'permalink_url': p.get('permalink_url'),
            'post_media_view': metrics.get('post_media_view') or 0,
            'post_clicks': metrics.get('post_clicks') or 0,
            'reactions_total': p.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments_total': p.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares_total': p.get('shares', {}).get('count', 0),
            'reactions_by_type': json.dumps(by_type),
            'ingested_at': ingested_at,
        })
    return rows


def get_bq_client():
    creds_json = os.environ.get('GCP_CREDENTIALS')
    credentials = service_account.Credentials.from_service_account_info(json.loads(creds_json))
    return bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)


def merge_rows(client, table, schema, rows, keys):
    """Načte řádky do staging tabulky a MERGE je do cílové (opakovaný běh nevytváří duplicity)."""
    if not rows:
        print(f"ℹ️ {table}: žádná data.")
        return

    target = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{table}"
    staging = f"{GCP_PROJECT_ID}.{BQ_DATASET}._stg_{table}_{uuid.uuid4().hex[:8]}"
    columns = [f.name for f in schema]

    def src(col):
        # reactions_by_type je ve staging STRING, v cílové tabulce JSON
        return f"PARSE_JSON(S.{col})" if col == 'reactions_by_type' else f"S.{col}"

    on = ' AND '.join(f"T.{k} = S.{k}" for k in keys)
    # COALESCE: chybějící hodnota (např. followers_count u starších dnů) nepřepíše existující
    updates = ', '.join(f"{c} = COALESCE({src(c)}, T.{c})" for c in columns if c not in keys)
    insert_cols = ', '.join(columns)
    insert_vals = ', '.join(src(c) for c in columns)

    try:
        client.load_table_from_json(
            rows, staging,
            job_config=bigquery.LoadJobConfig(schema=schema, write_disposition='WRITE_TRUNCATE'),
        ).result()
        client.query(
            f"MERGE `{target}` T USING `{staging}` S ON {on} "
            f"WHEN MATCHED THEN UPDATE SET {updates} "
            f"WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})"
        ).result()
        print(f"✅ {table}: zpracováno {len(rows)} řádků.")
    finally:
        client.delete_table(staging, not_found_ok=True)


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    today = now.date()
    ingested_at = now.isoformat()

    print("Stahuji data z Facebook API...")
    data, posts = fetch_facebook_data(today)
    page_rows = build_page_rows(data, today, ingested_at)
    post_rows = build_post_rows(posts, today, ingested_at)

    print("Nahrávám data do BigQuery...")
    client = get_bq_client()
    merge_rows(client, PAGE_TABLE, PAGE_SCHEMA, page_rows, ['date', 'page_id'])
    merge_rows(client, POST_TABLE, POST_SCHEMA, post_rows, ['snapshot_date', 'post_id'])
