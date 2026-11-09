"""Step 4. Figures: paper (release/paper/f_*.png, 300 dpi), blog (release/blog/b_*.png, 1800 px wide) and page (img/*.jpg).
All numbers drawn from data/results.json and the data tables."""
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PatchCollection
from PIL import Image
from common import *

warnings.filterwarnings("ignore")
for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
import dataclasses
fm.fontManager.ttflist = [dataclasses.replace(e, weight=600) if e.fname.endswith("SourceSerif4-Semibold.ttf") else e for e in fm.fontManager.ttflist]
SERIF, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": "#8A8170", "axes.labelcolor": "#2A2620", "xtick.color": "#5E574B",
                     "ytick.color": "#5E574B", "axes.facecolor": "none", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False})
PAPER, INKC, MUT, GRID = "#FBF8F1", "#2A2620", "#6E665A", "#E6DFD0"
EUC, NEC, MIX = "#1F4E9A", "#C2332B", "#7A4E8E"
R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/constituencies.csv")
H = pd.read_csv(f"{DATA}/hosts.csv")
T = pd.read_csv(f"{DATA}/twinnings.csv", keep_default_na=False)
seats = gpd.read_file(f"{SCR}/seats_27700.gpkg")
seats["geometry"] = seats.geometry.simplify(400)
seats = seats.merge(D[["code", "leave", "n_eu", "n_noneu"]], on="code")
use = T[T.host_type.isin(["lad", "settlement"]) & (T.country_q != "") & (T.domestic.astype(str) != "True")]
hc = use.groupby("host").agg(eu=("eu", lambda s: int((s.astype(str) == "True").sum())), n=("partner", "nunique")).reset_index()
HP = H.merge(hc, on="host")
HP["kind"] = np.where(HP.eu == HP.n, "eu", np.where(HP.eu == 0, "non", "mix"))
g = gpd.GeoSeries(gpd.points_from_xy(HP.lon, HP.lat), crs=4326).to_crs(27700)
HP["x"], HP["y"] = g.x, g.y
HP = HP[(HP.y < 1.0e6) & (HP.x > 0)]


def save(fig, name, blog=True, page=None):
    fig.savefig(f"{FIG}/f_{name}.png", dpi=300, facecolor=PAPER, bbox_inches="tight", pad_inches=0.2)
    if blog:
        fig.savefig(f"{SCR}/b.png", dpi=300, facecolor=PAPER, bbox_inches="tight", pad_inches=0.3)
        im = Image.open(f"{SCR}/b.png").convert("RGB")
        im.resize((1800, round(im.height * 1800 / im.width)), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
        if page:
            im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS).save(f"{IMG}/{page}.jpg", quality=84)
    plt.close(fig)


def leave_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("lv", ["#FFFFFF", "#ECE7DC", "#CFC6B4", "#A99F8B", "#7F7563"])


# ---------------------------------------------------------------- map
fig = plt.figure(figsize=(11, 10.5), facecolor=PAPER)
ax = fig.add_axes([0.0, 0.0, 0.66, 1.0])
seats.plot(ax=ax, column="leave", cmap=leave_cmap(), vmin=20, vmax=76, edgecolor="#FFFFFF", linewidth=0.15)
for kind, col, z in (("eu", EUC, 3), ("mix", MIX, 4), ("non", NEC, 5)):
    s = HP[HP.kind == kind]
    ax.scatter(s.x, s.y, s=6 + 9 * np.sqrt(s.n), c=col, edgecolors="white", linewidths=0.5, zorder=z, alpha=0.9)
ax.set_xlim(-10000, 670000); ax.set_ylim(0, 1000000); ax.set_aspect("equal"); ax.axis("off")
ax2 = fig.add_axes([0.68, 0.40, 0.29, 0.50])
bc = R["by_country"][:14][::-1]
ax2.barh(range(len(bc)), [b["n"] for b in bc], color=[EUC if b["eu"] else NEC for b in bc], height=0.7)
ax2.set_yticks(range(len(bc))); ax2.set_yticklabels([b["country"].replace("People's Republic of China", "China") for b in bc], fontsize=10.5)
for i, b in enumerate(bc):
    ax2.text(b["n"] + 6, i, f"{b['n']:,}", va="center", fontsize=9.5, family=MONO, color=MUT)
