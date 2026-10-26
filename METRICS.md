# Metriky Facebook Page Insights

Popis metrik, které se stahují z Graph API a ukládají do BigQuery (viz [schema.sql](./schema.sql)).

## Jak číst data

- **Denní metriky stránky** (`period=day`): hodnota za jeden uzavřený den. `end_time` je konec dne, takže `end_time = 2026-10-25T07:00` znamená data za **24. 10. 2026**. Do sloupce `date` se ukládá `end_time - 1 den`.
- **Lifetime metriky příspěvků** (`period=lifetime`): kumulativní hodnota od vytvoření příspěvku do okamžiku stažení. Mění se každý den, proto se ukládá denní snímek (`snapshot_date`). Denní přírůstek spočítáš rozdílem dvou po sobě jdoucích snímků.
- Chybějící pole (např. `shares`, prázdné `reactions_by_type`) se ukládají jako 0.

## Metriky stránky – tabulka `fb_page_daily`

| Sloupec | Graph API | Typ hodnoty | Co znamená |
|---|---|---|---|
| `followers_count` | `page_follows` (period=day) | denní, počet | Počet sledujících stránky na konci dne (sledování minus zrušená sledování). Díky denní periodě jde doplnit i historie. |
| `page_media_view` | `page_media_view` | denní, počet | **Zobrazení** – kolikrát se obsah stránky (příspěvky, příběhy, reels, reklamy…) zobrazil na obrazovce. Jeden člověk může generovat víc zobrazení. Nahrazuje zrušené `page_impressions`. |
| `page_total_media_view_unique` | `page_total_media_view_unique` | denní, počet | **Dosah** – počet jedinečných lidí, kterým se obsah zobrazil. Vždy ≤ `page_media_view`. Nahrazuje zrušené `page_impressions_unique`. |
| `page_post_engagements` | `page_post_engagements` | denní, počet | **Interakce s příspěvky** – součet reakcí, komentářů, sdílení, kliknutí a dalších akcí u příspěvků stránky. |
| `page_total_actions` | `page_total_actions` | denní, počet | Celkový počet akcí provedených na stránce. |
| `page_views_total` | `page_views_total` | denní, počet | **Návštěvy stránky** – kolikrát někdo otevřel profil stránky. |
| `page_video_views` | `page_video_views` | denní, počet | **Zhlédnutí videí** – kolikrát bylo video zhlédnuto alespoň 3 sekundy. |
| `page_daily_follows` | `page_daily_follows` | denní, počet | Počet sledujících získaných za den podle metriky Meta. |
| `page_daily_follows_unique` | `page_daily_follows_unique` | denní, počet | Denní počet unikátních nových sledujících. |
| `page_daily_unfollows_unique` | `page_daily_unfollows_unique` | denní, počet | Denní počet unikátních lidí, kteří stránku přestali sledovat. |
| `page_lifetime_engaged_followers_unique` | `page_lifetime_engaged_followers_unique` | denní, počet | Unikátní sledující, kteří interagovali se stránkou; API v testu vracelo denní hodnoty. |
| `page_actions_post_reactions_like_total` | stejná metrika | denní, počet | Denní počet reakcí Like. |
| `page_actions_post_reactions_love_total` | stejná metrika | denní, počet | Denní počet reakcí Love. |
| `page_actions_post_reactions_wow_total` | stejná metrika | denní, počet | Denní počet reakcí Wow. |
| `page_actions_post_reactions_haha_total` | stejná metrika | denní, počet | Denní počet reakcí Haha. |
| `page_actions_post_reactions_sorry_total` | stejná metrika | denní, počet | Denní počet reakcí Sorry. |
| `page_actions_post_reactions_anger_total` | stejná metrika | denní, počet | Denní počet reakcí Anger. |
| `page_actions_post_reactions_total` | stejná metrika | denní, počet | Celkový počet reakcí na příspěvky za den. |
| `page_video_views_organic` | stejná metrika | denní, počet | Organická zhlédnutí videí. |
| `page_video_views_paid` | stejná metrika | denní, počet | Zhlédnutí videí z placené distribuce. |
| `page_video_view_time` | stejná metrika | denní, čas | Celkový čas sledování videí; jednotku ověř v popisu vráceném Graph API. |
| `page_video_repeat_views` | stejná metrika | denní, počet | Opakovaná zhlédnutí videí. |
| `page_video_complete_views_30s` | stejná metrika | denní, počet | Zhlédnutí videa alespoň 30 sekund (nebo celé video, pokud je kratší). |
| `page_video_complete_views_30s_unique` | stejná metrika | denní, počet | Unikátní lidé, kteří splnili hranici 30 sekund. |
| `page_video_complete_views_30s_organic` | stejná metrika | denní, počet | Organická zhlédnutí videa alespoň 30 sekund. |
| `page_video_complete_views_30s_paid` | stejná metrika | denní, počet | Placená zhlédnutí videa alespoň 30 sekund. |
| `page_video_complete_views_30s_autoplayed` | stejná metrika | denní, počet | Zhlédnutí alespoň 30 sekund spuštěná automaticky. |
| `page_video_complete_views_30s_click_to_play` | stejná metrika | denní, počet | Zhlédnutí alespoň 30 sekund po kliknutí na přehrávání. |
| `page_video_complete_views_30s_repeat_views` | stejná metrika | denní, počet | Opakovaná zhlédnutí videa alespoň 30 sekund. |
| `page_video_views_autoplayed` | stejná metrika | denní, počet | Zhlédnutí videa spuštěná automaticky. |
| `page_video_views_click_to_play` | stejná metrika | denní, počet | Zhlédnutí videa po kliknutí na přehrávání. |
| `page_video_views_by_paid_non_paid` | stejná metrika | denní, JSON | Rozpad zhlédnutí podle placeného/neplaceného zdroje. |
| `page_video_views_by_uploaded_hosted` | stejná metrika | denní, JSON | Rozpad zhlédnutí podle umístění/hostingu videa. |

