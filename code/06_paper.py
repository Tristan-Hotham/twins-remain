"""Step 6: the paper. Fills code/paper_template.tex from data/results.json, builds the tables, compiles with xelatex and bibtex.
Output: release/paper/Hotham_Twins_Remain.pdf and .tex beside the f_*.png figures and refs.bib.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24094355 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/06_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
TAB = jload(f"{DATA}/model_tables.json")
OUT = FIG; NAME = "Hotham_Twins_Remain"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f in ("f0", "f1", "f2", "f3", "abs1", "abs2", "pc1"): return fmt(v, f).replace("%", "\\%")
    if f == "p3": return "$<$0.001" if float(v) < 0.001 else f"{float(v):.3f}"
    return tex(str(v))


pv = lambda p: "$<$0.001" if p < 0.001 else f"{p:.3f}"
z = lambda v, d=2: fmt(v, f"f{d}")


def row(c, lab):
    return f"{tex(lab)} & {z(c['b'])} & [{z(c['lo'])}, {z(c['hi'])}] & {pv(c['p'])} & {c['n']:,}\\\\\n"


def tab(label, cap, cols, head, rows, note, size="\\footnotesize"):
    return ("\\begin{table}[H]\\centering" + size + "\\begin{threeparttable}\\caption{" + cap + "}\\label{tab:" + label + "}"
            "\\begin{tabular}{" + cols + "}\\toprule " + head + "\\\\\\midrule\n" + rows +
            "\\bottomrule\\end{tabular}\\begin{tablenotes}\\footnotesize\\item " + note + "\\end{tablenotes}\\end{threeparttable}\\end{table}")


HEAD = "Specification & $\\beta$ & 95\\% CI & $p$ & N"
NOTE = ("$\\beta$: difference in the estimated Leave share (percentage points). OLS with region fixed effects, the 2011 census controls and the "
        "documentation controls unless stated; standard errors clustered by local authority.")
# descriptives
B = R["balance"]
lab = {"pct_65plus": "Aged 65 or over (\\%)", "pct_degree": "Degree level (\\%)", "pct_noqual": "No qualifications (\\%)",
       "pct_routine": "Routine and semi-routine occupations (\\%)", "pct_whitebrit": "White British (\\%)", "pct_foreignborn": "Born outside the UK (\\%)",
       "ldens": "log density (persons per hectare)", "lset": "log(1 + settlements with an article)", "lbig": "log(1 + largest settlement population)",
       "county_seat": "County constituency (share)", "pop2011": "Population 2011", "density": "Density (persons per hectare)"}
rows = "".join(f"{lab[k]} & {B[k]['eu']:,.2f} & {B[k]['none']:,.2f}\\\\\n" for k in lab)
rows += f"Leave share (\\%) & {R['desc']['leave_eu']:.2f} & {R['desc']['leave_noeu']:.2f}\\\\\nSeats & {R['n']['any_eu']} & {R['n']['no_eu']}\\\\\n"
T_DESC = tab("desc", "Seats with and without an EU twin: means of the outcome and controls.", "lrr", "Variable & EU twin & No EU twin", rows,
             "Great Britain, 2010 constituencies. Census 2011; settlements from Wikidata.")
# ladder and H2
L = R["ladder"]; H2 = R["h2"]
rows = row(L["M1"], "M1: no controls") + row(L["M2"], "M2: region fixed effects") + row(L["M3"], "M3: + 2011 census") + row(L["M4"], "M4: + documentation (main, planned)")
rows += "\\midrule\\multicolumn{5}{l}{\\textit{H2: Europe or twinning (planned)}}\\\\\n"
rows += row(H2["noneu_alone"], "Any non-EU partner (placebo)") + row(H2["joint_eu"], "Joint model: any EU partner") + row(H2["joint_noneu"], "Joint model: any non-EU partner")
rows += row(H2["diff"], "Difference, EU minus non-EU") + row(H2["noneu_within_eu"], "Any non-EU partner, EU-twinned seats only")
rows += row(H2["eu_share"], "EU share of partners, per 10 points (twinned seats)") + row(H2["count_eu"], "log(1 + EU partners), with non-EU count") + row(H2["count_noneu"], "log(1 + non-EU partners), with EU count")
rows += "\\midrule\\multicolumn{5}{l}{\\textit{H3: timing (planned, dated twinnings only)}}\\\\\n" + row(R["h3"]["model"], "First dated EU twin before 1973")
T_LADDER = tab("ladder", "The model ladder for an EU twin, and the planned tests of H2 and H3.", "p{8.2cm}rcrr", HEAD, rows, NOTE)
# robustness
rb = R["robust"]
rows = ""
for grp, title in (("exposure", "Exposure"), ("sample", "Sample and outcome"), ("spec", "Specification")):
    rows += f"\\midrule\\multicolumn{{5}}{{l}}{{\\textit{{{title}}}}}\\\\\n"
    for k, c in rb.items():
        if c["group"] == grp:
            rows += row(c, c["label"])
rows += "\\midrule\\multicolumn{5}{l}{\\textit{Inference}}\\\\\n"
rows += row(R["conley"]["km50"], "Conley standard errors, 50 km") + row(R["conley"]["km100"], "Conley standard errors, 100 km")
rows += f"Randomisation inference (2,000 within-region shuffles) & {z(R['ri']['obs'])} & & {R['ri']['p_two']:.3f} & {R['n']['seats']}\\\\\n"
m = R["match"]
rows += f"Matched seats, bias-corrected (naive bootstrap interval) & {z(m['att'])} & [{z(m['lo'])}, {z(m['hi'])}] & & {m['n_pairs']}\\\\\n"
rows += "\\midrule\\multicolumn{5}{l}{\\textit{Exploratory (added after the planned analysis)}}\\\\\n" + row(R["exploratory"]["active"], R["exploratory"]["active"]["label"])
T_ROBUST = tab("robust", "Planned robustness checks for the EU twin coefficient.", "p{8.2cm}rcrr", HEAD, "".join(rows.split("\\midrule", 1)[1:]).join(["\\midrule", ""]) if False else rows.replace("\\midrule", "", 1),
               NOTE + " Exposure rows other than the two log measures use an indicator; the log rows are per unit of the log measure.")
# non-EU exploratory
ne = R["exploratory"]["noneu"]
rows = row(H2["joint_noneu"], "Joint model (planned)") + "".join(row(ne[k], ne[k]["label"]) for k in ("known", "england", "nolondon", "ladfe", "nodoc", "leave_ch"))
rows += f"Leave one region out: range of estimates & \\multicolumn{{2}}{{l}}{{{z(ne['loro_max'])} to {z(ne['loro_min'])}}} & \\multicolumn{{2}}{{l}}{{{ne['loro_n_sig']} of 11 with $p<0.05$}}\\\\\n"
T_NOENEU = tab("noneu", "Exploratory: checks on the non-EU twinning coefficient (joint model with the EU indicator).", "p{8.2cm}rcrr", HEAD, rows, NOTE)
# LORO
rows = "".join(row(v, k) for k, v in R["loro"].items())
T_LORO = tab("loro", "Leaving out one region at a time (main specification).", "p{8.2cm}rcrr", "Region left out & $\\beta$ & 95\\% CI & $p$ & N", rows, NOTE)
# full coefficient table
nm = {"any_eu": "Any EU partner", "any_noneu": "Any non-EU partner", "pct_65plus": "Aged 65+ (\\%)", "pct_degree": "Degree level (\\%)",
      "pct_noqual": "No qualifications (\\%)", "pct_routine": "Routine occupations (\\%)", "pct_whitebrit": "White British (\\%)",
      "pct_foreignborn": "Born outside UK (\\%)", "ldens": "log density", "lset": "log(1 + settlements)", "lbig": "log(1 + largest settlement)",
      "county_seat": "County constituency", "Intercept": "Constant"}
cols = ["M1", "M2", "M3", "M4", "H2joint"]
terms = [t for t in dict.fromkeys(r["term"] for c in cols for r in TAB[c]["rows"]) if not t.startswith("C(region)")]
terms = sorted(terms, key=lambda t: list(nm).index(t) if t in nm else 99)
star = lambda p: "^{**}" if p < 0.01 else "^{*}" if p < 0.05 else ""
rows = ""
for t in terms:
    cells = []
    for c in cols:
        rr = {r["term"]: r for r in TAB[c]["rows"]}
        cells.append(f"${rr[t]['b']:.3f}{star(rr[t]['p'])}$ ({rr[t]['se']:.3f})" if t in rr else "")
    rows += f"{nm.get(t, tex(t))} & " + " & ".join(cells) + "\\\\\n"
rows += "\\midrule Region fixed effects & no & yes & yes & yes & yes\\\\\nN & " + " & ".join(str(TAB[c]["n"]) for c in cols) + "\\\\\n"
rows += "$R^2$ & " + " & ".join(f"{TAB[c]['r2']:.3f}" for c in cols) + "\\\\\n"
T_FULL = tab("full", "Full coefficients: model ladder (M1 to M4) and the joint H2 model.", "lrrrrr", "Term & M1 & M2 & M3 & M4 & H2 joint", rows,
             "Outcome: estimated Leave share (\\%). Standard errors clustered by local authority in brackets; $^{*}p<0.05$, $^{**}p<0.01$. Region effects not shown (reference: East Midlands).", size="\\scriptsize")
# hosts
hd = {"settlement": "Settlement (town, village, parish, former district): seat of the point", "lad": "Local authority (name and point match a 2013 district): seats mostly inside it",
      "wide": "Wide area (Greater London, counties, former regions): excluded", "school": "School or academy: excluded", "outside": "Outside Great Britain: excluded"}
pairs_by = R["build"]["host_types_pairs"]
rows = "".join(f"{hd[k]} & {R['hosts'][k]} & {pairs_by.get(k, 0)}\\\\\n" for k in hd)
T_HOSTS = tab("hosts", "Twinning hosts by class, with the rule that assigns them to constituencies.", "p{10.5cm}rr", "Host class and assignment & Hosts & Pairs", rows,
              "Pairs: host and partner pairs before dropping domestic partners and partners without a country.")
bc = R["by_country"]
half = (len(bc) + 1) // 2
rows = ""
for i in range(min(half, 22)):
    a = bc[i]; b = bc[i + half] if i + half < len(bc) else None
    f = lambda x: f"{tex(x['country'])}{' (EU)' if x['eu'] else ''} & {x['n']}"
    rows += f(a) + " & " + (f(b) if b else " & ") + "\\\\\n"
rest = bc[half + 22:] if len(bc) > half + 22 else []
T_COUNTRY = tab("country", "Usable twinnings by the partner's present country (main hosts, foreign partners).", "lrlr", "Country & Twinnings & Country & Twinnings", rows,
                f"{len(bc)} countries in all; the table shows the {min(half, 22) * 2} largest groups by column. EU: member state on 23 June 2016.", size="\\scriptsize")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_DESC", T_DESC), ("TABLE_LADDER", T_LADDER), ("TABLE_ROBUST", T_ROBUST), ("TABLE_NOENEU", T_NOENEU), ("TABLE_LORO", T_LORO),
             ("TABLE_FULL", T_FULL), ("TABLE_HOSTS", T_HOSTS), ("TABLE_COUNTRY", T_COUNTRY)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("DOIPLACEHOLDER", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t.replace("\\{\\{DOI", "") and "--" not in t and "—" not in t and "–" not in t, [l for l in t.splitlines() if "{{" in l or "--" in l][:5]
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
bib = open(os.path.join(ROOT, "code", "refs.bib"), encoding="utf-8").read().replace("--", "-")
open(os.path.join(OUT, "refs.bib"), "w", encoding="utf-8").write(bib)
run = lambda *a: subprocess.run(list(a), cwd=OUT, capture_output=True, text=True)
run("xelatex", "-interaction=nonstopmode", NAME + ".tex")
b = run("bibtex", NAME)
bbl = os.path.join(OUT, NAME + ".bbl")
s = open(bbl, encoding="utf-8").read().replace("--", "-")
open(bbl, "w", encoding="utf-8").write(s)
for _ in range(2):
    r = run("xelatex", "-interaction=nonstopmode", NAME + ".tex")
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print("bibtex warnings:", [l for l in b.stdout.splitlines() if "Warning" in l][:10])
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("References")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
