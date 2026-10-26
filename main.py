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

GRAPH_URL = 'https://graph.facebook.com/v26.0'
PAGE_METRICS = [
    'page_media_view',
    'page_total_media_view_unique',
    'page_post_engagements',
    'page_total_actions',
    'page_views_total',
    'page_video_views',
    'page_daily_follows',
    'page_daily_follows_unique',
    'page_daily_unfollows_unique',
    'page_lifetime_engaged_followers_unique',
    'page_actions_post_reactions_like_total',
    'page_actions_post_reactions_love_total',
    'page_actions_post_reactions_wow_total',
    'page_actions_post_reactions_haha_total',
    'page_actions_post_reactions_sorry_total',
    'page_actions_post_reactions_anger_total',
    'page_actions_post_reactions_total',
    'page_video_views_organic',
    'page_video_views_paid',
    'page_video_view_time',
    'page_video_repeat_views',
    'page_video_complete_views_30s',
    'page_video_complete_views_30s_unique',
    'page_video_complete_views_30s_organic',
    'page_video_complete_views_30s_paid',
    'page_video_complete_views_30s_autoplayed',
    'page_video_complete_views_30s_click_to_play',
    'page_video_complete_views_30s_repeat_views',
    'page_video_views_autoplayed',
    'page_video_views_click_to_play',
    'page_video_views_by_paid_non_paid',
    'page_video_views_by_uploaded_hosted',
]
# Denní historie sledujících, ukládá se do sloupce followers_count
FOLLOWS_METRIC = 'page_follows'
PAGE_JSON_METRICS = {
    'page_actions_post_reactions_total',
    'page_video_views_by_paid_non_paid',
    'page_video_views_by_uploaded_hosted',
}
POST_METRICS = [
    'post_media_view',
    'post_total_media_view_unique',
    'post_clicks',
    'post_reactions_by_type_total',
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
    'post_video_views_autoplayed',
    'post_video_complete_views_30s',
    'post_video_complete_views_30s_unique',
    'post_video_complete_views_30s_organic',
    'post_video_complete_views_30s_paid',
    'post_video_complete_views_30s_autoplayed',
    'post_video_view_time',
    'post_video_avg_time_watched',
]
# Metriky stránky se zpětně dopočítávají, přepisujeme poslední dny.
# BACKFILL_DAYS slouží k jednorázovému doplnění historie (Facebook drží data 2 roky).
PAGE_DAYS_BACK = int(os.environ.get('BACKFILL_DAYS') or 3)
MAX_BACKFILL_DAYS = 730
WINDOW_DAYS = 90      # jedno volání /insights smí pokrýt nejvýše 93 dní
if not 1 <= PAGE_DAYS_BACK <= MAX_BACKFILL_DAYS:
    raise SystemExit(f"❌ BACKFILL_DAYS musí být v rozmezí 1–{MAX_BACKFILL_DAYS}.")
POST_DAYS_BACK = 30   # starší příspěvky se skoro nemění