ax2.set_xlim(0, 560); ax2.set_xticks([]); ax2.spines["bottom"].set_visible(False)
ax2.set_title("Twinnings by partner country", fontsize=12.5, loc="left", weight=600)
lx = fig.add_axes([0.68, 0.05, 0.29, 0.3]); lx.axis("off")
for i, (lab, col) in enumerate((("Partners all in other EU states", EUC), ("Partners in and outside the EU", MIX), ("Partners all outside the EU", NEC))):
    lx.scatter([0.04], [0.92 - i * 0.12], s=70, c=col, edgecolors="white"); lx.text(0.1, 0.92 - i * 0.12, lab, va="center", fontsize=10.5)
lx.text(0.0, 0.52, "Dot size: number of partners.\nShading: estimated Leave share\nby 2010 constituency (light 20%,\ndark 76%).", fontsize=10, color=MUT, va="top")
lx.text(0.0, 0.08, f"{R['pairs']['usable']:,} twinnings of {R['pairs']['hosts_usable']} British\nplaces (Wikidata), Great Britain.", fontsize=10, color=MUT, va="bottom")
lx.set_xlim(0, 1); lx.set_ylim(0, 1)
save(fig, "map", page="map")

# ---------------------------------------------------------------- forest plot
rows = [("Raw difference", R["ladder"]["M1"], "#9A9283"), ("Same region", R["ladder"]["M2"], "#9A9283"),
        ("+ 2011 census", R["ladder"]["M3"], "#9A9283"), ("Main model: + size and documentation", R["main"], EUC),
        ("Non-EU twinning (placebo)", R["h2"]["noneu_alone"], NEC), ("EU, with non-EU in the model", R["h2"]["joint_eu"], EUC),
        ("Matched seats (interval too narrow, see text)", {"b": R["match"]["att"], "lo": R["match"]["lo"], "hi": R["match"]["hi"]}, "#9A9283")]
rb = R["robust"]
for k in ("point", "eu15", "frde", "l_neu", "known", "england", "ladfe"):
    rows.append((rb[k]["label"].replace("log(1 + EU partners)", "log(1 + EU partners), per unit").replace("Seats with a counted (ward-based) Leave figure", "Counted Leave results only")
                 .replace("Point assignment only (no spreading over the council area)", "Town points only, no council spreading")
                 .replace("Local authority fixed effects (within-council)", "Within the same council area"), rb[k], "#6E8FBF"))
fig, ax = plt.subplots(figsize=(10, 7.4), facecolor=PAPER)
for i, (lab, c, col) in enumerate(rows):
    y = len(rows) - i
    ax.plot([c["lo"], c["hi"]], [y, y], color=col, lw=2.2, solid_capstyle="round")
    ax.scatter([c["b"]], [y], s=60 if col in (EUC, NEC) else 40, color=col, zorder=3, edgecolors="white")
    ax.text(-6.4, y, lab, va="center", ha="left", fontsize=10.8, color=INKC)
ax.axvline(0, color=INKC, lw=0.8)
for y in (len(rows) - 3.5, len(rows) - 6.5):
    ax.axhline(y, color=GRID, lw=0.8)
ax.set_xlim(-6.5, 5.0); ax.set_ylim(0.3, len(rows) + 0.8); ax.set_yticks([])
ax.set_xticks([-3, -2, -1, 0, 1, 2, 3, 4]); ax.spines["left"].set_visible(False)
ax.set_xlabel("Difference in Leave share, percentage points (95% interval)\nleft of zero: more Remain", fontsize=11)
save(fig, "forest", page="forest")

# ---------------------------------------------------------------- Leave by number of EU partners (raw), with degree share
bn = R["by_neu"]
fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=PAPER)
x = np.arange(len(bn))
ax.bar(x - 0.2, [b["leave"] for b in bn], 0.38, color="#7F7563", label="Leave share (%)")
ax.bar(x + 0.2, [b["degree"] for b in bn], 0.38, color="#C9BFA9", label="Degree holders, 2011 (%)")
for i, b in enumerate(bn):
    ax.text(i - 0.2, b["leave"] + 1, f"{b['leave']:.1f}", ha="center", fontsize=10, family=MONO)
    ax.text(i + 0.2, b["degree"] + 1, f"{b['degree']:.1f}", ha="center", fontsize=10, family=MONO)
    ax.text(i, -6, f"{b['n']} seats", ha="center", fontsize=9.5, color=MUT, family=MONO)
