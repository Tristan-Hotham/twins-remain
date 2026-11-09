"""Step 2. The planned models (NOTES.md section 0): ladder, H2 (EU versus non-EU twinning), exposure variants,
sample and outcome checks, leave-one-region-out, matching, randomisation inference, Oster delta, timing (H3).

Reads data/constituencies.csv and data/twinnings.csv; writes data/results_models.json (merged into results.json by step 3)
and data/model_tables.json (full coefficient tables for the paper appendix).
"""
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(SEED)
D = pd.read_csv(f"{DATA}/constituencies.csv")
D["ldens"] = np.log(D.density)
D["lset"] = np.log1p(D.n_settle)
D["lbig"] = np.log1p(D.max_settle_pop)
D["county_seat"] = (D.ctype == "County").astype(int)
D["l_neu"] = np.log1p(D.n_eu)
D["l_per100k"] = np.log1p(D.eu_per100k)
for v in ("point", "wide", "preref", "active", "settle"):
    D[f"any_eu_{v}"] = (D[f"n_eu_{v}"] > 0).astype(int)
D["any_noneu_point"] = (D.n_noneu_point > 0).astype(int)
D["any_noneu_active"] = (D.n_noneu_active > 0).astype(int)
D["any_eu15"] = (D.n_eu15 > 0).astype(int)
D["any_frde"] = (D.n_frde > 0).astype(int)
D["any_eu_new"] = (D.n_eu_new > 0).astype(int)
D["n_all"] = D.n_eu + D.n_noneu
D["eu_share"] = np.where(D.n_all > 0, D.n_eu / D.n_all.where(D.n_all > 0) * 100, np.nan)
D["only_noneu"] = ((D.n_eu == 0) & (D.n_noneu > 0)).astype(int)

CEN = ["pct_65plus", "pct_degree", "pct_noqual", "pct_routine", "pct_whitebrit", "pct_foreignborn", "ldens"]
DOC = ["lset", "lbig", "county_seat"]
FULL = "C(region) + " + " + ".join(CEN + DOC)
R = {"n": {"seats": int(len(D)), "lads": int(D.lad.nunique()), "regions": int(D.region.nunique()),
           "any_eu": int(D.any_eu.sum()), "no_eu": int((D.any_eu == 0).sum()), "any_noneu": int(D.any_noneu.sum()),
           "only_noneu": int(D.only_noneu.sum()), "no_twin": int((D.n_all == 0).sum()), "known": int(D.leave_known.sum())}}
TAB = {}


def fit(formula, data, cluster="lad", weights=None):
    d = data.copy()
    m = smf.ols(formula, d)
    res0 = m.fit()
    idx = res0.model.data.row_labels
    g = pd.factorize(d.loc[idx, cluster])[0]
    return m.fit(cov_type="cluster", cov_kwds={"groups": g}), len(idx), len(np.unique(g))


def coef(res, n, ng, var="any_eu", scale=1.0):
    b, se = res.params[var], res.bse[var]
    q = stats.t.ppf(0.975, ng - 1)
    return {"b": b * scale, "se": se * scale, "lo": (b - q * se) * scale, "hi": (b + q * se) * scale,
            "p": float(2 * stats.t.sf(abs(b / se), ng - 1)), "n": int(n), "clusters": int(ng), "r2": float(res.rsquared)}


def table(res, name, keep=None):
    rows = []
    for k in res.params.index:
        if keep and not any(k.startswith(p) for p in keep):
            continue
        rows.append({"term": k, "b": float(res.params[k]), "se": float(res.bse[k]), "p": float(res.pvalues[k])})
    TAB[name] = {"rows": rows, "n": int(res.nobs), "r2": float(res.rsquared), "r2_adj": float(res.rsquared_adj)}


KEEP = ["any_eu", "any_noneu", "Intercept", "C(region)"] + CEN + DOC

