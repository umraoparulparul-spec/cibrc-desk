"""Print the text of contents entries (by index range) compactly, for writing summaries.
usage: python tools/dump_sections.py FIRST LAST [MAXCHARS_PER_SECTION]
Pages that are mostly tables/forms are marked and cut short."""
import json, re, sys
from pathlib import Path
h = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
d = json.loads(re.search(r"const DATA = (\{.*?\});\n", h, re.S).group(1))
P, T, toc = d["pages"], set(d["tbl"]), d["toc"]
first, last = int(sys.argv[1]), int(sys.argv[2])
cap = int(sys.argv[3]) if len(sys.argv) > 3 else 14000

def rng(i):
    lv, _, a = toc[i]
    b = len(P)
    for j in range(i + 1, len(toc)):
        if toc[j][0] <= lv:
            b = toc[j][2] - 1
            break
    # for parents, stop at the first child so text is not printed twice
    if i + 1 < len(toc) and toc[i + 1][0] > lv:
        b = max(a, toc[i + 1][2] - 1)
    return a, max(a, b)

for i in range(first, last + 1):
    a, b = rng(i)
    out = []
    for p in range(a, b + 1):
        t = re.sub(r"[ \t]+", " ", P[p - 1])
        t = re.sub(r"[.…_]{4,}", "…", t)
        if p in T:
            t = t[:900] + (" [TABLE/FORM PAGE, cut]" if len(t) > 900 else "")
        out.append(f"=== p{p} ===\n{t}")
    s = "\n".join(out)
    print(f"\n##### [{i}] {toc[i][1]}  (p{a}-{b})\n{s[:cap]}{' [CUT]' if len(s) > cap else ''}")
