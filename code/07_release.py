"""Step 7: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24094355, https://doi.org/10.5281/zenodo.24094355 and https://blog.tristanhotham.com/2026/10/31/twins-remain/ stay as placeholders for the publisher."""
import shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Twins_Remain"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
assert R["by_neu"][3]["leave"] < R["by_neu"][0]["leave"] + 1.5 and abs(R["by_neu"][3]["degree"] - R["by_neu"][0]["degree"]) < 1.5
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
P, M = R["pairs"], R["main"]
meta = {"title": "Twinned with Europe, voted Remain? Town twinning and the Brexit vote",
        "slug": "twins-remain",
        "excerpt": f"British towns have {P['usable']:,} recorded twinnings, {P['eu_pc']:.0f}% of them with towns in the EU. I checked whether the places with European twins voted Remain in 2016. Comparing like with like, they voted about the same as similar places.",
        "seo_description": f"{P['usable']:,} British town twinnings mapped against the 2016 Leave vote. Did places twinned with Europe vote Remain? Comparing like with like, no clear difference.",
        "tags": ["maps", "town twinning", "Brexit", "EU referendum", "Europe", "elections", "electoral geography", "Wikidata", "data visualisation"],
        "header_alt": f"Title card reading 'Twinned with Europe, voted Remain?' beside a map of Great Britain with blue dots for places twinned with EU towns over constituencies shaded grey by Leave vote, and the lines {P['usable']:,} twinnings of British towns, {P['eu']:,} with EU towns; comparing like with like, {fmt(M['b'], 'f1')} points of Leave."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        if fn in ("hosts.json", "seats.geojson"):
            continue
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "")
assert "\\" not in ab, ab
zmeta = {"title": "Twinned with Europe, Voted Remain? Town Twinning and the Geography of the 2016 Referendum in Great Britain",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/twins-remain/}}.</p><p>Sources: Wikidata (CC0); Leave estimates by C. Hanretty (2017) via parlitools; 2011 census (ONS, NRS) and ONS/OS boundaries (Open Government Licence v3.0). Derived twinning tables CC0; text and figures CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["town twinning", "Brexit", "EU referendum", "European identity", "transactionalism", "electoral geography", "Wikidata"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "Text and figures CC BY 4.0; code MIT; twinning tables derived from Wikidata, CC0; census and boundary derived data under the Open Government Licence v3.0.",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = json.dumps(zmeta, ensure_ascii=False) + json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