# ---------------------------------------------------------------- descriptives
R["desc"] = {"leave_mean": float(D.leave.mean()), "leave_sd": float(D.leave.std()),
             "leave_eu": float(D[D.any_eu == 1].leave.mean()), "leave_noeu": float(D[D.any_eu == 0].leave.mean()),
             "leave_twin": float(D[D.n_all > 0].leave.mean()), "leave_notwin": float(D[D.n_all == 0].leave.mean()),
             "n_eu_median": float(D.n_eu.median()), "n_eu_mean": float(D.n_eu.mean()), "n_eu_max": int(D.n_eu.max())}
R["desc"]["gap_raw"] = R["desc"]["leave_eu"] - R["desc"]["leave_noeu"]
bal = {}
for v in CEN + DOC + ["pop2011", "density"]:
    bal[v] = {"eu": float(D[D.any_eu == 1][v].mean()), "none": float(D[D.any_eu == 0][v].mean())}
R["balance"] = bal
bins = pd.cut(D.n_eu, [-1, 0, 2, 5, 100], labels=["0", "1 to 2", "3 to 5", "6 or more"])
R["by_neu"] = [{"bin": str(k), "n": int(len(g)), "leave": float(g.leave.mean()), "degree": float(g.pct_degree.mean()),
                "age": float(g.pct_65plus.mean())} for k, g in D.groupby(bins)]
R["by_region"] = [{"region": k, "n": int(len(g)), "any_eu": int(g.any_eu.sum()), "pc_eu": float(g.any_eu.mean() * 100),
                   "leave_eu": float(g[g.any_eu == 1].leave.mean()) if g.any_eu.sum() else None,
                   "leave_none": float(g[g.any_eu == 0].leave.mean()) if (g.any_eu == 0).sum() else None}
                  for k, g in D.groupby("region")]

# ---------------------------------------------------------------- model ladder (M4 = planned main)
L = {}
for name, rhs in (("M1", "any_eu"), ("M2", "any_eu + C(region)"), ("M3", "any_eu + C(region) + " + " + ".join(CEN)),
                  ("M4", f"any_eu + {FULL}")):
    res, n, ng = fit(f"leave ~ {rhs}", D)
    L[name] = coef(res, n, ng)
    table(res, name, keep=KEEP)
    if name == "M4":
        MAINRES = res
R["ladder"] = L
R["main"] = L["M4"]
b, se, ng = MAINRES.params["any_eu"], MAINRES.bse["any_eu"], L["M4"]["clusters"]
q90 = stats.t.ppf(0.95, ng - 1)
p_lo, p_hi = stats.t.sf((b + 1) / se, ng - 1), stats.t.cdf((b - 1) / se, ng - 1)
R["tost"] = {"sesoi": 1.0, "lo90": b - q90 * se, "hi90": b + q90 * se, "p": float(max(p_lo, p_hi)), "equivalent": bool(max(p_lo, p_hi) < 0.05)}
qq = stats.t.ppf(0.975, ng - 1) + stats.t.ppf(0.80, ng - 1)
R["mde80"] = float(qq * se)


def oster(short, full, rmax_mult=1.3):
    b0, r0, b1, r1 = short["b"], short["r2"], full["b"], full["r2"]
    rmax = min(1.0, rmax_mult * r1)
    if (b0 - b1) == 0 or (rmax - r1) == 0:
        return None
    return float(b1 * (r1 - r0) / ((b0 - b1) * (rmax - r1)))


R["oster"] = {"delta_vs_M1": oster(L["M1"], L["M4"]), "delta_vs_M2": oster(L["M2"], L["M4"])}
b0, r0, b1, r1 = L["M1"]["b"], L["M1"]["r2"], L["M4"]["b"], L["M4"]["r2"]
R["oster"]["bstar_delta1"] = float(b1 - (b0 - b1) * (min(1, 1.3 * r1) - r1) / (r1 - r0))

