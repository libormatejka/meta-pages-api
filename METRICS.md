# Metriky Facebook Page Insights

Popis metrik, které se stahují z Graph API a ukládají do BigQuery (viz [schema.sql](./schema.sql)).

## Jak číst data

- **Denní metriky stránky** (`period=day`): hodnota za jeden uzavřený den. `end_time` je konec dne, takže `end_time = 2026-10-25T07:00` znamená data za **24. 10. 2026**. Do sloupce `date` se ukládá `end_time - 1 den`.
- **Lifetime metriky příspěvků** (`period=lifetime`): kumulativní hodnota od vytvoření příspěvku do okamžiku stažení. Mění se každý den, proto se ukládá denní snímek (`snapshot_date`). Denní přírůstek spočítáš rozdílem dvou po sobě jdoucích snímků.
- **Snímkové hodnoty** (`followers_count`): aktuální stav v okamžiku stažení, ne hodnota za den.
- Chybějící pole (např. `shares`, prázdné `reactions_by_type`) se ukládají jako 0.

## Metriky stránky – tabulka `fb_page_daily`

| Sloupec | Graph API | Typ hodnoty | Co znamená |
|---|---|---|---|
| `followers_count` | pole `followers_count` | snímek | Aktuální počet sledujících stránky v okamžiku stažení. Historii si buduješ vlastními denními snímky. |
| `page_media_view` | `page_media_view` | denní, počet | **Zobrazení** – kolikrát se obsah stránky (příspěvky, příběhy, reels, reklamy…) zobrazil na obrazovce. Jeden člověk může generovat víc zobrazení. Nahrazuje zrušené `page_impressions`. |
| `page_total_media_view_unique` | `page_total_media_view_unique` | denní, počet | **Dosah** – počet jedinečných lidí, kterým se obsah zobrazil. Vždy ≤ `page_media_view`. Nahrazuje zrušené `page_impressions_unique`. |
| `page_post_engagements` | `page_post_engagements` | denní, počet | **Interakce s příspěvky** – součet reakcí, komentářů, sdílení, kliknutí a dalších akcí u příspěvků stránky. |
| `page_views_total` | `page_views_total` | denní, počet | **Návštěvy stránky** – kolikrát někdo otevřel profil stránky. |
| `page_video_views` | `page_video_views` | denní, počet | **Zhlédnutí videí** – kolikrát bylo video zhlédnuto alespoň 3 sekundy. |

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
