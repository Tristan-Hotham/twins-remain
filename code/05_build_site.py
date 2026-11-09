"""Step 5: index.html from code/page_template.html, filled from data/results.json, with facts stated in words checked.
10.5281/zenodo.24094355, https://doi.org/10.5281/zenodo.24094355 and https://blog.tristanhotham.com/2026/10/31/twins-remain/ stay as placeholders for the publisher."""
import time
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/constituencies.csv")
# facts stated in words
none = set(D[D.any_eu == 0].name)
assert {"Putney", "Wimbledon", "Ross, Skye and Lochaber"} <= none
assert R["top_hosts"][0]["host"] == "Coventry" and R["top_hosts"][1]["n"] < R["top_hosts"][0]["n"]
assert [b["country"] for b in R["by_country"][:6]] == ["France", "Germany", "United States", "Italy", "Poland", "People's Republic of China"]
assert abs(R["head"]["raw_lo"]) > 0 and R["head"]["raw_lo"] < 0 < R["head"]["raw_hi"]
assert R["h2"]["noneu_alone"]["hi"] < 0 and abs(R["h2"]["joint_eu"]["b"]) < 0.5
ne = R["exploratory"]["noneu"]
assert ne["loro_n_sig"] == 11 and ne["england"]["p"] < 0.05 and ne["ladfe"]["p"] > 0.05 and ne["known"]["p"] > 0.05
assert ne["big_noneu"] > ne["big_none"]
assert all(R["robust"][k]["p"] > 0.05 for k in ("point", "eu15", "frde", "known"))
assert R["h2"]["count_eu"]["p"] > 0.05 and R["robust"]["l_neu"]["b"] < 0
assert R["h3"]["model"]["p"] > 0.05 and R["coverage"]["tiny_pc"] < 1
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{BYLINE}}", BYLINE).replace("{{AI}}", AI).replace("{{VERSION}}", time.strftime("%Y")).replace("{{REPO}}", REPO)
t = fill(t, R)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= {"DOI", "DOI_URL", "BLOG_URL"}, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
js = open(os.path.join(ROOT, "js", "page.js"), encoding="utf-8").read()
assert "—" not in js and "–" not in js
print("index.html", len(t) // 1024, "KB")
