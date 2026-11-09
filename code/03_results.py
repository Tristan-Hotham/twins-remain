"""Step 3. data/results.json: every number quoted anywhere (page, paper, blog, collage, post, README), from the build
statistics, the model results and the cleaned twinning table. Also data/models.csv (every estimate in one table)."""
import pandas as pd
from common import *

ST = jload(f"{SCR}/build_stats.json")
M = jload(f"{DATA}/results_models.json")
T = pd.read_csv(f"{DATA}/twinnings.csv", keep_default_na=False)
H = pd.read_csv(f"{DATA}/hosts.csv", keep_default_na=False)
D = pd.read_csv(f"{DATA}/constituencies.csv")
R = dict(M)
R["build"] = ST
use = T[T.host_type.isin(["lad", "settlement"]) & (T.country_q != "") & (T.domestic.astype(str) != "True")]
eu = use[use.eu.astype(str) == "True"]
R["pairs"] = {"raw_rows": ST["rows_raw"], "pairs": ST["pairs"], "usable": len(use), "eu": len(eu), "noneu": len(use) - len(eu),
              "eu_pc": len(eu) / len(use) * 100, "hosts_usable": int(use.host.nunique()), "partners_usable": int(use.partner.nunique()),
              "countries": int(use.country.nunique()), "eu_countries": int(eu.country.nunique()),
              "domestic": ST["pairs_domestic"], "no_country": ST["pairs_no_country"],
              "with_coords": int(use.plon.astype(str).ne("").sum()), "partner_coords_rows": ST["partner_coords_rows"]}
bc = use.groupby("country").size().sort_values(ascending=False)
R["by_country"] = [{"country": k, "n": int(v), "eu": k in EU27.values()} for k, v in bc.items()]
R["country"] = {k.split(" ")[-1].lower() if k != "People's Republic of China" else "china": int(v) for k, v in bc.items()}
R["france_germany_pc"] = (R["country"]["france"] + R["country"]["germany"]) / len(use) * 100
ht = H.host_type.value_counts().to_dict()
R["hosts"] = {k: int(ht.get(k, 0)) for k in ("settlement", "lad", "wide", "school", "outside")}
R["hosts"]["all"] = int(len(H))
hp = use.groupby("host_name").partner.nunique().sort_values(ascending=False)
R["top_hosts"] = [{"host": k, "n": int(v), "eu": int(eu[eu.host_name == k].partner.nunique())} for k, v in hp.head(8).items()]
assert R["top_hosts"][0]["host"] == "Coventry"
sh = use[use.host_name == "Sherborne"]
assert sh.country.nunique() == len(sh) == R["top_hosts"][1]["n"] and (sh.eu.astype(str) == "True").all()
R["coventry"] = R["top_hosts"][0]
# seat examples used in text
ex = {}
for nm in ("West Dorset", "Coventry South", "Canterbury", "Boston and Skegness", "Bristol West", "Hartlepool", "Middlesbrough"):
    r = D[D.name == nm].iloc[0]
    ex[nm.replace(" ", "_")] = {"leave": float(r.leave), "n_eu": int(r.n_eu), "n_noneu": int(r.n_noneu), "hosts": str(r.host_names)}
R["ex"] = ex
R["seats_eu_pc"] = M["n"]["any_eu"] / M["n"]["seats"] * 100
R["seats_noneu_pc"] = M["n"]["any_noneu"] / M["n"]["seats"] * 100
cov = {b["band"]: b for b in ST["coverage_by_band"]}
R["coverage"] = {"big_pc": cov["50,000 or more"]["pc"], "big_n": cov["50,000 or more"]["n"], "big_hosts": cov["50,000 or more"]["hosts"],
                 "mid_pc": cov["10,000 to 49,999"]["pc"], "small_pc": cov["2,000 to 9,999"]["pc"], "tiny_pc": cov["under 2,000"]["pc"]}