PAGE_SCHEMA = [
    bigquery.SchemaField('date', 'DATE'),
    bigquery.SchemaField('page_id', 'STRING'),
    bigquery.SchemaField('followers_count', 'INT64'),
    *[
        bigquery.SchemaField(m, 'STRING' if m in PAGE_JSON_METRICS else 'INT64')
        for m in PAGE_METRICS
    ],
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
    bigquery.SchemaField('post_total_media_view_unique', 'INT64'),
    bigquery.SchemaField('post_clicks', 'INT64'),
    bigquery.SchemaField('reactions_total', 'INT64'),
    bigquery.SchemaField('comments_total', 'INT64'),
    bigquery.SchemaField('shares_total', 'INT64'),
    bigquery.SchemaField('reactions_by_type', 'STRING'),
    bigquery.SchemaField('post_video_views', 'INT64'),
    bigquery.SchemaField('post_video_views_organic', 'INT64'),
    bigquery.SchemaField('post_video_views_paid', 'INT64'),
    bigquery.SchemaField('post_video_views_autoplayed', 'INT64'),
    bigquery.SchemaField('post_video_complete_views_30s', 'INT64'),
    bigquery.SchemaField('post_video_complete_views_30s_unique', 'INT64'),
    bigquery.SchemaField('post_video_complete_views_30s_organic', 'INT64'),
    bigquery.SchemaField('post_video_complete_views_30s_paid', 'INT64'),
    bigquery.SchemaField('post_video_complete_views_30s_autoplayed', 'INT64'),
    bigquery.SchemaField('post_video_view_time', 'INT64'),
    bigquery.SchemaField('post_video_avg_time_watched', 'FLOAT64'),
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
    page_since_date = today - timedelta(days=min(PAGE_DAYS_BACK, WINDOW_DAYS))
    page_since = page_since_date.isoformat()
    post_days_back = max(POST_DAYS_BACK, PAGE_DAYS_BACK)
    post_since = (today - timedelta(days=post_days_back)).isoformat()
    until = (today + timedelta(days=1)).isoformat()

    fields = (
        f"followers_count,"
        f"insights.metric({','.join(PAGE_METRICS + [FOLLOWS_METRIC])}).period(day)"
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
    print(f"Načteno {len(posts)} příspěvků od {post_since} do {until}.")

    # Starší historii stahujeme po oknech, každé okno samostatným voláním
    oldest = today - timedelta(days=PAGE_DAYS_BACK)
    window_until = page_since_date
    while window_until > oldest:
        window_since = max(oldest, window_until - timedelta(days=WINDOW_DAYS))
        older = fb_get(f"{GRAPH_URL}/{FB_PAGE_ID}/insights", {
            'metric': ','.join(PAGE_METRICS + [FOLLOWS_METRIC]),
            'period': 'day',
            'since': window_since.isoformat(),
            'until': window_until.isoformat(),
            'access_token': FB_ACCESS_TOKEN,
        })
        data.setdefault('insights', {}).setdefault('data', []).extend(older.get('data', []))
        print(f"Doplněno okno {window_since} – {window_until}")
        window_until = window_since

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
            column = 'followers_count' if item['name'] == FOLLOWS_METRIC else item['name']
            value = v.get('value', 0)
            row[column] = (
                json.dumps(value) if column in PAGE_JSON_METRICS and value is not None
                else value
            )

    # Záloha: aktuální snímek sledujících, kdyby page_follows za včerejšek chyběl
    yesterday = (today - timedelta(days=1)).isoformat()
    row = rows.setdefault(yesterday, {
        'date': yesterday, 'page_id': FB_PAGE_ID, 'ingested_at': ingested_at,
    })
    row.setdefault('followers_count', data.get('followers_count'))
    return list(rows.values())


def parse_fb_time(value):
    # Facebook vrací +0000 bez dvojtečky, BigQuery vyžaduje ISO formát
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z').isoformat()


def build_post_rows(posts, today, ingested_at):
    rows = []
    for p in posts:
        metrics = {}
        for item in p.get('insights', {}).get('data', []):
            values = item.get('values', [])
            metrics[item['name']] = values[0].get('value') if values else None
        by_type = metrics.get('post_reactions_by_type_total') or {}
        row = {
            'snapshot_date': today.isoformat(),
            'page_id': FB_PAGE_ID,
            'post_id': p['id'],
            'created_time': parse_fb_time(p.get('created_time')),
            'message': p.get('message'),
            'permalink_url': p.get('permalink_url'),
            'post_media_view': metrics.get('post_media_view') or 0,
            'post_clicks': metrics.get('post_clicks') or 0,
            'reactions_total': p.get('reactions', {}).get('summary', {}).get('total_count', 0),
            'comments_total': p.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares_total': p.get('shares', {}).get('count', 0),
            'reactions_by_type': json.dumps(by_type),
            'ingested_at': ingested_at,
        }
        for metric in POST_METRICS:
            if metric == 'post_reactions_by_type_total':
                continue
            value = metrics.get(metric)
            row[metric] = value if value is not None else 0
        rows.append(row)
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

    def normalize_type(field_type):
        return {
            'INTEGER': 'INT64',
            'FLOAT': 'FLOAT64',
            'BOOLEAN': 'BOOL',
        }.get(field_type, field_type)

    target_schema = {field.name: field.field_type for field in client.get_table(target).schema}
    expected_types = {
        field.name: (
            'JSON' if field.name == 'reactions_by_type' or field.name in PAGE_JSON_METRICS
            else field.field_type
        )
        for field in schema
    }
    mismatched_columns = {
        column: (expected_type, target_schema.get(column))
        for column, expected_type in expected_types.items()
        if normalize_type(target_schema.get(column)) != normalize_type(expected_type)
    }
    if mismatched_columns:
        actual_types = ', '.join(
            f'{column}: expected {expected}, found {actual or "missing"}'
            for column, (expected, actual) in mismatched_columns.items()
        )
        raise RuntimeError(
            f"BigQuery schema mismatch in {target}: {actual_types}. "
            f"Run the migration for {table} before starting the sync."
        )

    def src(col):
        # JSON hodnoty jsou ve staging STRING, v cílové tabulce JSON
        return (
            f"PARSE_JSON(S.{col})"
            if col == 'reactions_by_type' or col in PAGE_JSON_METRICS
            else f"S.{col}"
        )

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
    required = ['FB_PAGE_ID', 'FB_ACCESS_TOKEN', 'GCP_PROJECT_ID', 'BQ_DATASET', 'GCP_CREDENTIALS']
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"❌ Chybí nebo jsou prázdné proměnné prostředí: {', '.join(missing)}")

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
