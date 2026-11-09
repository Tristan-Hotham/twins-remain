"""Step 1. Clean the Wikidata twinning statements and build the constituency dataset.

- one row per host and partner (partners with several historical countries collapsed to their present-day state)
- hosts classified by the rules fixed in NOTES.md section 0: local authority, settlement, wide area, not municipal
- local-authority twinnings assigned to every 2010 seat with at least a third of its area in that 2013 LAD (and the seat
  holding the point); settlement twinnings to the seat holding the point (points up to 2 km offshore to the nearest seat)
- seat exposure counts in several variants, 2011 census, Leave estimates, settlement documentation controls

Writes data/twinnings.csv, data/hosts.csv, data/constituencies.csv, data/assign.csv and SCR/seats_27700.gpkg.
"""
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from common import *

warnings.filterwarnings("ignore")
st = {}

# ---------------------------------------------------------------- twinning statements
raw = pd.read_csv(TWINS, sep="\t", dtype=str, keep_default_na=False, quoting=3)
raw.columns = [c.lstrip("?") for c in raw.columns]
st["rows_raw"] = len(raw)
T = pd.DataFrame({"host": raw.town.map(qid), "host_name": raw.townLabel.map(lit), "partner": raw.partner.map(qid),
                  "partner_name": raw.partnerLabel.map(lit), "cq": raw.pcountry.map(qid),
                  "start": raw.start.map(lit).str[:10], "end": raw.end.map(lit).str[:10]})
xy = raw.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
T["lon"], T["lat"] = xy[0], xy[1]

lab = {}
with open(LABELS, encoding="utf-8") as f:
    next(f)
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2 and qid(p[0]):
            lab[qid(p[0])] = lit(p[1])
lab.update(COUNTRY_EXTRA)
OUTSIDE_EU_TERR = {"Q223", "Q4628", "Q9648"}            # Greenland, Faroe Islands, Falklands: preferred over Denmark/UK
RECOGNISED = [("Q212", "Q159"), ("Q229", "Q23681"), ("Q1045", "Q34754")]  # Ukraine over Russia (Luhansk, Yalta), Cyprus over
                                                        # Northern Cyprus (Morphou), Somalia over Somaliland (Borama); fixed at review


def present_state(qs):
    qs = [q for q in dict.fromkeys(qs) if q]
    mod = [q for q in qs if q not in HISTORICAL]
    if any(q in OUTSIDE_EU_TERR for q in mod):
        return [q for q in mod if q in OUTSIDE_EU_TERR][0]
    for pref, other in RECOGNISED:                     # disputed places: the internationally recognised state
        if pref in mod and other in mod:
            return pref
    if len(mod) >= 1:
        return mod[0]
    return qs[0] if qs else ""


pc = T.groupby("partner").cq.apply(lambda s: present_state(list(s)))
multi = T.groupby("partner").cq.nunique()
st["partners_multi_country"] = int((multi > 1).sum())
pc_multi_mod = T[~T.cq.isin(HISTORICAL)].groupby("partner").cq.nunique()
st["partners_multi_present_state"] = int((pc_multi_mod > 1).sum())
T["country_q"] = T.partner.map(pc)
T["start"] = T.groupby(["host", "partner"]).start.transform(lambda s: s[s != ""].min() if (s != "").any() else "")
T["end"] = T.groupby(["host", "partner"]).end.transform(lambda s: s[s != ""].min() if (s != "").any() else "")
T = T.drop(columns="cq").drop_duplicates(["host", "partner"]).reset_index(drop=True)
T["country"] = T.country_q.map(lambda q: lab.get(q, q))
T.loc[T.country_q == "", "country"] = "unknown"
T["eu"] = T.country_q.isin(EU27)
T["joined"] = T.country_q.map(JOINED)
T["domestic"] = T.country_q == "Q145"
T["start_year"] = pd.to_numeric(T.start.str[:4], errors="coerce")
# partner points (Wikidata P625), for drawing town-to-town arcs only; not used in any model
PC = pd.read_csv(PCOORD, sep="\t", dtype=str)
PC.columns = [c.lstrip("?") for c in PC.columns]
PC["partner"] = PC.x.map(qid)
pxy = PC.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
PC["plon"], PC["plat"] = pxy[0], pxy[1]
PC = PC.groupby("partner")[["plon", "plat"]].mean().round(4).reset_index()
T = T.merge(PC, on="partner", how="left")
st["partner_coords_rows"] = int(len(pxy))
T["end_year"] = pd.to_numeric(T.end.str[:4], errors="coerce")
st["pairs"] = len(T)
st["pairs_no_country"] = int((T.country_q == "").sum())
st["pairs_domestic"] = int(T.domestic.sum())
assert all(lab.get(q) for q in T.country_q.unique() if q), [q for q in T.country_q.unique() if q and not lab.get(q)]

