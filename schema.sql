-- Nahraď `PROJECT.DATASET` svým GCP projektem a datasetem.

CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.fb_page_daily` (
  date DATE NOT NULL OPTIONS (description = 'Den, ke kterému metriky patří (end_time - 1 den)'),
  page_id STRING NOT NULL,
  followers_count INT64 OPTIONS (description = 'Snímek v čase stažení'),
  page_media_view INT64,
  page_total_media_view_unique INT64,
  page_post_engagements INT64,
  page_views_total INT64,
  page_video_views INT64,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY page_id;

CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.fb_post_daily` (
  snapshot_date DATE NOT NULL OPTIONS (description = 'Den snímku lifetime hodnot'),
  page_id STRING NOT NULL,
  post_id STRING NOT NULL,
  created_time TIMESTAMP,
  message STRING,
  permalink_url STRING,
  post_media_view INT64,
  post_clicks INT64,
  reactions_total INT64,
  comments_total INT64,
  shares_total INT64,
  reactions_by_type JSON,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY snapshot_date
CLUSTER BY page_id, post_id;

-- Klíče pro MERGE (BigQuery je nevynucuje):
--   fb_page_daily: (date, page_id)
--   fb_post_daily: (snapshot_date, post_id)
