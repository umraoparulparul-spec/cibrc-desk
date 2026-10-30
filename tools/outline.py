"""Turn each guideline page into a short outline: headings (3 levels) plus the few lines that matter.

outline_page(text, is_form) -> list of [level, text, kind]
  level 1 = main heading, 2 = sub heading ("1.", "A."), 3 = sub-sub heading / list item ("1.1", "a)", "i."),
  level 4 = key line under a heading
  kind  "h" plain, "k" key content (obligation, prohibition, figure, time limit)
"""
import re

MAIN = re.compile(r"^(sub\s*-?\s*category|category|annexure|part\s+[ivx\d]+\b|chapter|guidelines? for|requirements? (for|under)|standard operating procedure|sop\b|general requirements?)", re.I)
LETTERHEAD = re.compile(r"government of india|ministry of|directorate of|faridabad|nh[- ]?iv|department of agriculture|preview", re.I)
L2 = re.compile(r"^(\d{1,2}[.)](?!\d)|[A-H][.)]|[IVX]{1,4}[.)])\s*")
L3 = re.compile(r"^(\d{1,2}\.\d{1,2}(\.\d{1,2})*\.?|\(?[a-h][.)]|\(?[ivx]{1,4}[.)]|[•●▪◦\-–])\s*", re.I)
KEY = re.compile(r"\b(shall not|shall|must|mandatory|compulsory|not (be )?(allowed|permitted|accepted|considered)|prohibited|invalid|at least|minimum|maximum|not more than|not less than|within \d|validity|valid for|deadline)\b|\b\d+(\.\d+)?\s*(days?|months?|years?|weeks?|%|per ?cent|batches|seasons?|locations?)\b|(rs\.?|inr|₹)\s*[\d,]+", re.I)
JUNK = re.compile(r"^(\[?insert[^\]]*\]?|yes|no|r|nr|s\.?\s*no\.?|sl\.?\s*no\.?|name|date|place|signature|remarks?|particulars|parameters?|details|[-–.…_\s\d/]*)$", re.I)

def clean(t):
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\(?approved by the registration committee[^)]*\)?", "", t, flags=re.I).strip()
    t = re.sub(r"[.…_]{3,}", "…", t)
    t = re.sub(r"(\s+(R|NR)[*#$]*(\s*/\s*NR[*#$]*)?){2,}(?=\s|$)", "", t)   # R / NR cells from tables
    return t.strip(" ,;")

def short(t, limit=160):
    m = re.search(r"^(.{50,}?[.;])\s", t + " ")
    s = m.group(1) if m else t
    return s if len(s) <= limit else s[:limit].rsplit(" ", 1)[0] + "…"

def outline_page(text, is_form=False):
    out, seen = [], set()
    keys_under = 0
    for raw in text.split("\n"):
        t = clean(raw)
        words = t.split()
        if len(t) < 4 or JUNK.match(t) or (len(words) < 2 and not L2.match(t)):
            continue
        letters = re.sub(r"[^A-Za-z]", "", t)
        is_caps = len(letters) >= 8 and letters.isupper() and len(t) <= 110
        lvl = None
        if MAIN.match(t) or is_caps:
            if LETTERHEAD.search(t):
                continue
            lvl = 1
        elif L3.match(t):
            lvl = 3
        elif L2.match(t):
            lvl = 2
        elif len(t) <= 90 and t.endswith(":") and len(words) <= 12:
            lvl = 3
        if lvl:
            body = re.sub(r"\s+", " ", L3.sub("", t) if lvl == 3 else t)
            if lvl == 3 and len(body.split()) < 3 and not t.endswith(":"):
                continue                      # form fragments like "a) Name"
            if is_form and lvl == 3:
                continue                      # forms: keep only the main and sub headings
            text_ = short(t, 200 if lvl == 1 else 160).rstrip(":")
            key = text_.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append([lvl, text_, "k" if KEY.search(t) else "h"])
            keys_under = 0
            continue
        if KEY.search(t) and len(words) >= 5 and keys_under < 3:
            s = short(t)
            if s.lower() not in seen:
                seen.add(s.lower())
                out.append([4, s, "k"])
                keys_under += 1
    # long runs of plain list items read like a form: keep 8, then a "more" marker
    res, run = [], 0
    for item in out:
        run = run + 1 if item[0] == 3 and item[2] == "h" else 0
        if run <= 8:
            res.append(item)
        elif run == 9:
            res.append([3, "…more items on this page", "m"])
    return res
