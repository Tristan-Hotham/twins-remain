# twins-remain: working notes

Brief: /home/claude/work/new12/BRIEFS.md section 4 (+ new11, new10, new9, new8 BRIEFS tops and /home/claude/newdata/BRIEF.md).
Format refs: studies/pm-streets, studies/wiki-vs-hansard (release layout); studies/beeching-leave (same outcome data and
controls, same unit). GIF: /home/claude/gifs/BRIEF.md, toolkit /home/claude/gifs/gifkit.py.
Work files: /home/claude/scratch/twins-remain (delete at the end by exact path).

## 0. Analysis plan (written before any outcome model was run)

Written after reading the twinning file (hosts, partners, countries, dates) and the census and Leave column lists only.
No twinning count had been joined to a Leave share when this section was written.

### Question
Do British places twinned with towns in other EU member states vote Remain more, beyond what their demography explains,
and is any such link about Europe, or about being the kind of place that twins at all?

### Unit, outcome, exposure
- Unit: Westminster constituency on 2010 boundaries, Great Britain (632 seats; Northern Ireland has no boundaries in the
  file and a different party system, so it is left out and the paper says "Great Britain").
- Outcome: estimated Leave share 2016 (Hanretty 2017 estimates as compiled in parlitools, `figure_to_use`, which uses
  counted ward results where known), in percentage points.
- Exposure data: Wikidata "twinned administrative body" (P190) statements on UK places (twins_wd.tsv). One row per
  host and partner after removing duplicate rows created by partners with several historical countries.
- Partner country: the partner's present sovereign state (historical states such as Austria-Hungary, the Soviet Union or
  the German Empire are ignored when the partner also has a present state). EU = the 27 other member states in June 2016.
  Non-EU = everything else (United States, China, Russia, Commonwealth, EFTA, Turkey, Greenland, the Faroes and so on).
  Partners inside the UK and hosts outside Great Britain are dropped.
- Host types (rules fixed now, applied before outcomes are joined):
  1. Local-authority hosts: a host whose name matches a 2013 local authority district (LAD) name (after removing
     "City of", "London Borough of", "Royal Borough of", "County Borough", "The") and whose point lies in or within 5 km
     of that LAD. Most English and Welsh twinnings are made by the district or city council, so these twinnings are
     assigned to every seat with at least a third of its area in that LAD (and to the seat holding the point).
  2. Settlement hosts (towns, villages, parishes, former districts abolished before 2013): assigned to the seat that
     contains the point (points up to 2 km offshore go to the nearest seat).
  3. Wide-area hosts (Greater London, shire counties, metropolitan counties, former regions such as Grampian, historic
     counties): left out of the main exposure, reported, and used in a sensitivity check (assigned to the seat holding
     the point).
  4. Not municipal (schools and academies): dropped and reported.
- Seat exposure: distinct EU partners reached by hosts assigned to the seat (n_eu), distinct non-EU partners (n_noneu);
  any_eu = n_eu > 0, any_noneu = n_noneu > 0; eu_per100k = n_eu per 100,000 residents (2011).

### Hypotheses
- H1 (main). Seats with at least one EU twinning have a lower Leave share than otherwise similar seats.
- H2 (Europe or twinning?). The EU twinning gap is larger (more negative) than the gap for non-EU twinnings, in a model
  with both; and among twinned seats, a higher EU share of partners goes with lower Leave.
- H3 (timing, secondary). If contact over decades matters, twinnings formed before UK accession (1973) go with a larger
  gap than later ones (dated twinnings only, which are a minority, so this is descriptive).

### Controls (the standard aggregate Leave predictors plus twinning-documentation proxies)
Region fixed effects (9 English regions, Wales, Scotland); 2011 census: % aged 65+, % degree level (level 4+), % no
qualifications, % routine and semi-routine occupations (NS-SEC), % White British, % born outside the UK, log population
density; documentation and size: log(1 + settlements in the seat with an English Wikipedia article), log(1 + population of
the largest such settlement), borough versus county seat.

### Main specification
OLS: leave ~ any_eu + controls, standard errors clustered by the seat's main 2013 local authority (LAD-level twinnings
make seats in one LAD share exposure). Report the coefficient in points with a 95% CI (t with clusters - 1 df) and N.
SESOI for an equivalence test: 1 point of Leave.

