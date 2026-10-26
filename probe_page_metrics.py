import csv
import os
import sys
import time
from pathlib import Path

import requests


PAGE_METRICS = [
    'page_media_view',
    'page_total_media_view_unique',
    'page_follows',
    'page_daily_follows',
    'page_daily_follows_unique',
    'page_daily_unfollows_unique',
    'page_lifetime_engaged_followers_unique',
    'page_post_engagements',
    'page_total_actions',
    'page_negative_feedback_by_type',
    'page_views_total',
    'page_tab_views_login_top',
    'page_tab_views_login_top_unique',
    'page_tab_views_logout_top',
    'page_actions_post_reactions_like_total',
    'page_actions_post_reactions_love_total',
    'page_actions_post_reactions_wow_total',
    'page_actions_post_reactions_haha_total',
    'page_actions_post_reactions_sorry_total',
    'page_actions_post_reactions_anger_total',
    'page_actions_post_reactions_total',
    'page_video_views',
    'page_video_views_unique',
    'page_video_views_organic',
    'page_video_views_paid',
    'page_video_view_time',
    'page_video_repeat_views',
    'page_video_views_10s',
    'page_video_views_10s_unique',
    'page_video_views_10s_organic',
    'page_video_views_10s_paid',
    'page_video_views_10s_autoplayed',
    'page_video_views_10s_click_to_play',
    'page_video_views_10s_repeat',
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
    'page_uploaded_views_15s_count',
    'page_uploaded_3s_to_15s_views_rate',
    'page_uploaded_views_60s_excludes_shorter_unique_count_by_is_60s_returning_viewer',
    'page_consumptions_by_consumption_type',
    'page_daily_video_ad_break_ad_impressions_by_crosspost_status',
    'page_daily_video_ad_break_cpm_by_crosspost_status',
    'page_daily_video_ad_break_earnings_by_crosspost_status',
    'page_follows_city',
    'page_follows_country',
]

GRAPH_VERSION = os.environ.get('FB_GRAPH_VERSION', 'v26.0')
GRAPH_URL = f'https://graph.facebook.com/{GRAPH_VERSION}'
PAGE_ID = os.environ.get('FB_PAGE_ID')
ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')


def probe(metric, period, since, until):
    try:
        response = requests.get(
            f'{GRAPH_URL}/{PAGE_ID}/insights',
            params={
                'metric': metric,
                'period': period,
                'since': since,
                'until': until,
                'access_token': ACCESS_TOKEN,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        return 'REQUEST_ERROR', type(exc).__name__

    try:
        payload = response.json()
    except ValueError:
        return 'HTTP_ERROR', f'HTTP {response.status_code}; non-JSON response'

    error = payload.get('error')
    if error:
        message = error.get('message', 'Unknown API error')
        if 'valid insights metric' in message.lower():
            return 'INVALID_METRIC', message
        if 'period' in message.lower():
            return 'PERIOD_ERROR', message
        return 'API_ERROR', message

    data = payload.get('data', [])
    if not data:
        return 'VALID_NO_DATA', 'API returned no metric rows'
    values = sum(len(item.get('values', [])) for item in data)
    return ('VALID_WITH_DATA' if values else 'VALID_NO_VALUES'), f'{values} values'


def main():
    missing = [
        name for name, value in (
            ('FB_PAGE_ID', PAGE_ID),
            ('FB_ACCESS_TOKEN', ACCESS_TOKEN),
        ) if not value
    ]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    from datetime import date, timedelta

    today = date.today()
    since = (today - timedelta(days=7)).isoformat()
    until = today.isoformat()

    output_path = Path(os.environ.get('METRICS_PROBE_OUTPUT', 'page-metrics-probe.csv'))
    with output_path.open('w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(['metric', 'period', 'status', 'details'])
        for metric in PAGE_METRICS:
            status, details = probe(metric, 'day', since, until)
            writer.writerow([metric, 'day', status, details.replace('\n', ' ')])
            time.sleep(0.25)

            if status in {'PERIOD_ERROR', 'VALID_NO_DATA', 'VALID_NO_VALUES'}:
                status, details = probe(metric, 'lifetime', since, until)
                writer.writerow([metric, 'lifetime', status, details.replace('\n', ' ')])
                time.sleep(0.25)

    print(f'CSV report written to {output_path}')
    with output_path.open(encoding='utf-8') as report:
        sys.stdout.write(report.read())


if __name__ == '__main__':
    main()