# ---------------------------------------------------------------- H2: Europe or twinning?
H2 = {}
res, n, ng = fit(f"leave ~ any_eu + any_noneu + {FULL}", D)
H2["joint_eu"] = coef(res, n, ng, "any_eu")
H2["joint_noneu"] = coef(res, n, ng, "any_noneu")
w = res.t_test("any_eu - any_noneu = 0")
dd, dse = float(np.squeeze(w.effect)), float(np.squeeze(w.sd))
qd = stats.t.ppf(0.975, ng - 1)
H2["diff"] = {"b": dd, "se": dse, "lo": dd - qd * dse, "hi": dd + qd * dse, "p": float(2 * stats.t.sf(abs(dd / dse), ng - 1)), "n": int(n)}
table(res, "H2joint", keep=KEEP)
res, n, ng = fit(f"leave ~ any_noneu + {FULL}", D)
H2["noneu_alone"] = coef(res, n, ng, "any_noneu")
res, n, ng = fit(f"leave ~ any_noneu + {FULL}", D[D.any_eu == 1])
H2["noneu_within_eu"] = coef(res, n, ng, "any_noneu")
TW = D[D.n_all > 0]
res, n, ng = fit(f"leave ~ eu_share + np.log1p(n_all) + {FULL}", TW)
H2["eu_share"] = coef(res, n, ng, "eu_share", scale=10.0)
H2["eu_share"]["mean_share"] = float(TW.eu_share.mean())
res, n, ng = fit(f"leave ~ np.log1p(n_eu) + np.log1p(n_noneu) + {FULL}", D)
H2["count_eu"] = coef(res, n, ng, "np.log1p(n_eu)")
H2["count_noneu"] = coef(res, n, ng, "np.log1p(n_noneu)")
R["h2"] = H2

# ---------------------------------------------------------------- robustness (planned)
RB = {}


def rb(key, label, formula, data, var="any_eu", cluster="lad", scale=1.0, group="spec"):
    res, n, ng = fit(formula, data, cluster=cluster)
    c = coef(res, n, ng, var, scale=scale)
    c["label"], c["group"] = label, group
    RB[key] = c
    return res


rb("main", "Main specification (M4)", f"leave ~ any_eu + {FULL}", D, group="main")
# exposure variants
rb("l_neu", "log(1 + EU partners)", f"leave ~ l_neu + {FULL}", D, var="l_neu", group="exposure")
rb("l_per100k", "log(1 + EU partners per 100,000)", f"leave ~ l_per100k + {FULL}", D, var="l_per100k", group="exposure")
rb("point", "Point assignment only (no spreading over the council area)", f"leave ~ any_eu_point + {FULL}", D, var="any_eu_point", group="exposure")
rb("preref", "Twinnings begun after June 2016 removed", f"leave ~ any_eu_preref + {FULL}", D, var="any_eu_preref", group="exposure")
rb("eu15", "EU-15 partners only (member before 2004)", f"leave ~ any_eu15 + {FULL}", D, var="any_eu15", group="exposure")
rb("frde", "French and German partners only", f"leave ~ any_frde + {FULL}", D, var="any_frde", group="exposure")
rb("wide", "Wide-area hosts added (counties, Greater London)", f"leave ~ any_eu_wide + {FULL}", D, var="any_eu_wide", group="exposure")
# sample and outcome
rb("known", "Seats with a counted (ward-based) Leave figure", f"leave ~ any_eu + {FULL}", D[D.leave_known], group="sample")
rb("leave_ch", "Outcome: Hanretty model estimate only", f"leave_ch ~ any_eu + {FULL}", D, group="sample")
rb("england", "England only", f"leave ~ any_eu + {FULL}", D[D.country == "England"], group="sample")
rb("nolondon", "Without London", f"leave ~ any_eu + {FULL}", D[D.region != "London"], group="sample")
infl = MAINRES.get_influence().cooks_distance[0]
keep = MAINRES.model.data.row_labels[infl <= np.quantile(infl, 0.99)]
rb("cooks", "Drop top 1% Cook's distance", f"leave ~ any_eu + {FULL}", D.loc[keep], group="sample")
# specification
rb("nodoc", "No documentation controls", "leave ~ any_eu + C(region) + " + " + ".join(CEN), D, group="spec")
rb("eu_born", "Add % born in Ireland or other EU", f"leave ~ any_eu + pct_eu_born + {FULL}", D, group="spec")
rb("ladfe", "Local authority fixed effects (within-council)", "leave ~ any_eu + C(lad) + " + " + ".join(CEN + DOC), D, group="spec")
R["ladfe_identifying"] = int(D.groupby("lad").any_eu.agg(lambda s: s.nunique() > 1).sum())
R["robust"] = RB