### Planned alternatives, placebos, robustness
- Model ladder: raw; region FE; + census; + documentation (main).
- H2: any_eu and any_noneu together, with a test of equality; non-EU twinning alone (placebo: if non-EU twinning predicts
  Remain as strongly, the link is about the kind of place that twins, not Europe); EU share of partners among twinned seats.
- Exposure variants: log(1 + n_eu); eu_per100k (log1p); point-only assignment (no LAD spreading); twinnings starting
  after 23 June 2016 removed; EU-15 partners only (pre-2004 members); France and Germany only; wide-area hosts added.
- Sample and outcome: seats with a counted (known) ward-based Leave figure only; Hanretty model-only estimate;
  England only; without London; leave one region out; drop top 1% Cook's distance.
- Specification: no documentation controls; local authority fixed effects (within-LAD comparison, identified only from
  settlement-level twinnings); EU-born share added; Conley spatial standard errors (50 km, 100 km).
- Matching: nearest neighbour on standardised controls within region (twinned with EU vs none), bias-corrected, bootstrap CI.
- Randomisation inference: any_eu shuffled within regions, 2,000 draws.
- Sensitivity to unobservables: Oster (2019) delta against the raw and region-only models.
- Timing (H3): among seats with dated EU twinnings, earliest EU twinning before 1973 vs 1973 or later (descriptive and
  a model on the twinned subset). Reverse causality: list EU twinnings recorded as ending after June 2016.
- Coverage: Wikidata P190 is incomplete. Report how many settlements have any twinning by size band; no external
  register is available in the workspace, so the coverage cannot be validated against council lists (flagged).

### What counts against the hypotheses
- H1 fails if the 95% CI includes zero and the point estimate is smaller in size than 1 point, or if the estimate is not
  negative. A significant estimate that the planned non-EU placebo matches (overlapping CIs, similar size) means the
  link is about twinning places, not Europe (H2 fails).
- The design is cross-sectional and correlational throughout: twinning is chosen by councils, and Remain-leaning places
  may twin more. No causal language beyond that.

## 1. Log
- Build (01_build.py): 1,612 raw rows -> 1,536 host-partner pairs after collapsing historical countries. Hosts: 487
  settlement, 219 local authority (name and point match a 2013 LAD), 11 wide area, 13 schools, 17 outside Great Britain
  (Northern Ireland towns, Gibraltar, Guernsey, Cayman Islands). Usable pairs (settlement or LAD host, foreign partner):
  1,451, of which 1,150 EU. Seats: 559 of 632 have at least one EU partner under the main assignment (local-authority
  twinnings spread to every seat with a third of its area in the LAD), so "none" is the small group (73 seats).
- Found at build (before outcomes): the Neath Port Talbot twinnings are recorded as ending in 2015; P190 keeps ended
  twinnings. The plan counts all recorded twinnings; an exploratory check drops those that ended before the referendum.

## 2. Results of the planned analysis (first run; recorded before any text was written)
- Main (M4): any EU twinning -0.13 points Leave (95% CI -1.28 to 1.01), N = 632, 356 LAD clusters. Null. TOST at 1 point
  not passed (p = 0.07): the data rule out effects larger than about 1.1 points in either direction (90% CI -1.09 to 0.83).
- Ladder: raw +2.4 (EU-twinned seats voted MORE Leave before controls), region FE +0.7, census -0.2, full -0.1.
- H2: non-EU twinning (planned placebo) -1.25 (-2.16 to -0.33), p = 0.007; jointly EU +0.17, non-EU -1.25, difference
  EU minus non-EU +1.42 (-0.15 to 2.99), p = 0.075. EU share of partners among twinned seats: +0.11 per 10 points (ns).
  So H1 fails and H2 fails in the planned sense: what association there is lies with non-EU (world) twinning.
- All planned robustness checks for the EU coefficient are null (range about -0.7 to +1.1, none significant).
- H3: of 1,150 EU pairs 299 (26%) are dated; pre-1973 first EU twinning -0.50 (-2.16 to 1.17), N = 277. Null.
- Exploratory (added after the plan): the non-EU coefficient survives leaving out any region (11 of 11 significant),
  England only, without London and the model-only outcome; it does not survive local authority fixed effects (-0.29,
  -2.19 to 1.61) or the counted-results sample (N = 128). Treat as a lead, not a finding.

