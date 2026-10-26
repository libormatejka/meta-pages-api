-- Add the confirmed post insight metric columns to an existing table.
-- Run in the collectorboycz.MarketingData dataset.

ALTER TABLE `collectorboycz.MarketingData.fb_post_daily`
  ADD COLUMN IF NOT EXISTS post_total_media_view_unique INT64
    OPTIONS (description = 'Kumulativní počet unikátních lidí, kterým se příspěvek zobrazil.'),
  ADD COLUMN IF NOT EXISTS post_video_views INT64
    OPTIONS (description = 'Kumulativní počet zhlédnutí videa v příspěvku.'),
  ADD COLUMN IF NOT EXISTS post_video_views_organic INT64
    OPTIONS (description = 'Kumulativní počet organických zhlédnutí videa v příspěvku.'),
  ADD COLUMN IF NOT EXISTS post_video_views_paid INT64
    OPTIONS (description = 'Kumulativní počet placených zhlédnutí videa v příspěvku.'),
  ADD COLUMN IF NOT EXISTS post_video_views_autoplayed INT64
    OPTIONS (description = 'Kumulativní počet automaticky spuštěných zhlédnutí videa v příspěvku.'),
  ADD COLUMN IF NOT EXISTS post_video_complete_views_30s INT64
    OPTIONS (description = 'Kumulativní počet zhlédnutí videa alespoň 30 sekund nebo celého kratšího videa.'),
  ADD COLUMN IF NOT EXISTS post_video_complete_views_30s_unique INT64
    OPTIONS (description = 'Kumulativní počet unikátních lidí, kteří zhlédli video alespoň 30 sekund nebo celé kratší video.'),
  ADD COLUMN IF NOT EXISTS post_video_complete_views_30s_organic INT64
    OPTIONS (description = 'Kumulativní počet organických zhlédnutí videa alespoň 30 sekund.'),
  ADD COLUMN IF NOT EXISTS post_video_complete_views_30s_paid INT64
    OPTIONS (description = 'Kumulativní počet placených zhlédnutí videa alespoň 30 sekund.'),
  ADD COLUMN IF NOT EXISTS post_video_complete_views_30s_autoplayed INT64
    OPTIONS (description = 'Kumulativní počet automaticky spuštěných zhlédnutí videa alespoň 30 sekund.'),
  ADD COLUMN IF NOT EXISTS post_video_view_time INT64
    OPTIONS (description = 'Kumulativní doba sledování videa v jednotce vrácené Meta API.'),
  ADD COLUMN IF NOT EXISTS post_video_avg_time_watched FLOAT64
    OPTIONS (description = 'Průměrná doba sledování videa v jednotce vrácené Meta API.');
