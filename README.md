# Hijri Calendar for Morocco (Maghrib)

A Hijri calendar for Morocco that uses the official start dates where they are known (1445–1448 AH) and forecasts every month from Jumada al-Thani 1448 to Dhul-Hijjah 1460 AH (late 2026 to early 2039).

Morocco's Ministry of Habous and Islamic Affairs starts each month the day after the new crescent is sighted in Morocco on the evening of the 29th. If it isn't sighted, the month runs to 30 days. This project learns how Morocco's decisions relate to the crescent visibility maps published by moonsighting.com. It then uses that to forecast future months, with a probability for each date.

**Open `index.html` in a browser.** It is one self-contained page with no build step needed to view it. To host it, enable GitHub Pages for this repository (Settings → Pages → deploy from `main`, root folder).

## What the page shows

- **Calendar:** each Hijri month as a grid, with the Hijri day large and the Gregorian date beside it. Ramadan, the two Eids, the Islamic New Year and Mawlid are highlighted. Weeks start on Monday.
- **Key dates, 1445–1460:** Islamic New Year, Eid al-Mawlid, the start of Ramadan, Eid al-Fitr and Eid al-Adha for every year, with the forecast probability for future years.
- **Evidence:** for every month, the three crescent maps (the new-moon evening and the two after it) cropped to Morocco, with the 29th evening outlined. Past months show what the model would have predicted at the time and the actual announced date. Future months show the forecast.
- **How good the model is:** walk-forward accuracy, calibration, the model weights, and how Morocco's decisions on borderline nights changed in 2025–26.

## Method

1. **Features.** On each 29th-evening map, measure the share of Moroccan land (Tangier to Lagouira) in each visibility zone: A green (naked eye), B cyan (perfect conditions), C grey (optical aid to find), D red (optical aid only) or none. See `scripts/features.py`.
2. **Labels.** Whether Morocco reported the crescent that evening, for 137 evenings from Muharram 1437 (Oct 2015) to Jumada al-Ula 1448 (Oct 2026). Sources are the Morocco Awqaf sighting reports logged on moonsighting.org.uk (1437–1444), Morocco's announced start dates on the same site (1445–1446), and official Habous announcements for 2025–26.
3. **Model** (`scripts/build_calendar.py`):
   - **Any naked-eye green over Morocco:** observed rate, 50 of 50 reported (98% with smoothing).
   - **Only red or no visibility:** observed rate, 0 of 43 reported (2%).
   - **Borderline nights (cyan or grey):** logistic regression on the cyan and grey shares, weighting recent years more (half-life 2 years, C = 3). This setting was chosen by walk-forward testing in `scripts/tune_model.py`.
4. **Forecasting.** Start-date probabilities are carried forward month by month. The calendar shows the most likely consistent chain of month starts (Viterbi), so every month is 29 or 30 days.

## Results (walk-forward: each evening predicted using only earlier evenings)

| | Model | Simple rule: "seen only if green" |
|---|---|---|
| All 117 evenings, 2017–2026 | 94.9% correct, Brier 0.041 | 89.7%, Brier 0.103 |
| 31 borderline evenings | 80.6%, Brier 0.143 | 61.3%, Brier 0.387 |
| 9 borderline evenings since July 2024 | 44% | 44% |

From 2015 to 2024 Morocco reported every all-cyan night (8 of 8) and no grey-heavy night (0 of 19). In 2025–26 that reversed: 1 of 3 all-cyan nights and 3 of 4 grey-heavy nights were reported. Borderline nights stay close to a coin toss, and the forecast percentages reflect that. Full notes and the month table are in [`docs/model.md`](docs/model.md).

## Rebuilding

Requires Python 3.10+ (`pip install -r requirements.txt`) and curl.

```bash
# 1. Get the maps (about 1,300 GIFs, not stored in this repo).
#    Windows: run tools/Download-MoonMaps.ps1, which creates
#    "Moon Visibility Maps (moonsighting.com)" with index.csv.
#    Then fetch the remaining maps, including 1437 AH, which the site still hosts but no longer lists:
export MOON_MAPS="/path/to/Moon Visibility Maps (moonsighting.com)"
python scripts/fetch_maps.py

# 2. Rebuild data/calendar.json and index.html
python scripts/build_calendar.py            # TODAY=YYYY-MM-DD to pin the date

# Optional: re-run model selection
python scripts/tune_model.py
```

To add a new month once Morocco announces it, add the evening to `data/dataset.json`, or to `data/official_months_2024_2026.json` for the official start, then rebuild.

## Data files

| File | Contents |
|---|---|
| `data/labelled_evenings.csv` | The 137 training evenings: date, which month it decided, reported or not, source, map file, zone shares |
| `data/dataset.json` | The same data in the form the build script reads |
| `data/official_months_2024_2026.json` | Official Moroccan month starts Jumada al-Thani 1446 to Jumada al-Ula 1448, with source links |
| `data/reports_parsed.json` | Morocco results parsed from moonsighting.org.uk monthly reports |
| `data/maps_1437.csv` | URLs of the 1437 AH maps |
| `data/calendar.json` | Everything the page displays (months, evidence, forecasts, stats) |

## Credits and caveats

- Crescent visibility maps: [moonsighting.com](https://www.moonsighting.com/visibility.html) (OmegaHilalSighting by Fawzi Kayali, Shaukat criterion). The page embeds small cropped thumbnails, and the full maps are not redistributed here.
- Sighting results: [moonsighting.org.uk](https://www.moonsighting.org.uk/) (ICOUK) and announcements by Morocco's Ministry of Habous and Islamic Affairs as reported by Hespress, SNRT News, Médias24, TelQuel and Le360.
- Forecasts are for planning only. Morocco's months begin on the Ministry's announcement, which depends on an actual sighting and on the weather.