ax.set_xticks(x); ax.set_xticklabels([f"{b['bin']} EU partners" for b in bn])
ax.set_ylim(-9, 66); ax.axhline(0, color=INKC, lw=0.6); ax.set_yticks([0, 20, 40, 60])
ax.legend(frameon=False, loc="upper right", fontsize=10.5)
save(fig, "bins", page="bins")

# ---------------------------------------------------------------- documentation: share of settlements that are hosts, by size
cb = R["build"]["coverage_by_band"]
fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=PAPER)
ax.bar(range(len(cb)), [b["pc"] for b in cb], color=EUC, width=0.6)
for i, b in enumerate(cb):
    ax.text(i, b["pc"] + 1.5, f"{b['pc']:.1f}%", ha="center", fontsize=11, family=MONO)
    ax.text(i, -7, f"{b['hosts']} of {b['n']:,}", ha="center", fontsize=9.5, color=MUT, family=MONO)
ax.set_xticks(range(len(cb))); ax.set_xticklabels([f"population {b['band']}" for b in cb], fontsize=10.5)
ax.set_ylim(-10, 68); ax.axhline(0, color=INKC, lw=0.6); ax.set_yticks([0, 20, 40, 60]); ax.set_ylabel("% of settlements with a recorded twinning")
save(fig, "coverage", page="coverage")

# ---------------------------------------------------------------- timing: dated EU twinnings by decade
bd = R["h3"]["by_decade"]
fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=PAPER)
ax.bar([b["decade"] + 5 for b in bd], [b["n"] for b in bd], width=8.4, color=[EUC if b["decade"] >= 1970 else "#6E8FBF" for b in bd])
ax.axvline(1973, color=NEC, lw=1.4, ls=(0, (3, 2)))
ax.text(1974, max(b["n"] for b in bd) * 0.95, "UK joins, 1973", color=NEC, fontsize=10.5)
ax.set_xlabel("Decade the twinning began (dated twinnings only)"); ax.set_ylabel("EU twinnings")
ax.set_xlim(1935, 2030)
save(fig, "timing", page="timing")

# ---------------------------------------------------------------- page data
seats4 = seats.to_crs(4326)
seats4["geometry"] = seats4.geometry.simplify(0.002)
gj = json.loads(seats4[["code", "seat", "leave", "n_eu", "n_noneu", "geometry"]].to_json())
for f in gj["features"]:
    p = f["properties"]; p["leave"] = round(p["leave"], 1)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 4), round(c[1], 4)]
    f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
with open(f"{DATA}/seats.geojson", "w") as fh:
    json.dump(gj, fh, separators=(",", ":"))
Dd = D.set_index("code")
for c in gj["features"]:
    pass
hosts_out = []
for _, r in HP.iterrows():
    pr = use[use.host == r.host].sort_values(["eu", "country", "partner_name"], ascending=[False, True, True])
    hosts_out.append({"q": r.host, "n": r.host_name, "lon": round(r.lon, 4), "lat": round(r.lat, 4), "t": r.host_type,
                      "lad": r.lad_name if isinstance(r.lad_name, str) else "", "k": r.kind,
                      "p": [[x.partner_name, x.country, 1 if str(x.eu) == "True" else 0, x.start[:4], x.end[:4], x.partner]
                            + ([float(x.plon), float(x.plat)] if str(x.plon) not in ("", "nan") else []) for x in pr.itertuples()]})
nolink = sum(len(p) < 8 for h in hosts_out for p in h["p"])
assert nolink == R["pairs"]["usable"] - R["pairs"]["with_coords"], nolink
jsave({"hosts": hosts_out}, f"{DATA}/hosts.json")
print("figures done; page data", len(hosts_out), "hosts; twinnings without a partner point:", nolink)
