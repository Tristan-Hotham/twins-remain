# Twinned with Europe, voted Remain?

Town twinning and the geography of the 2016 referendum in Great Britain. Every twinning of a British town or council recorded in Wikidata (1,445 links of 704 hosts, 79% with partners in other EU member states), assigned to the 632 constituencies of Great Britain with documented rules, and set against the estimated 2016 Leave share in a test specified in a written plan before the outcome was examined (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/twins-remain/
Paper: https://doi.org/10.5281/zenodo.24094355
Blog post: https://blog.tristanhotham.com/2026/10/31/twins-remain/
Code and data: https://github.com/Tristan-Hotham/twins-remain

## Headline results

- Partners: France 484, Germany 375, United States 74, Italy 62, Poland 42, China 35. Coventry has the most partners (25). 566 of 632 seats have at least one EU partner (council twinnings count for every seat mostly inside the council area).
- Pre-specified main model (OLS, region fixed effects, 2011 census and documentation controls, SE clustered by local authority): a seat with an EU twin has a Leave share -0.3 (95% CI -1.4 to 0.8) points different from similar seats; N = 632. Null; the planned equivalence test at 1 point is not passed (p = 0.11).
- Planned placebo: a twin outside the EU goes with -1.4 (95% CI -2.3 to -0.5) points; with both in the model the EU coefficient is 0.0; EU minus non-EU 1.3 (95% CI -0.2 to 2.9), p = 0.095. Not Europe-specific.
- Robustness: 2 of 15 planned checks significant (the two count measures, about -0.7 per unit of log count, not significant once non-EU counts are included); leave one region out -0.77 to 0.17; randomisation inference p = 0.59; matched seats -1.0 (95% CI -1.6 to -0.5) with a naive bootstrap that understates uncertainty.
- Exploratory: the non-EU association survives leaving out any region and England only, but not local authority fixed effects (-0.7 (95% CI -2.6 to 1.1)) or counted results only. Timing: only 26% of EU twinnings are dated; pre-1973 first twins -0.3 (95% CI -1.9 to 1.4).
- Coverage: 58% of settlements of 50,000+ have a recorded twinning, under 1% of villages. Correlational design throughout.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; twinned places coloured by EU or non-EU partners, constituencies shaded by Leave, optional lines to partner countries; layers panel, search, popups, full-screen. |
| `header.png` | Social card, 1200 x 630. |
| `data/twinnings.csv` | Every host and partner pair (1,540): host, class, council, point, partner, present country, EU flag, year joined, start and end, seats assigned. CC0 (from Wikidata). |
| `data/hosts.csv` | Every host (747): Wikidata types, class, matched local authority, point seat, seats assigned. |
| `data/assign.csv` | Host to constituency assignments, with how each was made. |
| `data/constituencies.csv` | The 632 seats: Leave estimates, census controls, settlement controls and every exposure variant. |
| `data/models.csv`, `data/model_tables.json` | Every estimate and the full coefficient tables. |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage, GIF and post. |
| `data/hosts.json`, `data/seats.geojson` | Page data. |
| `code/` | Numbered pipeline, templates, `overrides.csv` (one documented override and one class change), `refs.bib`, `qa.js`. |
| `release/` | Paper (`paper/`, with `cover_note.md`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage, looping GIF, `collage.py` and post text. |
| `NOTES.md` | The analysis plan (written before the outcome models), the log, the data check and the reference verification list. |

## Method in brief

- Partners resolved to their present country; EU = the 27 other member states on 23 June 2016.
- Hosts whose name and point match a 2013 local authority district are council hosts, assigned to every seat with at least a third of its area in the district; other hosts go to the seat containing their point. Wide-area hosts (Greater London, counties), schools and places outside Great Britain are excluded from the main count.
- Outcome: Hanretty's estimated Leave share by 2010 constituency. Controls: region, age 65+, degree, no qualifications, routine occupations, White British, born abroad, log density, log settlements with an article, log largest settlement, county seat.
- Models as in the plan in `NOTES.md` (statsmodels).

## How to rerun

Python 3 with pandas, numpy, scipy, geopandas, shapely, pyproj, statsmodels, matplotlib, Pillow; xelatex, bibtex, pdftotext; node with Playwright for `code/qa.js`. Raw inputs are listed in `code/common.py`; intermediates go to `TR_SCRATCH`.

```
python3 code/01_build.py       # clean twinnings, classify hosts, assign seats, join census and Leave
python3 code/02_models.py      # the planned models and checks
python3 code/03_results.py     # results.json and models.csv
python3 code/04_figures.py     # figures and page data
python3 code/05_build_site.py  # index.html
python3 code/06_paper.py       # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage and header
python3 code/08_readme.py      # README, LICENSE, post, cover note
python3 code/07_release.py     # blog post and Zenodo files
node code/qa.js                # screenshots
```

## Sources and licences

- Twinnings and settlements: Wikidata contributors (CC0). Derived twinning tables are CC0.
- Leave estimates: C. Hanretty (2017), Journal of Elections, Public Opinion and Parties, via parlitools (E. Odell).
- 2011 census: ONS and National Records of Scotland; boundaries: ONS and Ordnance Survey (Open Government Licence v3.0). Land outlines: Natural Earth (public domain). Partner town points: Wikidata coordinate location (P625, CC0).
- Base map: OpenFreeMap, OpenStreetMap data (ODbL). MapLibre GL JS (BSD 3-Clause).
- Text and figures CC BY 4.0; code MIT (see `LICENSE`).

## Citation

Hotham, T. (2026). Twinned with Europe, Voted Remain? Town twinning and the geography of the 2016 referendum in Great Britain. Zenodo. https://doi.org/10.5281/zenodo.24094355

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
