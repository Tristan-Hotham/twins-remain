"""Reddit collage (reddit/twins_remain_collage.png, 2700 x 2025) and social card (header.png, 1200 x 630).
The collage map draws each twinning as an arc from the British place to its partner's own Wikidata point (P625).
Every number comes from data/results.json. Run after code/04_figures.py (needs SCR/seats_27700.gpkg)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from common import *

for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "FrauncesVar.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
import dataclasses
fm.fontManager.ttflist = [dataclasses.replace(e, weight=600) if e.fname.endswith("SourceSerif4-Semibold.ttf") else e for e in fm.fontManager.ttflist]
SERIF, MONO, DISP = "Source Serif 4", "IBM Plex Mono", "Fraunces"
plt.rcParams.update({"font.family": SERIF, "axes.unicode_minus": False})
PAPER, INKC, MUT = "#FBF8F1", "#2A2620", "#6E665A"
EUC, NEC, MIX = "#1F4E9A", "#C2332B", "#7A4E8E"
R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/constituencies.csv")
H = jload(f"{DATA}/hosts.json")["hosts"]
seats = gpd.read_file(f"{SCR}/seats_27700.gpkg")
seats["geometry"] = seats.geometry.simplify(300)
seats = seats.merge(D[["code", "leave"]], on="code")
HP = pd.DataFrame([{"lon": h["lon"], "lat": h["lat"], "k": h["k"], "n": len(h["p"])} for h in H])
g = gpd.GeoSeries(gpd.points_from_xy(HP.lon, HP.lat), crs=4326).to_crs(27700)
HP["x"], HP["y"] = g.x, g.y
CM = LinearSegmentedColormap.from_list("lv", ["#FFFFFF", "#ECE7DC", "#CFC6B4", "#A99F8B", "#7F7563"])


def gbmap(ax, scale=1.0):
    seats.plot(ax=ax, column="leave", cmap=CM, vmin=20, vmax=76, edgecolor="#FFFFFF", linewidth=0.2 * scale)
    for k, c, z in (("eu", EUC, 3), ("mix", MIX, 4), ("non", NEC, 5)):
        s = HP[HP.k == k]
        ax.scatter(s.x, s.y, s=(8 + 12 * np.sqrt(s.n)) * scale, c=c, edgecolors="white", linewidths=0.6 * scale, zorder=z, alpha=0.92)
    ax.set_xlim(0, 660000); ax.set_ylim(0, 1000000); ax.set_aspect("equal"); ax.axis("off")


f1 = lambda v: fmt(v, "f1")
# ---------------------------------------------------------------- Europe map with true town-to-town arcs (partner points: Wikidata P625)
EPSG = 3035
land = gpd.read_file(f"{GEO}/ne_50m_land.geojson").to_crs(EPSG)
seatsE = seats.to_crs(EPSG)
LK = pd.DataFrame([(h["lon"], h["lat"], p[6], p[7], p[2]) for h in H for p in h["p"] if len(p) > 7], columns=["lon", "lat", "plon", "plat", "eu"])
assert len(LK) == R["pairs"]["with_coords"]
from pyproj import Transformer
TR = Transformer.from_crs(4326, EPSG, always_xy=True)
ax0, ay0 = TR.transform(LK.lon.values, LK.lat.values); bx0, by0 = TR.transform(LK.plon.values, LK.plat.values)


def arcs(sel, n=40):
    out = []
    for a1, a2, b1, b2 in zip(ax0[sel], ay0[sel], bx0[sel], by0[sel]):
        a, b = np.array([a1, a2]), np.array([b1, b2]); d = b - a; c = (a + b) / 2 + np.array([-d[1], d[0]]) * 0.18
        t = np.linspace(0, 1, n)[:, None]
        out.append((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b)
    return out


from matplotlib.collections import LineCollection
XL, YL = (2800000, 5100000), (1900000, 4420000)


def euromap(ax):
    ax.set_facecolor("#EEF3F6")
    land.plot(ax=ax, color="#F4EFE3", edgecolor="#D9CFBC", linewidth=0.4)
    seatsE.plot(ax=ax, column="leave", cmap=CM, vmin=20, vmax=76, edgecolor="#FFFFFF", linewidth=0.1)
    ne, eu = (LK.eu == 0).values, (LK.eu == 1).values
    ax.add_collection(LineCollection(arcs(ne), colors=NEC, linewidths=0.55, alpha=0.30, zorder=2))
    ax.add_collection(LineCollection(arcs(eu), colors=EUC, linewidths=0.5, alpha=0.22, zorder=3))
    ax.scatter(bx0[ne], by0[ne], s=7, c=NEC, edgecolors="white", linewidths=0.3, zorder=4)
    ax.scatter(bx0[eu], by0[eu], s=7, c=EUC, edgecolors="white", linewidths=0.3, zorder=4)
    hx, hy = TR.transform(HP.lon.values, HP.lat.values)
    for k, c, z in (("eu", EUC, 5), ("mix", MIX, 6), ("non", NEC, 7)):
        m = (HP.k == k).values
        ax.scatter(np.array(hx)[m], np.array(hy)[m], s=5 + 7 * np.sqrt(HP.n[m]), c=c, edgecolors="white", linewidths=0.45, zorder=z)
    ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    for s_ in ax.spines.values(): s_.set_edgecolor("#CFC6B4")


# ---------------------------------------------------------------- collage
fig = plt.figure(figsize=(13.5, 10.125), dpi=200, facecolor=PAPER)
fig.text(0.035, 0.945, "Twinned with Europe, voted Remain?", fontsize=34, family=DISP, weight="bold", color=INKC)
fig.text(0.035, 0.905, f"Every recorded twinning of a British town or council ({R['pairs']['usable']:,}, {R['pairs']['eu_pc']:.0f}% with EU towns) against the 2016 Leave vote",
         fontsize=15, color=MUT)
ax = fig.add_axes([0.035, 0.19, 0.465, 0.69]); euromap(ax)
# legend on the paper below the map, two columns
lg = fig.add_axes([0.035, 0.045, 0.465, 0.13]); lg.axis("off"); lg.set_xlim(0, 1); lg.set_ylim(0, 1)
lg.text(0.0, 0.93, "British twinned place", fontsize=11, weight=600, color=INKC, va="center")
for i, (lab, c) in enumerate((("partners all in the EU", EUC), ("partners in and outside the EU", MIX), ("partners all outside the EU", NEC))):
    lg.scatter([0.015], [0.70 - i * 0.22], s=60, c=c, edgecolors="white"); lg.text(0.04, 0.70 - i * 0.22, lab, va="center", fontsize=10)
lg.text(0.50, 0.93, f"Lines: each twinning to its partner town ({R['pairs']['with_coords']:,})", fontsize=11, weight=600, color=INKC, va="center")
for i, (lab, c) in enumerate((("partner town in another EU state", EUC), ("partner town outside the EU", NEC))):
    y = 0.70 - i * 0.22
    lg.plot([0.50, 0.55], [y, y], color=c, lw=1.8); lg.scatter([0.55], [y], s=16, c=c, edgecolors="white", zorder=3)
    lg.text(0.565, y, lab, va="center", fontsize=10)
lg.text(0.50, 0.26, "Grey seats: Leave share, light 20% to dark 76%.\nLines off the edge run to partners further away.", fontsize=9.5, color=MUT, va="top")
# right: headline estimates
fig.text(0.53, 0.83, "Comparing similar seats*, the difference in Leave share:", fontsize=15, weight=600, color=INKC)
ax2 = fig.add_axes([0.53, 0.56, 0.43, 0.24]); ax2.set_facecolor("none")
rows = [("Seat has an EU twin", R["main"], EUC), ("Seat has a twin outside the EU\n(placebo: US, China, Russia...)", R["h2"]["noneu_alone"], NEC)]
for i, (lab, c, col) in enumerate(rows):
    y = 1 - i
    ax2.plot([c["lo"], c["hi"]], [y, y], color=col, lw=5, solid_capstyle="round")
    ax2.scatter([c["b"]], [y], s=260, color=col, edgecolors="white", zorder=3, linewidths=2)
    ax2.text(-3.9, y + 0.28, lab, fontsize=13.5, color=INKC, va="bottom")
    ax2.text(max(c["hi"], 0) + 0.25, y, f"{f1(c['b'])} points\n(95% range {f1(c['lo'])} to {f1(c['hi'])})", fontsize=12, family=MONO, color=col, va="center")
ax2.axvline(0, color=INKC, lw=1)
ax2.set_xlim(-4, 4); ax2.set_ylim(-0.5, 1.9); ax2.set_yticks([])
for s in ("left", "top", "right"): ax2.spines[s].set_visible(False)
ax2.set_xticks([-3, -2, -1, 0, 1, 2, 3]); ax2.tick_params(labelsize=11)
ax2.set_xlabel("points of Leave (left: more Remain)", fontsize=11.5, color=MUT)
# country bars
ax3 = fig.add_axes([0.62, 0.17, 0.33, 0.30]); ax3.set_facecolor("none")
bc = R["by_country"][:8][::-1]
ax3.barh(range(len(bc)), [b["n"] for b in bc], color=[EUC if b["eu"] else NEC for b in bc], height=0.68)
ax3.set_yticks(range(len(bc))); ax3.set_yticklabels([b["country"].replace("People's Republic of China", "China") for b in bc], fontsize=12)
for i, b in enumerate(bc):
    ax3.text(b["n"] + 8, i, f"{b['n']:,}", va="center", fontsize=11, family=MONO, color=MUT)
ax3.set_xlim(0, 560); ax3.set_xticks([])
for s in ("top", "right", "bottom"): ax3.spines[s].set_visible(False)
ax3.set_title("Twinnings by partner country", fontsize=14, loc="left", weight=600)
fig.text(0.53, 0.10, "* same region, age, education, jobs, ethnicity, density and town size;\n"
         f"{R['n']['seats']} seats in Great Britain, {R['n']['any_eu']} with an EU twin. The non-EU link\nvanishes when comparing seats within one council area.",
         fontsize=11, color=MUT, va="top")
fig.text(0.035, 0.018, "Data: Wikidata (CC0); Leave estimates C. Hanretty (2017); 2011 census (ONS, NRS); boundaries ONS/OS (OGL)  ·  maps.tristanhotham.com/twins-remain  ·  Dr Tristan Hotham",
         fontsize=10.5, color=MUT)
out = os.path.join(ROOT, "reddit", "twins_remain_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
plt.close(fig)
print("collage", Image.open(out).size)

# ---------------------------------------------------------------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.60, 0.02, 0.38, 0.96]); gbmap(ax, 0.55)
fig.text(0.05, 0.74, "Twinned with Europe,", fontsize=40, family=DISP, weight="bold", color=INKC)
fig.text(0.05, 0.61, "voted Remain?", fontsize=40, family=DISP, weight="bold", color=EUC)
fig.text(0.05, 0.47, f"{R['pairs']['usable']:,} twinnings of British towns, {R['pairs']['eu']:,} with EU towns.", fontsize=17, color=INKC)
fig.text(0.05, 0.40, f"Comparing like with like: {f1(R['main']['b'])} points of Leave.", fontsize=17, color=INKC)
fig.text(0.05, 0.33, "No Remain bonus for EU twins.", fontsize=17, color=EUC, weight=600)
fig.text(0.05, 0.08, "maps.tristanhotham.com/twins-remain · Dr Tristan Hotham", fontsize=12, family=MONO, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
print("header", Image.open(os.path.join(ROOT, "header.png")).size)