# ---------------------------------------------------------------- boundaries
seats = gpd.read_file(f"{RAW}/wpc2010_gb.json")[["PCON13CD", "PCON13NM", "geometry"]]
seats = seats[seats.PCON13CD.str[0].isin(list("EWS"))].rename(columns={"PCON13CD": "code", "PCON13NM": "seat"}).to_crs(27700)
seats["geometry"] = seats.geometry.buffer(0)
seats["area_km2"] = seats.area / 1e6
rp = seats.representative_point()
seats["cx"], seats["cy"] = rp.x, rp.y
lad = gpd.read_file(f"{RAW}/lad_gb.json")[["LAD13CD", "LAD13NM", "geometry"]]
lad = lad[lad.LAD13CD.str[0].isin(list("EWS"))].to_crs(27700)
lad["geometry"] = lad.geometry.simplify(20).buffer(0)
sim = seats[["code", "geometry"]].copy()
sim["geometry"] = sim.geometry.simplify(20).buffer(0)
ov = gpd.overlay(sim, lad, how="intersection", keep_geom_type=True)
ov["a"] = ov.area
ov["share"] = ov.a / ov.code.map(sim.set_index("code").area)
best = ov.sort_values("a", ascending=False).drop_duplicates("code").set_index("code")
seats["lad"] = seats.code.map(best.LAD13CD)
seats["lad_name"] = seats.code.map(best.LAD13NM)
seats.to_file(f"{SCR}/seats_27700.gpkg", driver="GPKG")
st["n_seats_geo"] = len(seats)


