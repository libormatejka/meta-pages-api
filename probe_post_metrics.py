import csv
import os
import sys
import time
from pathlib import Path

import requests


POST_METRICS = [
    'post_media_view',
    'post_total_media_view_unique',
    'post_clicks',
    'post_reactions_by_type_total',
    'post_link_clicks',
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
    'post_video_views_autoplayed',
    'post_video_views_click_to_play',
    'post_video_views_10s',
    'post_video_views_10s_autoplayed',
    'post_video_views_10s_click_to_play',
    'post_video_complete_views_30s',
    'post_video_complete_views_30s_unique',
    'post_video_complete_views_30s_organic',
    'post_video_complete_views_30s_paid',
    'post_video_complete_views_30s_autoplayed',
    'post_video_complete_views_30s_click_to_play',
    'post_video_complete_views_30s_repeat_views',
    'post_video_view_time',
    'post_video_avg_time_watched',
]

GRAPH_VERSION = os.environ.get('FB_GRAPH_VERSION', 'v26.0')
GRAPH_URL = f'https://graph.facebook.com/{GRAPH_VERSION}'
PAGE_ID = os.environ.get('FB_PAGE_ID')
POST_ID = os.environ.get('FB_POST_ID')
ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')


def graph_get(path, params):
    try:
        response = requests.get(
            f'{GRAPH_URL}/{path}',
            params={**params, 'access_token': ACCESS_TOKEN},
            timeout=30,
        )
    except requests.RequestException as exc:
        return None, ('REQUEST_ERROR', type(exc).__name__)

    try:
        payload = response.json()
    except ValueError:
        return None, ('HTTP_ERROR', f'HTTP {response.status_code}; non-JSON response')

    if payload.get('error'):
        error = payload['error']
        return None, ('API_ERROR', error.get('message', 'Unknown API error'))
    return payload, None


def find_post_id():
    if POST_ID:
        return POST_ID

    payload, error = graph_get(
        f'{PAGE_ID}/posts',
        {'fields': 'id', 'limit': 1},
    )
    if error:
        raise RuntimeError(f'Cannot find a post to probe: {error[1]}')
    posts = payload.get('data', [])
    if not posts:
        raise RuntimeError('The Page returned no posts to probe.')
    return posts[0]['id']


def probe(post_id, metric):
    payload, error = graph_get(
        f'{post_id}/insights',
        {'metric': metric, 'period': 'lifetime'},
    )
    if error:
        status, details = error
        if status == 'API_ERROR' and 'valid insights metric' in details.lower():
            return 'INVALID_METRIC', details
        return status, details

    data = payload.get('data', [])
    if not data:
        return 'VALID_NO_DATA', 'API returned no metric rows'
    values = sum(len(item.get('values', [])) for item in data)
    if values:
        return 'VALID_WITH_DATA', f'{values} values'
    return 'VALID_NO_VALUES', 'Metric row returned without values'


def main():
    missing = [
        name for name, value in (
            ('FB_PAGE_ID', PAGE_ID),
            ('FB_ACCESS_TOKEN', ACCESS_TOKEN),
        ) if not value
    ]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    post_id = find_post_id()
    print(f'Probing lifetime metrics for one post: {post_id}')

    output_path = Path(os.environ.get('METRICS_PROBE_OUTPUT', 'post-metrics-probe.csv'))
    with output_path.open('w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(['post_id', 'metric', 'period', 'status', 'details'])
        for metric in POST_METRICS:
            status, details = probe(post_id, metric)
            writer.writerow([
                post_id, metric, 'lifetime', status, details.replace('\n', ' '),
            ])
            time.sleep(0.25)

    print(f'CSV report written to {output_path}')
    with output_path.open(encoding='utf-8') as report:
        sys.stdout.write(report.read())


if __name__ == '__main__':
    main()
