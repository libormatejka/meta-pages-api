import os
import json
import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

# --- KONFIGURACE Z PROMĚNNÝCH PROSTŘEDÍ ---
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')

GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
BQ_DATASET = os.environ.get('BQ_DATASET')
BQ_TABLE = os.environ.get('BQ_TABLE')

def get_fb_page_insights():
    # Stahujeme data za kompletně uzavřený včerejší den
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    
    # Graph API Endpoint (v19.0) pro Page Insights
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/insights"
    
    # Metriky oddělené čárkou. Pro denní rozsah použijeme 'day'.
    params = {
        'metric': 'page_impressions_unique,page_post_engagements',
        'period': 'day',
        'since': date_str,
        'until': datetime.now().strftime('%Y-%m-%d'),
        'access_token': FB_ACCESS_TOKEN
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json().get('data', [])
    
    # Základní záznam, který odešleme do BigQuery
    row_to_insert = {
        "date": date_str,
        "page_id": FB_PAGE_ID
    }
    
    # Rozparsování metrik do formátu pro BigQuery tabulku
    for item in data:
        metric_name = item['name']
        values = item.get('values', [])
        if values:
            # Hodnota pro daný den
            row_to_insert[metric_name] = values[0].get('value', 0)
            
    return [row_to_insert]

def load_to_bigquery(rows):
    # Autentizace pomocí JSON klíče z Github Secrets
    creds_json = os.environ.get('GCP_CREDENTIALS')
    credentials_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    
    # Inicializace BigQuery klienta
    client = bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)
    table_ref = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    
    # Vložení dat jako nový řádek (Streaming Insert)
    errors = client.insert_rows_json(table_ref, rows)
    
    if not errors:
        print(f"✅ Data za datum {rows[0]['date']} úspěšně nahrána do BigQuery.")
    else:
        print(f"❌ Chyba při nahrávání do BQ: {errors}")

if __name__ == "__main__":
    print("Stahuji data z Facebook API...")
    rows = get_fb_page_insights()
    print("Nahrávám data do BigQuery...")
    load_to_bigquery(rows)