# Conley spatial HAC
CV = {}
Xm, e = MAINRES.model.exog, MAINRES.resid.values
ix = list(MAINRES.model.exog_names).index("any_eu")
xy = D.loc[MAINRES.model.data.row_labels, ["cx", "cy"]].values
dist = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
bread = np.linalg.inv(Xm.T @ Xm); u = Xm * e[:, None]
for km in (50, 100):
    K = (dist <= km * 1000).astype(float)
    V = bread @ (u.T @ K @ u) @ bread
    s_ = float(np.sqrt(V[ix, ix])); b_ = float(MAINRES.params["any_eu"])
    CV[f"km{km}"] = {"b": b_, "se": s_, "lo": b_ - 1.96 * s_, "hi": b_ + 1.96 * s_, "p": float(2 * stats.norm.sf(abs(b_ / s_))), "n": int(len(e))}
R["conley"] = CV

# leave one region out
LORO = {}
for r in sorted(D.region.unique()):
    res, n, ng = fit(f"leave ~ any_eu + {FULL}", D[D.region != r])
    LORO[r] = coef(res, n, ng)
R["loro"] = LORO
R["loro_range"] = {"min": min(v["b"] for v in LORO.values()), "max": max(v["b"] for v in LORO.values()),
                   "n_sig": int(sum(v["p"] < 0.05 for v in LORO.values())), "n": len(LORO)}

# randomisation inference: shuffle any_eu within region (FWL with the other controls held fixed)
import patsy
y, X = patsy.dmatrices(f"leave ~ {FULL}", D, return_type="dataframe")
Mx = X.values
P = np.eye(len(Mx)) - Mx @ np.linalg.pinv(Mx)
ry = P @ y.values.ravel()
x0 = D.any_eu.values.astype(float)
bobs = float((P @ x0) @ ry / ((P @ x0) @ (P @ x0)))
reg = D.region.values
draws = []
for _ in range(2000):
    xs = x0.copy()
    for g in np.unique(reg):
        m = reg == g
        xs[m] = rng.permutation(xs[m])
    rx = P @ xs
    draws.append(rx @ ry / (rx @ rx))
draws = np.array(draws)
R["ri"] = {"obs": bobs, "draws": 2000, "p_two": float((np.abs(draws) >= abs(bobs)).mean()), "count": int((np.abs(draws) >= abs(bobs)).sum())}

# ---------------------------------------------------------------- matching: EU-twinned seats vs seats with none, within region
MV = CEN + DOC
Z = D.copy()
Xs = (Z[MV] - Z[MV].mean()) / Z[MV].std()
VI = np.linalg.pinv(np.cov(Xs.T.values))
tr, co = Z[Z.any_eu == 1], Z[Z.any_eu == 0]
pairs = []
for i, r in tr.iterrows():
    c = co[co.region == r.region]
    if len(c) == 0:
        continue
    dx = Xs.loc[c.index].values - Xs.loc[i].values
    d2 = np.einsum("ij,jk,ik->i", dx, VI, dx)
    pairs.append((i, c.index[int(np.argmin(d2))]))
