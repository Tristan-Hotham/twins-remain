"""Step 8: README.md, LICENSE, the Reddit post (reddit/post.md) and the journal cover note (release/paper/cover_note.md),
filled from data/results.json. https://doi.org/10.5281/zenodo.24094355 and https://blog.tristanhotham.com/2026/10/31/twins-remain/ stay as placeholders."""
from common import *

R = jload(f"{DATA}/results.json")
import subprocess
_txt = subprocess.run(["pdftotext", os.path.join(ROOT, "release", "paper", "Hotham_Twins_Remain.pdf"), "-"], capture_output=True, text=True).stdout
R["paper_words"] = round(len(_txt.split("References")[0].split("Abstract", 1)[1].split()), -2)
f1 = lambda v: fmt(v, "f1")
ci = lambda c: f"{f1(c['b'])} (95% CI {f1(c['lo'])} to {f1(c['hi'])})"
P, N, M, H2 = R["pairs"], R["n"], R["main"], R["h2"]
NE = R["exploratory"]["noneu"]
readme = f"""# Twinned with Europe, voted Remain?

Town twinning and the geography of the 2016 referendum in Great Britain. Every twinning of a British town or council recorded in Wikidata ({P['usable']:,} links of {P['hosts_usable']} hosts, {P['eu_pc']:.0f}% with partners in other EU member states), assigned to the {N['seats']} constituencies of Great Britain with documented rules, and set against the estimated 2016 Leave share in a test specified in a written plan before the outcome was examined (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24094355}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/twins-remain/}}
Code and data: {REPO}

## Headline results

- Partners: France {R['country']['france']}, Germany {R['country']['germany']}, United States {R['country']['states']}, Italy {R['country']['italy']}, Poland {R['country']['poland']}, China {R['country']['china']}. Coventry has the most partners ({R['coventry']['n']}). {N['any_eu']} of {N['seats']} seats have at least one EU partner (council twinnings count for every seat mostly inside the council area).
- Pre-specified main model (OLS, region fixed effects, 2011 census and documentation controls, SE clustered by local authority): a seat with an EU twin has a Leave share {ci(M)} points different from similar seats; N = {M['n']}. Null; the planned equivalence test at 1 point is not passed (p = {R['tost']['p']:.2f}).
- Planned placebo: a twin outside the EU goes with {ci(H2['noneu_alone'])} points; with both in the model the EU coefficient is {f1(H2['joint_eu']['b'])}; EU minus non-EU {ci(H2['diff'])}, p = {H2['diff']['p']:.3f}. Not Europe-specific.
- Robustness: {R['robust_summary']['n_sig']} of {R['robust_summary']['n']} planned checks significant (the two count measures, about -0.7 per unit of log count, not significant once non-EU counts are included); leave one region out {fmt(R['loro_range']['min'], 'f2')} to {fmt(R['loro_range']['max'], 'f2')}; randomisation inference p = {R['ri']['p_two']:.2f}; matched seats {ci({'b': R['match']['att'], 'lo': R['match']['lo'], 'hi': R['match']['hi']})} with a naive bootstrap that understates uncertainty.
- Exploratory: the non-EU association survives leaving out any region and England only, but not local authority fixed effects ({ci(NE['ladfe'])}) or counted results only. Timing: only {R['h3']['dated_pc']:.0f}% of EU twinnings are dated; pre-1973 first twins {ci(R['h3']['model'])}.
- Coverage: {R['coverage']['big_pc']:.0f}% of settlements of 50,000+ have a recorded twinning, under 1% of villages. Correlational design throughout.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; twinned places coloured by EU or non-EU partners, constituencies shaded by Leave, optional lines to partner countries; layers panel, search, popups, full-screen. |
| `header.png` | Social card, 1200 x 630. |
| `data/twinnings.csv` | Every host and partner pair ({P['pairs']:,}): host, class, council, point, partner, present country, EU flag, year joined, start and end, seats assigned. CC0 (from Wikidata). |
| `data/hosts.csv` | Every host ({R['hosts']['all']}): Wikidata types, class, matched local authority, point seat, seats assigned. |
| `data/assign.csv` | Host to constituency assignments, with how each was made. |
| `data/constituencies.csv` | The {N['seats']} seats: Leave estimates, census controls, settlement controls and every exposure variant. |
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

Hotham, T. (2026). Twinned with Europe, Voted Remain? Town twinning and the geography of the 2016 referendum in Great Britain. Zenodo. {{https://doi.org/10.5281/zenodo.24094355}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
Derived twinning tables (from Wikidata): CC0. Census and boundary derived data: Open Government Licence v3.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] Britain has {P['usable']:,} recorded town twinnings, {P['eu_pc']:.0f}% with EU towns. Did twinned places vote Remain? Comparing like with like: no ({f1(M['b'])} points)

**Body:**

Every twinning of a British town or council in Wikidata, placed in its constituency and set against the estimated 2016 Leave vote.

- France {R['country']['france']}, Germany {R['country']['germany']}, United States {R['country']['states']}, Italy {R['country']['italy']}, Poland {R['country']['poland']}, China {R['country']['china']}. Coventry has the most partners ({R['coventry']['n']}).
- {N['any_eu']} of {N['seats']} seats in Great Britain have an EU twin. Before any controls they voted {f1(R['ladder']['M1']['b'])} points more Leave.
- Same region, age, education, jobs, ethnicity, density and town size: {f1(M['b'])} points (95% range {f1(M['lo'])} to {f1(M['hi'])}). No Remain bonus.
- The placebo, twins outside the EU (US, China, Russia...): {f1(H2['noneu_alone']['b'])} points, but that disappears when comparing seats within one council area. It looks like the kind of place that twins, not Europe.
- Caveat: Wikidata knows big towns' twinnings far better than villages'. Test and checks written down before running.

Interactive map (tap any town or seat, or switch on lines to every partner town): {PAGE}

**Source comment:**

Data: Wikidata twinning records (CC0); Leave estimates by Chris Hanretty via parlitools; 2011 census (ONS, NRS); ONS/OS boundaries (OGL). Tools: Python (pandas, geopandas, statsmodels, matplotlib), MapLibre with OpenFreeMap tiles. Analysis plan, paper, data and code: {REPO}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
cover = f"""# Cover note: Twinned with Europe, Voted Remain?

