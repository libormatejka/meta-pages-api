-- Nahraď `PROJECT.DATASET` svým GCP projektem a datasetem.

CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.fb_page_daily` (
  date DATE NOT NULL OPTIONS (description = 'Den, ke kterému metriky patří (end_time - 1 den)'),
  page_id STRING NOT NULL,
  followers_count INT64 OPTIONS (description = 'Počet sledujících podle page_follows za den'),
  page_media_view INT64,
  page_total_media_view_unique INT64,
  page_post_engagements INT64,
  page_total_actions INT64,
  page_views_total INT64,
  page_video_views INT64,
  page_daily_follows INT64,
  page_daily_follows_unique INT64,
  page_daily_unfollows_unique INT64,
  page_lifetime_engaged_followers_unique INT64,
  page_actions_post_reactions_like_total INT64,
  page_actions_post_reactions_love_total INT64,
  page_actions_post_reactions_wow_total INT64,
  page_actions_post_reactions_haha_total INT64,
  page_actions_post_reactions_sorry_total INT64,
  page_actions_post_reactions_anger_total INT64,
  page_actions_post_reactions_total JSON,
  page_video_views_organic INT64,
  page_video_views_paid INT64,
  page_video_view_time INT64,
  page_video_repeat_views INT64,
  page_video_complete_views_30s INT64,
  page_video_complete_views_30s_unique INT64,
  page_video_complete_views_30s_organic INT64,
  page_video_complete_views_30s_paid INT64,
  page_video_complete_views_30s_autoplayed INT64,
  page_video_complete_views_30s_click_to_play INT64,
  page_video_complete_views_30s_repeat_views INT64,
  page_video_views_autoplayed INT64,
  page_video_views_click_to_play INT64,
  page_video_views_by_paid_non_paid JSON,
  page_video_views_by_uploaded_hosted JSON,
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