pt = np.array([p[0] for p in pairs]); pcn = np.array([p[1] for p in pairs])
bc = smf.ols("leave ~ " + " + ".join(MV), co).fit()
diff = Z.loc[pt, "leave"].values - Z.loc[pcn, "leave"].values
diff_bc = diff - (bc.predict(Z.loc[pt]).values - bc.predict(Z.loc[pcn]).values)
boots = [diff_bc[rng.integers(0, len(diff_bc), len(diff_bc))].mean() for _ in range(2000)]
smd = lambda a, b, v: float((a[v].mean() - b[v].mean()) / np.sqrt((a[v].var() + b[v].var()) / 2))
R["match"] = {"n_treated": int(len(tr)), "n_control_pool": int(len(co)), "n_pairs": len(pairs), "n_controls_used": int(len(set(pcn))),
              "att_raw": float(diff.mean()), "att": float(diff_bc.mean()), "lo": float(np.percentile(boots, 2.5)), "hi": float(np.percentile(boots, 97.5)),
              "balance": {v: {"before": smd(tr, co, v), "after": smd(Z.loc[pt], Z.loc[pcn], v)} for v in MV}}
R["match"]["max_abs_smd_before"] = max(abs(v["before"]) for v in R["match"]["balance"].values())
R["match"]["max_abs_smd_after"] = max(abs(v["after"]) for v in R["match"]["balance"].values())

# ---------------------------------------------------------------- H3 timing (dated EU twinnings only)
TT = pd.read_csv(f"{DATA}/twinnings.csv", keep_default_na=False)
TT["start_year"] = pd.to_numeric(TT.start.str[:4], errors="coerce")
usable = TT[TT.host_type.isin(["lad", "settlement"]) & (TT.country_q != "") & (TT.domestic.astype(str) != "True")]
eu = usable[usable.eu.astype(str) == "True"]
H3 = {"pairs_eu": int(len(eu)), "dated_eu": int(eu.start_year.notna().sum()), "dated_pc": float(eu.start_year.notna().mean() * 100),
      "pre73": int((eu.start_year < 1973).sum()), "post73": int((eu.start_year >= 1973).sum()),
      "after_ref": int((eu.start >= "2016-06-23").sum()), "dated_all": int(usable.start_year.notna().sum())}
