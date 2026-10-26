-- Run once for an existing fb_page_daily table.
-- Replace PROJECT.DATASET with the BigQuery project and dataset.

DECLARE reaction_metric_type STRING;

SET reaction_metric_type = (
  SELECT data_type
  FROM `PROJECT.DATASET.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'fb_page_daily'
    AND column_name = 'page_actions_post_reactions_total'
);

IF reaction_metric_type IS NOT NULL AND reaction_metric_type != 'JSON' THEN
  EXECUTE IMMEDIATE
    'ALTER TABLE `PROJECT.DATASET.fb_page_daily` DROP COLUMN page_actions_post_reactions_total';
END IF;

ALTER TABLE `PROJECT.DATASET.fb_page_daily`
  ADD COLUMN IF NOT EXISTS page_total_actions INT64,
  ADD COLUMN IF NOT EXISTS page_daily_follows INT64,
  ADD COLUMN IF NOT EXISTS page_daily_follows_unique INT64,
  ADD COLUMN IF NOT EXISTS page_daily_unfollows_unique INT64,
  ADD COLUMN IF NOT EXISTS page_lifetime_engaged_followers_unique INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_like_total INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_love_total INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_wow_total INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_haha_total INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_sorry_total INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_anger_total INT64,
  ADD COLUMN IF NOT EXISTS page_video_views_organic INT64,
  ADD COLUMN IF NOT EXISTS page_video_views_paid INT64,
  ADD COLUMN IF NOT EXISTS page_video_view_time INT64,
  ADD COLUMN IF NOT EXISTS page_video_repeat_views INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_unique INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_organic INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_paid INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_autoplayed INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_click_to_play INT64,
  ADD COLUMN IF NOT EXISTS page_video_complete_views_30s_repeat_views INT64,
  ADD COLUMN IF NOT EXISTS page_video_views_autoplayed INT64,
  ADD COLUMN IF NOT EXISTS page_video_views_click_to_play INT64,
  ADD COLUMN IF NOT EXISTS page_actions_post_reactions_total JSON,
  ADD COLUMN IF NOT EXISTS page_video_views_by_paid_non_paid JSON,
  ADD COLUMN IF NOT EXISTS page_video_views_by_uploaded_hosted JSON;
