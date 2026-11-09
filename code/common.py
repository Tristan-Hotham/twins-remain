"""Shared paths, constants and helpers for the twins-remain study ("Twinned with Europe, voted Remain?").

Raw inputs (read in place, never modified):
  TWINS    /home/claude/newdata/raw_new12/twins_wd.tsv
           Wikidata (CC0): UK places with "twinned administrative body" (P190): host item, label, point, partner item,
           partner label, partner country item, start and end qualifiers where present. One row per host, partner and
           partner country (partners with several historical countries appear several times).
  LABELS   /home/claude/newdata/raw_new12/fame_labels.tsv  English labels for country items (Wikidata, CC0); a few
           country items missing from it are labelled in COUNTRY_EXTRA below.
  RAW      /home/claude/newdata/raw_new11/
           leave_votes_west.csv  Hanretty's estimated Leave share by 2010 Westminster constituency (parlitools)
           census_11.csv         2011 census by 2010 constituency (parlitools; ONS and NRS, OGL v3)
           wpc2010_gb.json       Westminster constituency boundaries, 2010 (ONS/OS, OGL v3), Great Britain
           lad_gb.json           local authority districts 2013 (ONS/OS, OGL v3), Great Britain
           uk_settlements_enwiki.tsv.gz  Wikidata UK settlements with an English Wikipedia article, population where stated
  PCOORD   /home/claude/newdata/raw_new12/twin_partner_coords.tsv  Wikidata (CC0) coordinate location (P625) of the partner
           items, used to draw town-to-town arcs on the map, collage and GIF (a few partners have two nearby points: averaged)
  SETTLE   /home/claude/newdata/raw_new8/uk_settlements.tsv  Wikidata UK settlements with instance-of labels (CC0)
  GEO      /home/claude/newdata/raw/geo  Natural Earth (public domain) for the land base of the figures
Intermediates go to SCR (/home/claude/scratch/twins-remain), outside the repository.
"""
import json, gzip, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TWINS = os.environ.get("TR_TWINS", "/home/claude/newdata/raw_new12/twins_wd.tsv")
LABELS = os.environ.get("TR_LABELS", "/home/claude/newdata/raw_new12/fame_labels.tsv")
RAW = os.environ.get("TR_RAW", "/home/claude/newdata/raw_new11")
PCOORD = os.environ.get("TR_PCOORD", "/home/claude/newdata/raw_new12/twin_partner_coords.tsv")
SETTLE = os.environ.get("TR_SETTLE", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
GEO = os.environ.get("TR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("TR_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("TR_SCRATCH", "/home/claude/scratch/twins-remain")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
FIG = os.path.join(ROOT, "release", "paper")
BLOG = os.path.join(ROOT, "release", "blog")
for d in (DATA, IMG, SCR, FIG, BLOG):
    os.makedirs(d, exist_ok=True)

SLUG = "twins-remain"
TITLE = "Twinned with Europe, Voted Remain?"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
SEED = 20160623

# the other 27 member states of the European Union on 23 June 2016 (Wikidata items)
EU27 = {"Q40": "Austria", "Q31": "Belgium", "Q219": "Bulgaria", "Q224": "Croatia", "Q229": "Cyprus", "Q213": "Czech Republic",
        "Q35": "Denmark", "Q191": "Estonia", "Q33": "Finland", "Q142": "France", "Q183": "Germany", "Q41": "Greece",
        "Q28": "Hungary", "Q27": "Ireland", "Q38": "Italy", "Q211": "Latvia", "Q37": "Lithuania", "Q32": "Luxembourg",
        "Q233": "Malta", "Q55": "Netherlands", "Q36": "Poland", "Q45": "Portugal", "Q218": "Romania", "Q214": "Slovakia",
        "Q215": "Slovenia", "Q29": "Spain", "Q34": "Sweden"}
EU15 = {"Q40", "Q31", "Q35", "Q33", "Q142", "Q183", "Q41", "Q27", "Q38", "Q32", "Q55", "Q45", "Q29", "Q34"}  # with the UK
JOINED = {"Q142": 1958, "Q183": 1958, "Q38": 1958, "Q31": 1958, "Q55": 1958, "Q32": 1958, "Q35": 1973, "Q27": 1973,
          "Q41": 1981, "Q29": 1986, "Q45": 1986, "Q40": 1995, "Q33": 1995, "Q34": 1995, "Q229": 2004, "Q213": 2004,
          "Q191": 2004, "Q28": 2004, "Q211": 2004, "Q37": 2004, "Q233": 2004, "Q36": 2004, "Q214": 2004, "Q215": 2004,
          "Q219": 2007, "Q218": 2007, "Q224": 2013}
# country items not in the label file (checked against the partner labels in the data)
COUNTRY_EXTRA = {"Q55": "Netherlands", "Q35": "Denmark", "Q223": "Greenland", "Q4628": "Faroe Islands", "Q9648": "Falkland Islands"}
# historical states: ignored when the partner also has a present-day state
HISTORICAL = {"Q12560", "Q15180", "Q28513", "Q43287", "Q121932", "Q147909", "Q207272", "Q107258515", "Q600018", "Q1649871",
              "Q104863335", "Q153136", "Q116080", "Q16410", "Q2899771", "Q243652", "Q156111", "Q577867", "Q1108445",
              "Q516160", "Q131964", "Q1470101", "Q253094", "Q2277", "Q940741", "Q63158027", "Q815731", "Q696908",
              "Q152115", "Q172107", "Q8890160", "Q16985296", "Q16056854"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return z0(f"{float(v):.1f}")
    if f == "f2": return z0(f"{float(v):.2f}")
    if f == "f3": return z0(f"{float(v):.3f}")
    if f == "abs1": return f"{abs(float(v)):.1f}"
    if f == "abs2": return f"{abs(float(v)):.2f}"
    if f == "p3": return "<0.001" if float(v) < 0.001 else f"{float(v):.3f}"
    raise ValueError(f)


def z0(s):
    return s[1:] if re.fullmatch(r"-0\.0+", s) else s


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL"), tf=None):
    """replace {{path|fmt}} tokens from results.json; leave the publisher's placeholders and IMG tokens"""
    f = tf or fmt
    return re.sub(r"\{\{(?!IMG\|)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in keep else f(get(R, m.group(1)), m.group(3)), t)


def lit(s):
    s = (s or "").strip()
    if s.startswith("<") and s.endswith(">"):
        return s[1:-1]
    m = re.match(r'^"(.*)"(?:@[\w-]+|\^\^.*)?$', s, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    m = re.match(r"^(.*)@[a-z-]+$", s)
    return m.group(1) if m else s


def qid(s):
    m = re.search(r"(Q\d+)", s or "")
    return m.group(1) if m else ""


def norm_lad(s):
    s = str(s).lower().replace("&", "and")
    for p in ("london borough of ", "royal borough of ", "metropolitan borough of ", "borough of ", "city of ", ", city of",
              " county borough", " district", "the ", ", county of"):
        s = s.replace(p, " ")
    s = re.sub(r"[^a-z]+", " ", s).strip()
    return re.sub(r" city$", "", s)