## Suitable journals (checked 2026)

Each publishes subscription articles without an article processing charge (open access optional and paid). Word limits are from the publishers' author guidelines as last seen; recheck before submitting. The main text is about {R.get('paper_words', 7000):,} words before references, plus tables and figures.

1. **Political Geography** (Elsevier). Publishes work on twinning (Clarke 2009) and on the geography of Brexit; the place-level design and the twinning inventory fit its remit. Full-length articles up to 11,000 words (as listed in the Cirad journal directory, checked 2026); optional open access costs about 3,010 USD, subscription publication is free. The paper fits.
2. **Journal of Common Market Studies** (Wiley). The natural home for the transactionalist and European identity argument (it published Mitchell 2015 on the Erasmus effect). The UACES call for JCMS special issues (checked 2026) limits articles to 8,500 words including footnotes, appendices, figures and tables but excluding references; the general limit should be rechecked. The appendix tables would move to online supplementary material and the text would need light cutting.
3. **Comparative European Politics** (Palgrave Macmillan, Springer Nature). Hybrid journal with no charge for subscription publication; its word limit could not be confirmed at writing (the guidelines page was unreachable).

Also possible: **Journal of European Integration** (Taylor and Francis), if framed around integration from below.

## Summary of the contribution (for a cover letter)

Town twinning was one of the most widespread forms of organised European exchange in British localities, and transactionalist theory expects cross-border contact to build attachment to Europe. This paper builds an open national inventory of British twinnings from Wikidata ({P['usable']:,} links, {P['eu_pc']:.0f}% with EU partners), assigns them to the {N['seats']} constituencies of Great Britain with documented rules, and tests in an analysis pre-specified in a written plan whether seats with an EU twin had a lower estimated Leave share in 2016. Conditional on region, the standard census predictors and settlement size and documentation, the difference is {f1(M['b'])} points (95% CI {f1(M['lo'])} to {f1(M['hi'])}), null in all but two of {R['robust_summary']['n']} planned checks (an equivalence test at one point is not passed). A built-in placebo, twinning outside the EU, is associated with a slightly lower Leave share that disappears within local authorities, which points to selection into twinning rather than European contact. The paper contributes a reproducible dataset, a place-level null that excludes large associations but not one of about a point, and a design that separates European contact from the kind of place that twins. It is correlational and reports the uneven coverage of its source.
"""
open(os.path.join(ROOT, "release", "paper", "cover_note.md"), "w", encoding="utf-8").write(cover)
for name, txt in (("README", readme), ("post", post), ("cover", cover)):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in txt.replace("```", "").replace("|---|---|", ""), (name, bad)
print("README, LICENSE, post, cover note written")