## 3. References (41; verification)
Verified in this session by WebSearch/WebFetch (title, authors, year, venue, volume, pages, DOI; abstract read unless noted):
Vion 2002 (CEH 11(4) 623-640); Clarke 2009 (Pol Geog 28(8) 496-507); Clarke 2010 (CBH 24(2) 173-191); Falkenhain, Hölscher
and Ruser 2012 (J Civil Society 8(3) 229-250); Brakman, Garretsen and Oumer 2016 (Reg Studies 50(8) 1420-1432); Jayne,
Hubbard and Bell 2011 (City 15(1) 25-41); Cremer, De Bruin and Dupuis 2001 (AJES 60(1) 377-401); Joenniemi and Sergunin
2017 (JBS 32(4) 443-458); Warwick 2024 (Urban History 51(4) 709-724); Langenohl 2023 (Urban History, online, DOI only;
volume not shown on the page); Seth, Kunegis and Lambiotte 2018 (Wiki Workshop extended abstract, read in full);
Fligstein 2008 (OUP; publisher summary read); Kuhn 2015 (OUP; summary read); Pettigrew and Tropp 2006 (JPSP 90(5)
751-783); Sigalas 2010 (EUP 11(2) 241-265); Mitchell 2015 (JCMS 53(2) 330-348); Hooghe and Marks 2009 (BJPolS 39(1)
1-23); Carl, Dennison and Evans 2019 (EUP 20(2) 282-304); Goodwin and Milazzo 2017 (BJPIR 19(3) 450-464); Vrandečić and
Krötzsch 2014 (CACM 57 78-85; issue 10 from the download link); Graham et al. 2014 (Annals AAG 104(4) 746-764);
Deutsch et al. 1957 (Princeton UP; title and authors from the APSR review record); Hanretty 2017 (JEPOP; UEA record).
Partly verified: Kuhn 2011 (EJPR 50(6) 811-837, DOI 10.1111/j.1475-6765.2011.01987.x from the Wiley search result;
the article page was not reachable; the abstract read is that of the EUI thesis it comes from, same test and data).
Zelinsky 1991 (Annals AAG 81(1) 1-31, DOI from the Wiley record; abstract not reachable: cited only as a geographic
survey of sister cities, which is what its title says).
Reused from the beeching-leave study, where each was verified at review (NOTES there): Becker, Fetzer and Novy 2017;
Colantone and Stanig 2018; Goodwin and Heath 2016; Jennings and Stoker 2016; Hobolt 2016; Alabrese et al. 2019;
Abreu and Öner 2020; Harris and Charlton 2016; Johnston et al. 2018; Clarke, Goodwin and Whiteley 2017; Oster 2019;
Cameron and Miller 2015; Lakens 2017; Abadie and Imbens 2006; Conley 1999; Odell (parlitools).
Blocked at fetch (permission not available in this session): doi.org, tandfonline, jstor, api.crossref, Wiley pages,
Cambridge article pages for Warwick and Langenohl (their records were read on White Rose and NWU repositories).

## 4. Data check of the whole host list (after the first run, before any text)
- Read every host with three or more partners and every seat left without an EU twinning. Two classification errors
  in my own rule, now fixed: (1) Scottish council areas are named "Glasgow City", "Aberdeen City", "Dundee City", so the
  LAD name rule missed Glasgow, Aberdeen and Dundee (the rule now also strips a trailing "City" and ", County of");
  (2) "Greater London" (an urban-agglomeration item with 6 partners) was a settlement host; it is now wide area like
  London. One documented override: Brighton's twinnings are assigned to Brighton and Hove (code/overrides.csv).