def place(lon, lat):
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4326).to_crs(27700)
    j = gpd.sjoin(g, seats[["code", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    miss = j.code.isna()
    if miss.any():
        nn = gpd.sjoin_nearest(g[miss], seats[["code", "geometry"]], how="left", max_distance=2000, distance_col="d")
        nn = nn[~nn.index.duplicated()]
        j.loc[miss, "code"] = nn.code
    return j.code.values, g


# ---------------------------------------------------------------- hosts and their types
H = T.groupby("host").agg(host_name=("host_name", "first"), lon=("lon", "first"), lat=("lat", "first"),
                          partners=("partner", "nunique")).reset_index()
s8 = pd.read_csv(SETTLE, sep="\t", dtype=str, quoting=3)
s8.columns = [c.lstrip("?") for c in s8.columns]
s8["q"] = s8.p.map(qid)
s8["typel"] = s8.typel.map(lit)
types = s8.groupby("q").typel.apply(lambda s: "; ".join(sorted(set(s.dropna()))))
H["wd_types"] = H.host.map(types).fillna("")
H["code_point"], hg = place(H.lon.values, H.lat.values)

WIDE = {"Q84": "Greater London", "Q23077": "county", "Q23092": "county", "Q23098": "county", "Q23099": "metropolitan county",
        "Q23109": "county", "Q23115": "county", "Q23287": "county", "Q24550": "former county", "Q1542364": "former region",
        "Q547052": "historic county"}
OUTSIDE = {"Q25230": "Guernsey", "Q5785": "Cayman Islands"}
lad_by_norm = {}
for _, r in lad.iterrows():
    lad_by_norm.setdefault(norm_lad(r.LAD13NM), []).append(r.LAD13CD)
lad_geom = lad.set_index("LAD13CD").geometry


OV = pd.read_csv(os.path.join(ROOT, "code", "overrides.csv")).set_index("host_name")
lad_by_name = dict(zip(lad.LAD13NM, lad.LAD13CD))


def classify(i, r):
    if r.host_name in OV.index:
        o = OV.loc[r.host_name]
        return (o.action, lad_by_name[o.value]) if o.action == "lad" else (o.action, "")
    if r.host in OUTSIDE:
        return "outside", ""
    if r.host in WIDE:
        return "wide", ""
    if re.search(r"School|Academy", r.host_name):
        return "school", ""
    cands = lad_by_norm.get(norm_lad(r.host_name), [])
    for c in cands:
        if lad_geom[c].distance(hg.geometry.iloc[i]) <= 5000:
            return "lad", c
    if pd.isna(r.code_point):
        return "outside", ""
    return "settlement", ""


cl = [classify(i, r) for i, r in H.iterrows()]
H["host_type"] = [c[0] for c in cl]
H["lad"] = [c[1] for c in cl]
H["lad_name"] = H.lad.map(lad.set_index("LAD13CD").LAD13NM)
st["hosts"] = len(H)
st["host_types"] = H.host_type.value_counts().to_dict()
st["host_types_pairs"] = H.groupby("host_type").partners.sum().to_dict()

# ---------------------------------------------------------------- assignment of hosts to seats
A = []
for _, r in H.iterrows():
    if r.host_type == "lad":
        cs = set(ov[(ov.LAD13CD == r.lad) & (ov.share >= 1 / 3)].code)
        if isinstance(r.code_point, str):
            cs.add(r.code_point)
        A += [(r.host, c, "lad") for c in sorted(cs)]
    if r.host_type in ("settlement", "lad", "wide") and isinstance(r.code_point, str):
        A.append((r.host, r.code_point, "point"))
A = pd.DataFrame(A, columns=["host", "code", "how"])
A.to_csv(f"{DATA}/assign.csv", index=False)
H["seats_assigned"] = H.host.map(A[A.how == "lad"].groupby("host").code.nunique()).fillna(0).astype(int)

# ---------------------------------------------------------------- seat exposure variants
TP = T[~T.domestic & (T.country_q != "")].merge(H[["host", "host_type"]], on="host")
st["pairs_usable"] = int((TP.host_type.isin(["lad", "settlement"])).sum())
st["pairs_usable_eu"] = int((TP.host_type.isin(["lad", "settlement"]) & TP.eu).sum())


def links(mask_types, how):
    a = A[A.how.isin(how)]
    x = TP[TP.host_type.isin(mask_types)].merge(a, on="host")
    if "point" in how and "lad" in how:      # an LAD host's point seat is already among its lad seats
        x = x.drop_duplicates(["host", "partner", "code"])
    return x


MAINL = links(["lad", "settlement"], ["lad"]).pipe(lambda x: pd.concat([x, links(["settlement"], ["point"])]))
MAINL = MAINL.drop_duplicates(["code", "partner"])
POINTL = links(["lad", "settlement"], ["point"]).drop_duplicates(["code", "partner"])
WIDEL = pd.concat([MAINL, links(["wide"], ["point"])]).drop_duplicates(["code", "partner"])
SETL = links(["settlement"], ["point"]).drop_duplicates(["code", "partner"])
MAINL.to_csv(f"{SCR}/links_main.csv", index=False)

S = pd.DataFrame({"code": seats.code})
cnt = lambda L, m=None: S.code.map((L if m is None else L[m]).groupby("code").partner.nunique()).fillna(0).astype(int)
S["n_eu"] = cnt(MAINL, MAINL.eu)
S["n_noneu"] = cnt(MAINL, ~MAINL.eu)
S["n_eu_point"] = cnt(POINTL, POINTL.eu)
S["n_noneu_point"] = cnt(POINTL, ~POINTL.eu)
S["n_eu_wide"] = cnt(WIDEL, WIDEL.eu)
S["n_eu_settle"] = cnt(SETL, SETL.eu)
pre_ref = MAINL.start.eq("") | (MAINL.start < "2016-06-23")
S["n_eu_preref"] = cnt(MAINL, MAINL.eu & pre_ref)
active = MAINL.end.eq("") | (MAINL.end >= "2016-06-23")
S["n_eu_active"] = cnt(MAINL, MAINL.eu & pre_ref & active)
S["n_noneu_active"] = cnt(MAINL, ~MAINL.eu & pre_ref & active)
S["n_eu15"] =cnt(MAINL, MAINL.country_q.isin(EU15))
S["n_eu_new"] = cnt(MAINL, MAINL.eu & ~MAINL.country_q.isin(EU15))
S["n_frde"] = cnt(MAINL, MAINL.country_q.isin(["Q142", "Q183"]))
S["n_eu_dated"] = cnt(MAINL, MAINL.eu & MAINL.start_year.notna())
S["n_eu_pre73"] = cnt(MAINL, MAINL.eu & (MAINL.start_year < 1973))
S["n_eu_post73"] = cnt(MAINL, MAINL.eu & (MAINL.start_year >= 1973))
S["first_eu_year"] = S.code.map(MAINL[MAINL.eu].groupby("code").start_year.min())
S["n_hosts"] = S.code.map(MAINL.groupby("code").host.nunique()).fillna(0).astype(int)
S["host_names"] = S.code.map(MAINL.groupby("code").host_name.apply(lambda s: "; ".join(sorted(set(s)))))
top = MAINL.groupby(["code", "country"]).partner.nunique().reset_index().sort_values(["code", "partner"], ascending=[True, False])
S["countries"] = S.code.map(top.groupby("code").apply(lambda g: "; ".join(f"{c} {n}" for c, n in zip(g.country, g.partner))))

# ---------------------------------------------------------------- settlements (documentation and size controls)
rows = []
with gzip.open(f"{RAW}/uk_settlements_enwiki.tsv.gz", "rt", encoding="utf-8") as f:
    head = [h.lstrip("?") for h in f.readline().rstrip("\n").split("\t")]
    for line in f:
        p = line.rstrip("\n").split("\t") + [""] * 4
        rows.append(dict(zip(head, p)))
E = pd.DataFrame(rows)
E["q"] = E.p.map(qid)
E["pop"] = pd.to_numeric(E.pp.map(lit), errors="coerce")
xy = E.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
E["lon"], E["lat"] = xy[0], xy[1]
E = E.dropna(subset=["lon"]).groupby("q").agg(title=("title", "first"), pop=("pop", "max"), lon=("lon", "first"), lat=("lat", "first")).reset_index()
E["code"], _ = place(E.lon.values, E.lat.values)
st["settlements_enwiki"] = len(E)
st["settlements_in_gb_seat"] = int(E.code.notna().sum())
st["settlements_with_pop"] = int(E["pop"].notna().sum())
E = E[E.code.notna()]
S["n_settle"] = S.code.map(E.groupby("code").size()).fillna(0).astype(int)
S["max_settle_pop"] = S.code.map(E.groupby("code")["pop"].max()).fillna(0)
# coverage: share of settlements (by population band) that are twinning hosts themselves
E["is_host"] = E.q.isin(set(H.host))
E["band"] = pd.cut(E["pop"], [0, 2000, 10000, 50000, 1e9], labels=["under 2,000", "2,000 to 9,999", "10,000 to 49,999", "50,000 or more"], right=False)
cov = E.groupby("band").agg(n=("q", "size"), hosts=("is_host", "sum")).reset_index()
cov["pc"] = cov.hosts / cov.n * 100
st["coverage_by_band"] = cov.to_dict(orient="records")
st["coverage_no_pop"] = {"n": int(E["pop"].isna().sum()), "hosts": int(E[E["pop"].isna()].is_host.sum())}

# ---------------------------------------------------------------- census and Leave
cen = pd.read_csv(f"{RAW}/census_11.csv")
lv = pd.read_csv(f"{RAW}/leave_votes_west.csv")
c = cen.rename(columns={"ons_const_id": "code"})
D = pd.DataFrame({"code": c.code, "name": c.constituency_name, "country": c.country, "region": c.region,
                  "ctype": c.constituency_type, "pop2011": c.population, "density": c.population_density})
D["pct_65plus"] = c[["age_65_to_74", "age_75_to_84", "age_85_to_89", "age_90_plus"]].sum(axis=1)
D["pct_degree"] = c.qual_level_4
D["pct_noqual"] = c.qual_none
nssec = c[["nssechigher_manager", "nssechigher_professional", "nsseclower_manager", "nssecintermediate", "nssecsmall_employer",
           "nsseclower_supervisor", "nssecsemi_routine", "nssecroutine", "nssecnever_worked", "nsseclongterm_unemployed"]]
D["pct_routine"] = (c.nssecsemi_routine + c.nssecroutine) / nssec.sum(axis=1) * 100
D["pct_whitebrit"] = c.ethnicity_white_british
D["pct_foreignborn"] = 100 - c.born_uk
D["pct_eu_born"] = c.born_ireland + c.born_other_eu
D = D.merge(lv[["ons_const_id", "figure_to_use", "known_leave_vote", "ch_leave_vote"]].rename(columns={"ons_const_id": "code"}), on="code", how="left")
D["leave"] = D.figure_to_use * 100
D["leave_known"] = D.known_leave_vote.eq("Yes")
D["leave_ch"] = D.ch_leave_vote * 100
D = D.drop(columns=["figure_to_use", "known_leave_vote", "ch_leave_vote"])
G = seats[["code", "area_km2", "lad", "lad_name", "cx", "cy"]]
D = D.merge(G, on="code", how="inner").merge(S, on="code", how="left")
assert len(D) == 632 and D.leave.notna().all()
D["any_eu"] = (D.n_eu > 0).astype(int)
D["any_noneu"] = (D.n_noneu > 0).astype(int)
D["eu_per100k"] = D.n_eu / D.pop2011 * 1e5
D.to_csv(f"{DATA}/constituencies.csv", index=False, float_format="%.6g")
st["n_seats"] = len(D)

# ---------------------------------------------------------------- tidy twinning and host tables for release
H.drop(columns=["code_point"]).assign(code_point=H.code_point).to_csv(f"{DATA}/hosts.csv", index=False)
out = T.merge(H[["host", "host_type", "lad_name"]], on="host", how="left")
out["seats_main"] = out.host.map(pd.concat([A[A.how == "lad"], A[(A.how == "point") & A.host.isin(H[H.host_type == "settlement"].host)]])
                                 .groupby("host").code.apply(lambda s: ";".join(sorted(set(s)))))
out = out[["host", "host_name", "host_type", "lad_name", "lon", "lat", "partner", "partner_name", "country_q", "country", "eu",
           "joined", "domestic", "start", "end", "seats_main", "plon", "plat"]]
out.to_csv(f"{DATA}/twinnings.csv", index=False)
jsave(st, f"{SCR}/build_stats.json", indent=1)
print(json.dumps(nonan(st), indent=1, default=str)[:3000])
print(D[["n_eu", "n_noneu", "any_eu", "any_noneu", "n_settle", "max_settle_pop"]].describe().T)