# headline conveniences (all in points of Leave)
m, h2 = M["main"], M["h2"]
R["head"] = {"b": m["b"], "lo": m["lo"], "hi": m["hi"], "p": m["p"], "n": m["n"],
             "raw": M["ladder"]["M1"]["b"], "raw_lo": M["ladder"]["M1"]["lo"], "raw_hi": M["ladder"]["M1"]["hi"],
             "noneu": h2["noneu_alone"]["b"], "noneu_lo": h2["noneu_alone"]["lo"], "noneu_hi": h2["noneu_alone"]["hi"], "noneu_p": h2["noneu_alone"]["p"],
             "joint_eu": h2["joint_eu"]["b"], "joint_noneu": h2["joint_noneu"]["b"],
             "diff": h2["diff"]["b"], "diff_lo": h2["diff"]["lo"], "diff_hi": h2["diff"]["hi"], "diff_p": h2["diff"]["p"]}
rb = M["robust"]
R["region_remain"] = {r: {"remain": int((g.leave < 50).sum()), "n": int(len(g))} for r, g in D.groupby("region")}
R["tost_sd"] = abs(m["lo"]) / M["desc"]["leave_sd"] * 100
kn = D[D.leave_known]
R["known_density"] = {"known": float(kn.density.mean()), "other": float(D[~D.leave_known].density.mean())}
assert R["known_density"]["known"] > 2 * R["known_density"]["other"]
R["robust_summary"] = {"n": len(rb) - 1, "n_sig": int(sum(v["p"] < 0.05 for k, v in rb.items() if k != "main")),
                       "min": min(v["b"] for k, v in rb.items() if k != "main"), "max": max(v["b"] for k, v in rb.items() if k != "main")}
# claims made in words, checked here
assert m["lo"] < 0 < m["hi"] and abs(m["b"]) < 0.5
assert R["robust_summary"]["n_sig"] == 2 and rb["l_neu"]["p"] < 0.05 and rb["l_per100k"]["p"] < 0.05
# review checks (exploratory) as described in words
RV = M["exploratory"]["review"]
assert RV["match_noneu"]["lo"] < 0 < RV["match_noneu"]["hi"] and RV["match_rematch"]["lo"] < 0 < RV["match_rematch"]["hi"]
assert RV["spill_main"]["lo"] < 0 < RV["spill_main"]["hi"] and RV["spill_noneu"]["p"] < 0.05
assert RV["big_main"]["lo"] < 0 < RV["big_main"]["hi"] and RV["big_noneu"]["p"] > 0.05
assert M["tost"]["p"] > 0.05 and not M["tost"]["equivalent"]
assert M["h2"]["count_eu"]["p"] > 0.05 and M["match"]["hi"] < 0
assert h2["noneu_alone"]["hi"] < 0 and h2["diff"]["p"] > 0.05
assert M["ladder"]["M1"]["b"] > 0
assert M["exploratory"]["noneu"]["ladfe"]["p"] > 0.05 and M["exploratory"]["noneu"]["loro_n_sig"] == 11
jsave(R, f"{DATA}/results.json", indent=1)

rows = []
def add(group, key, c, label=None):
    if isinstance(c, dict) and "b" in c:
        rows.append({"group": group, "key": key, "label": label or c.get("label", key), "b": c["b"], "lo": c["lo"], "hi": c["hi"], "p": c["p"], "n": c["n"]})
for k, c in M["ladder"].items(): add("ladder", k, c)
for k, c in M["h2"].items(): add("h2", k, c)
for k, c in M["robust"].items(): add("robust", k, c)
for k, c in M["conley"].items(): add("conley", k, c)
for k, c in M["loro"].items(): add("loro", k, c, f"without {k}")
add("h3", "pre73", M["h3"]["model"])
for k, c in M["exploratory"].items(): add("exploratory", k, c)
for k, c in M["exploratory"]["noneu"].items(): add("exploratory_noneu", k, c)
pd.DataFrame(rows).to_csv(f"{DATA}/models.csv", index=False, float_format="%.5g")
print(json.dumps({k: R[k] for k in ("pairs", "hosts", "head", "robust_summary", "coverage", "coventry")}, indent=1, default=str))
print(R["by_country"][:10]); print(R["ex"])