- Checked and kept: Sherborne's 24 EU partners are the Douzelage network (one town in each member state).
- Effect of the fix on the main estimate: -0.13 (-1.28 to 1.01) became -0.30 (-1.41 to 0.80). Conclusions unchanged.
- Current planned results: main -0.30 (-1.41 to 0.80), N = 632; non-EU twinning -1.37 (-2.26 to -0.48), p = 0.003;
  EU minus non-EU +1.34 (-0.23 to 2.91), p = 0.095. Robustness: 2 of 15 checks significant (log count -0.72, -1.40 to
  -0.03; log per 100k -0.67, -1.35 to -0.00), but with the non-EU count in the model the EU count is -0.27 (ns).
  Matching (EU-twinned vs none, within region): -1.02 (-1.56 to -0.47); the bootstrap ignores matching uncertainty and
  only 58 control seats are used, so this is reported as the strongest planned check against the null, not as a finding.

## 5. Outputs and checks (end of build)
- Paper: release/paper/Hotham_Twins_Remain.pdf (23 pages, about 7,100 words before references, abstract 247 words,
  41 references, 8 appendix tables, 5 figures; https://doi.org/10.5281/zenodo.24094355 printed unless DOI is set). Cover note: release/paper/cover_note.md
  (Political Geography 11,000-word limit confirmed via the Cirad journal directory; JCMS 8,500 from the UACES special
  issue call; Comparative European Politics limit not confirmed).
- Page: index.html + js/page.js (MapLibre, Positron, layers panel, chips, search, popups, full-screen, site-nav.js).
  QA screenshots in qa/ at 1280 and 390 px; no console errors (only aborted tile requests during fly-to).
- Blog: release/blog/post.html (5 figures) + meta.json; Reddit: reddit/twins_remain_collage.png, post.md, collage.py,
  twins_remain.gif (copy of /home/claude/gifs/out/twins-remain.gif, script /home/claude/gifs/scripts/twins-remain.py).
- Every number in page, blog, paper, README, post, collage and GIF is filled from data/results.json; facts stated in
  words are asserted in 03_results.py, 05_build_site.py and 07_release.py.
- Limitation for the page arcs and GIF: partner towns have no coordinates in the raw file, so lines end at the
  partner country's centre (said on the page and in the GIF). Partner coordinates (Wikidata P625 of each partner item)
  would allow true town-to-town arcs.

## 6. Independent review (referee-style, 2026)

Reviewer did not build the study. Brief: BRIEFS.md section 4 of new12 and the shared rules it points to.

### Reproduction
- Re-ran 01 to 03 from the raw inputs before any change: results.json, model_tables.json, results_models.json,
  constituencies.csv and twinnings.csv were byte-identical to the builder's files.

### Data
- New input: raw_new12/twin_partner_coords.tsv (Wikidata P625 of partner items; 1,413 rows, 1,399 items, 14 items with two
  nearby points, averaged). 1,444 of the 1,445 usable twinnings have a partner point (missing: Lancaster's Perpignan
  Mediterranee Metropole). Used for display only (map, collage, GIF), never in a model. twinnings.csv gains plon/plat.
- Checked every partner point against Natural Earth countries: 31 fall outside the stated country, all coastal points
  just offshore or border towns (Halluin, Constance, Passau) except two disputed places. That check found a country
  error: Luhansk was resolved to Russia (Yalta correctly to Ukraine). Fixed by a documented rule preferring the
  internationally recognised state (Ukraine over Russia; Cyprus over Northern Cyprus for Morphou; Somalia over Somaliland
  for Borama). No exposure changes (all candidates are on the same side of the EU line), so every model estimate is
  unchanged; Russia 19 -> 18 and Ukraine 11 -> 12 twinnings, seats with a Russian partner 44 -> 40, Ukrainian 34 -> 38.
- Spot-checked text facts against the data: Leeds council twinnings reach all eight Leeds seats; Coventry and Volgograd
  from 1944; Klaksvik (Faroes and Denmark) resolved to the Faroes; Putney, Wimbledon and Ross, Skye and Lochaber have no
  EU twin; Wakefield is a council host.

### Exploratory checks added at review (in 02_models.py, results.json exploratory.review; labelled exploratory)
- Matching that also requires the same non-EU twinning status (exact within region x any_noneu; 474 matched seats):
  -0.32 (naive bootstrap -0.84 to 0.22). The planned matched -1.02 does not survive holding non-EU twinning fixed.
- Planned matching with a bootstrap that resamples seats within region and re-matches (500 draws): 95% interval -3.04 to
  0.63. The builder's naive interval (-1.56 to -0.47) was misleadingly narrow, as the builder suspected.
- Clustering on groups of seats linked by any shared council host (324 clusters instead of 356 LADs): EU -1.42 to 0.81;
  non-EU still significant (-2.26 to -0.47). Clustering choice does not drive anything.
- Seats whose largest documented settlement has 50,000+ people (where Wikidata coverage is best; N = 226, only 19 without
  an EU twin): EU +0.30 (-1.67 to 2.26); non-EU -1.26 (-2.64 to 0.12). Weak test, consistent with the main result.

### Text fixes
- Abstract: the placebo CI was printed without minus signs ("2.3 to 0.5"); "the most widespread form" (unverified) softened;
  "stable across fifteen planned checks" replaced by "thirteen of fifteen null"; the failed TOST at 1 point now stated;
  "reflects the kind of place" softened to "better read as a marker"; matched claim removed from the abstract. 246 words.
- Intro, discussion, conclusion: "voted Leave by -0.3 points more" rewritten; "Whatever links twinning to Remain, it is not
  Europe" softened; "stable across the planned checks" corrected; "what matters is" and "left no detectable mark" (causal)
  rephrased. Placebo coefficient described as "lower" rather than "-1.37 points different".
- Hanretty: the paper said Hanretty's estimates "combine ... ward-level results"; his paper remaps LA counts with a
  small-area model, and parlitools substitutes counted ward-based figures (Rosenbaum and others) for 128 seats. Fixed.
- Graham et al. 2014 was cited for small towns versus cities, which it does not show (it is about global unevenness of
  Wikipedia); citations reworded so our own Figure 2 carries the size claim.
- Table 9 (full coefficients) and Appendix A were never referenced; now referenced in the roadmap paragraph.
- Blog: "-0.3 points more", "as close to nothing as this kind of data gets" (TOST fails) and the unsigned placebo range
  fixed; "None of the planned checks finds a clear European effect" corrected (two count checks significant) and the
  matched result reported with its caveat. Page: same fixes, plus "The opposite happened" (wrong: the EU estimate is
  null, not positive). Post: raw difference now says "more Leave". Cover note: "precise null", "stable" fixed.
- Map: lines now run to each partner town (P625) with partner-town dots, popups for partner towns, legend note, the lines
  chip folds the title card and zooms out to Europe. Collage: Europe map with true arcs, legend moved off the map onto
  paper, axis labels removed. GIF: arcs to partner towns; final counter "1,444 lines drawn" (one twinning has no point);
  final frame checked, no overlap.

### References
- Verified at review (title, authors, year, venue, volume, pages, DOI; abstract or record read): Zelinsky 1991 (via the
  Joenniemi and Sergunin reference list and its page citations; Wiley page not reachable), Kuhn 2011 (EJPR 50(6) 811-837,
  abstract read on the Cambridge EJPR issue page; now fully verified), Langenohl 2023 (NWU record; volume still not shown),
  Warwick 2024, Joenniemi and Sergunin 2017, Cremer et al. 2001, Jayne et al. 2011 and Clarke 2009 (reference list),
  Clarke 2010, Brakman et al. 2016, Falkenhain et al. 2012, Vion 2002, Mitchell 2015, Sigalas 2010, Carl et al. 2019,
  Graham et al. 2014, Hanretty 2017, Seth et al. 2018, Goodwin and Milazzo 2017, Pettigrew and Tropp 2006. All 41 cited
  and present. No reference removed.
- Journal word limits: JCMS and Comparative European Politics guideline pages could not be fetched at review (permission
  blocked); the cover note already flags both for rechecking.

### What a referee would still ask for
- Validation of Wikidata twinning against an external register (council websites or the LGA/Town Twinning Association
  lists) for a random sample of towns, to estimate missingness by size and region.
- Town-level or ward-level outcomes (e.g. counted ward results for the 128 seats) with town-level exposure, rather than
  constituency aggregates that dilute a few hundred participants.
- Measures of activity (visits, funding, Europe for Citizens grants) rather than the bare existence of a link.
- A sharper selection model for the non-EU association (e.g. city-region or LAD-level analysis), since it is a
  between-council contrast.