dec = eu.dropna(subset=["start_year"]).assign(dec=lambda x: (x.start_year // 10 * 10).astype(int)).groupby("dec").size()
H3["by_decade"] = [{"decade": int(k), "n": int(v)} for k, v in dec.items()]
DT = D[D.n_eu_dated > 0].copy()
DT["pre73"] = (DT.first_eu_year < 1973).astype(int)
res, n, ng = fit(f"leave ~ pre73 + {FULL}", DT)
H3["model"] = coef(res, n, ng, "pre73")
H3["model"]["n_pre73"] = int(DT.pre73.sum())
H3["leave_pre73"] = float(DT[DT.pre73 == 1].leave.mean()); H3["leave_post73"] = float(DT[DT.pre73 == 0].leave.mean())
ended = usable[(usable.end != "")].copy()
H3["ended"] = int(len(ended))
H3["ended_after_ref"] = [{"host": r.host_name, "partner": r.partner_name, "country": r.country, "eu": str(r.eu) == "True", "end": r.end[:4],
                          "start": r.start[:4]} for r in ended[ended.end >= "2016-06-23"].itertuples()]
H3["ended_after_ref_eu"] = int(sum(x["eu"] for x in H3["ended_after_ref"]))
R["h3"] = H3

# ---------------------------------------------------------------- exploratory (added after the planned analysis)
EX = {}
res, n, ng = fit(f"leave ~ any_eu_active + {FULL}", D)
EX["active"] = coef(res, n, ng, "any_eu_active"); EX["active"]["label"] = "Twinnings ended before the referendum removed"
res, n, ng = fit(f"leave ~ any_eu_active + any_noneu_active + {FULL}", D)
EX["active_joint_noneu"] = coef(res, n, ng, "any_noneu_active")
res, n, ng = fit(f"leave ~ any_eu_point + any_noneu_point + {FULL}", D)
EX["point_joint_eu"] = coef(res, n, ng, "any_eu_point"); EX["point_joint_noneu"] = coef(res, n, ng, "any_noneu_point")
# the non-EU association: does it survive the same checks as the main estimate?
NE = {}
for key, lab, f, dat in (("known", "Counted Leave figure only", f"leave ~ any_noneu + any_eu + {FULL}", D[D.leave_known]),
                         ("england", "England only", f"leave ~ any_noneu + any_eu + {FULL}", D[D.country == "England"]),
                         ("nolondon", "Without London", f"leave ~ any_noneu + any_eu + {FULL}", D[D.region != "London"]),
                         ("ladfe", "Local authority fixed effects", "leave ~ any_noneu + any_eu + C(lad) + " + " + ".join(CEN + DOC), D),
                         ("nodoc", "No documentation controls", "leave ~ any_noneu + any_eu + C(region) + " + " + ".join(CEN), D),
                         ("leave_ch", "Outcome: Hanretty model estimate only", f"leave_ch ~ any_noneu + any_eu + {FULL}", D)):
    res, n, ng = fit(f, dat)
    NE[key] = coef(res, n, ng, "any_noneu"); NE[key]["label"] = lab
lo_ne = {}
for r in sorted(D.region.unique()):
    res, n, ng = fit(f"leave ~ any_noneu + any_eu + {FULL}", D[D.region != r])
    lo_ne[r] = coef(res, n, ng, "any_noneu")
NE["loro_min"] = max(v["b"] for v in lo_ne.values()); NE["loro_max"] = min(v["b"] for v in lo_ne.values())
NE["loro_n_sig"] = int(sum(v["p"] < 0.05 for v in lo_ne.values()))
NE["loro_weakest"] = max(lo_ne, key=lambda r: lo_ne[r]["b"])
# which partner countries make a seat 'non-EU twinned'
LM = pd.read_csv(f"{SCR}/links_main.csv", keep_default_na=False)
ne = LM[LM.eu.astype(str) != "True"].drop_duplicates(["code", "partner"])
NE["seat_countries"] = ne.groupby("country").code.nunique().sort_values(ascending=False).head(8).to_dict()
NE["pop_noneu"] = float(D[D.any_noneu == 1].pop2011.mean()); NE["pop_none"] = float(D[D.any_noneu == 0].pop2011.mean())
NE["big_noneu"] = float(D[D.any_noneu == 1].max_settle_pop.median()); NE["big_none"] = float(D[D.any_noneu == 0].max_settle_pop.median())
EX["noneu"] = NE

# ---------------------------------------------------------------- exploratory: checks added at independent review
RV = {}


def match_att(Z, cells, rs=None):
    """nearest neighbour (Mahalanobis on standardised MV) within cells, with replacement, regression bias correction"""
    Xs_ = (Z[MV] - Z[MV].mean()) / Z[MV].std()
    VI_ = np.linalg.pinv(np.cov(Xs_.T.values))
    cells = cells if isinstance(cells, list) else [cells]
    key = Z[cells].astype(str).agg("|".join, axis=1)
    t_, c_ = Z[Z.any_eu == 1], Z[Z.any_eu == 0]
    pt_, pc_ = [], []
    for cell, g in t_.groupby(key[t_.index]):
        cc = c_[key[c_.index] == cell]
        if len(cc) == 0:
            continue
        dx = Xs_.loc[g.index].values[:, None, :] - Xs_.loc[cc.index].values[None, :, :]
        d2 = np.einsum("abj,jk,abk->ab", dx, VI_, dx)
        pt_ += list(g.index); pc_ += list(cc.index[d2.argmin(axis=1)])
    bc_ = smf.ols("leave ~ " + " + ".join(MV), c_).fit()
    d_ = Z.loc[pt_, "leave"].values - Z.loc[pc_, "leave"].values
    d_ = d_ - (bc_.predict(Z.loc[pt_]).values - bc_.predict(Z.loc[pc_]).values)
    return float(d_.mean()), len(pt_), len(set(pc_)), d_


# (1) matching that also holds non-EU twinning fixed (exact match on any_noneu within region)
att, npairs, nctl, dd_ = match_att(D, ["region", "any_noneu"])
bt = [dd_[rng.integers(0, len(dd_), len(dd_))].mean() for _ in range(2000)]
RV["match_noneu"] = {"att": att, "lo": float(np.percentile(bt, 2.5)), "hi": float(np.percentile(bt, 97.5)), "n_pairs": npairs, "n_controls_used": nctl}
# (2) the planned matching with a bootstrap that resamples seats within region and re-matches (honest about reuse of controls)
rb_att = []
for _ in range(500):
    idx = np.concatenate([rng.choice(g.index.values, len(g), replace=True) for _, g in D.groupby("region")])
    Zb = D.loc[idx].reset_index(drop=True)
    if (Zb.groupby("region").any_eu.min() == 1).any():
        Zb = Zb[Zb.region.isin(Zb.groupby("region").any_eu.min().loc[lambda s: s == 0].index)]
    rb_att.append(match_att(Zb, "region")[0])
RV["match_rematch"] = {"att": R["match"]["att"], "lo": float(np.percentile(rb_att, 2.5)), "hi": float(np.percentile(rb_att, 97.5)), "draws": 500}
# (3) coarser clusters: seats linked by sharing any council-level twinning host (connected components with the main LAD)
AS = pd.read_csv(f"{DATA}/assign.csv")
par = {c: c for c in D.code}
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for _, g in pd.concat([AS[AS.how == "lad"][["host", "code"]], D[["lad", "code"]].rename(columns={"lad": "host"})]).groupby("host"):
    cs = [c for c in g.code if c in par]
    for c in cs[1:]:
        par[find(c)] = find(cs[0])
D["spill"] = D.code.map(find)
res, n, ng = fit(f"leave ~ any_eu + {FULL}", D, cluster="spill")
RV["spill_main"] = coef(res, n, ng)
res, n, ng = fit(f"leave ~ any_eu + any_noneu + {FULL}", D, cluster="spill")
RV["spill_noneu"] = coef(res, n, ng, "any_noneu")
# (4) where Wikidata coverage is best: seats whose largest documented settlement has 50,000 people or more
BIG = D[D.max_settle_pop >= 50000]
res, n, ng = fit(f"leave ~ any_eu + {FULL}", BIG)
RV["big_main"] = coef(res, n, ng); RV["big_main"]["n_noeu"] = int((BIG.any_eu == 0).sum())
res, n, ng = fit(f"leave ~ any_eu + any_noneu + {FULL}", BIG)
RV["big_noneu"] = coef(res, n, ng, "any_noneu")
EX["review"] = RV
R["exploratory"] = EX

jsave(R, f"{DATA}/results_models.json", indent=1)
jsave(TAB, f"{DATA}/model_tables.json", indent=1)
pr = lambda k, c: print(f"{k:30s} b={c['b']:+.3f} [{c['lo']:+.3f},{c['hi']:+.3f}] p={c['p']:.3f} n={c['n']}")
print(R["n"]); print({k: round(v, 2) if isinstance(v, float) else v for k, v in R["desc"].items()})
for k, c in L.items(): pr(k, c)
print("TOST", R["tost"], "MDE", R["mde80"], "Oster", R["oster"])
for k, c in H2.items(): pr("H2 " + k, c)
for k, c in RB.items(): pr(k, c)
for k, c in CV.items(): pr("conley " + k, c)
print("LORO", R["loro_range"], "RI", R["ri"])
print("match", {k: v for k, v in R["match"].items() if k != "balance"})
print("H3", {k: v for k, v in H3.items() if k not in ("by_decade",)})
for k, c in EX.items():
    if "b" in c: pr("EX " + k, c)
