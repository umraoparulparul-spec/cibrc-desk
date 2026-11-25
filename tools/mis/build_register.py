"""Save the full list of CIB&RC notices, RC minutes, Gazettes and guidelines from ppqs.gov.in.

usage: python build_register.py
writes register_items.json next to this script (newest first, as the website lists them).
Plain-English notes for items live in register_notes.json (keyed by item id) and are merged by build.py.
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "updates"))   # reuse the watcher's fetch + parser
import watch_cibrc as w

def date_of(it):
    if it["date"]:
        return it["date"]
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", it["title"])   # most older titles carry "dated dd.mm.yyyy"
    return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}" if m else ""

items, seen = [], set()
for src, base in (("news", "/divisions/cib-rc/news-update"), ("guidelines", "/divisions/cib-rc/guidelines")):
    for pg in range(0, 200):
        got = w.parse(src, w.fetch(w.BASE + base + f"?page={pg}"))
        new = [i for i in got if i["id"] not in seen]
        if not new:
            break
        for i in new:
            seen.add(i["id"])
            i["date"] = date_of(i)
            m = re.search(r"minutes of (?:the )?(\d{3})", i["title"], re.I)
            i["meeting"] = int(m.group(1)) if m and i["kind"] == "RC minutes" else None
            i["seq"] = len(items)
            items.append(i)
    print(src, "items so far:", len(items))
(HERE / "register_items.json").write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding="utf-8")
from collections import Counter
print(Counter(i["kind"] for i in items), "dated:", sum(1 for i in items if i["date"]))