Metriky s JSON ukládají strukturu vrácenou API. Názvy bez dalších popisů vycházejí z názvů metrik; přesné definice a jednotky zobrazí metadata v odpovědi Graph API.

### Výsledek ověření dostupnosti

Jednorázový probe z 26. 10. 2026 ověřil každou kandidátní metriku samostatně za posledních 7 dní. Metriky uvedené v tabulce vrátily hodnoty. To potvrzuje jejich dostupnost pro tuto stránku v době testu, ne nutně historickou dostupnost ve všech obdobích.

Odmítnuté metriky (`INVALID_METRIC`): `page_negative_feedback_by_type`, `page_tab_views_login_top`, `page_tab_views_login_top_unique`, `page_tab_views_logout_top`, `page_video_views_unique`, všechny testované `page_video_views_10s*`, `page_uploaded_views_15s_count`, `page_uploaded_3s_to_15s_views_rate`, `page_uploaded_views_60s_excludes_shorter_unique_count_by_is_60s_returning_viewer` a `page_consumptions_by_consumption_type`.

`page_follows_city` a `page_follows_country` v testu nevrátily žádné řádky, takže se zatím do denního skriptu nezařazují. Monetizační metriky byly dostupné jen pro Page adminy s přístupem k monetizačním insights.

Pomocné sloupce: `date` (den, ke kterému metriky patří), `page_id`, `ingested_at` (kdy byl řádek stažen).

## Metriky příspěvků – tabulka `fb_post_daily`

| Sloupec | Graph API | Typ hodnoty | Co znamená |
|---|---|---|---|
| `post_media_view` | `post_media_view` | lifetime, počet | Kolikrát se příspěvek zobrazil na obrazovce (od vzniku). Nahrazuje zrušené `post_impressions`. |
| `post_clicks` | `post_clicks` | lifetime, počet | Počet kliknutí kamkoli v příspěvku (odkaz, fotka, „zobrazit více“…). |
| `reactions_total` | `reactions.summary.total_count` | lifetime, počet | Celkový počet reakcí (To se mi líbí, Super, Haha…). |
| `reactions_by_type` | `post_reactions_by_type_total` | lifetime, JSON | Rozpad reakcí podle typu, např. `{"like": 5, "love": 2}`. U příspěvku bez reakcí `{}`. |
| `comments_total` | `comments.summary.total_count` | lifetime, počet | Počet komentářů. |
| `shares_total` | `shares.count` | lifetime, počet | Počet sdílení. Pole `shares` chybí, pokud příspěvek nikdo nesdílel. |

Pomocné sloupce: `snapshot_date` (den snímku), `page_id`, `post_id`, `created_time` (kdy byl příspěvek publikován), `message` (text), `permalink_url` (odkaz na příspěvek), `ingested_at`.

## Rozdíl: zobrazení vs. dosah

- **Zobrazení** (`*_media_view`) = kolikrát se obsah ukázal. Počítá opakovaná zobrazení.
- **Dosah** (`*_total_media_view_unique`) = kolik různých lidí obsah vidělo.
- Příklad: 6 lidí vidělo stránku dohromady 17krát → dosah 6, zobrazení 17.

## Zrušené metriky (nepoužívat)

API na ně vrací chybu `(#100) The value must be a valid insights metric`.

| Zrušená metrika | Náhrada |
|---|---|
| `page_fans` | `page_follows` / pole `followers_count` |
| `page_impressions`, `page_impressions_paid` | `page_media_view` |
| `page_impressions_unique` | `page_total_media_view_unique` |
| `post_impressions` | `post_media_view` |
| `post_impressions_unique` | `post_total_media_view_unique` |
| `page_fan_adds`, `page_fan_removes` | `page_daily_follows_unique`, `page_daily_unfollows_unique` |
| `page_fans_gender_age` | bez náhrady |

Úplný seznam: [Deprecated metrics](https://developers.facebook.com/documentation/pages-api/platforminsights/page/deprecated-metrics).
