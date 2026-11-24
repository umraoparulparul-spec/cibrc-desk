"""Turn one RC minutes PDF into a list of agenda-item rows for the RC MIS.

usage: python extract_rc.py MEETING_NO MINUTES.pdf [MINUTES_URL]
writes rc<MEETING_NO>_items.json next to this script and prints a short report.
"""
import json, re, sys
from pathlib import Path
import fitz

sys.stdout.reconfigure(encoding="utf-8")
no, pdf = int(sys.argv[1]), sys.argv[2]
url = sys.argv[3] if len(sys.argv) > 3 else ""
d = fitz.open(pdf)

# 1. lines with page numbers, up to "Meeting ended" (the annexures follow)
lines = []
for i in range(d.page_count):
    for ln in d[i].get_text().split("\n"):
        s = ln.strip()
        if (not s or re.match(r"(Minutes of )?\d+(st|nd|rd|th) Registration Committee meeting held on", s, re.I)
                or re.fullmatch(r"Page \d+ of \d+", s) or re.fullmatch(r"\d{1,4}", s)):
            continue
        lines.append((i + 1, s))
    if any("Meeting ended" in s for p, s in lines[-40:] if p == i + 1):
        break
# English part starts at the first "1.0" line that is followed by English text
start = next(k for k, (p, s) in enumerate(lines) if s == "1.0" and re.search(r"[A-Za-z]{4}", lines[k + 1][1]))
lines = lines[start:]

# 2. split into numbered blocks; keep only numbers that follow the agenda order
NUM = re.compile(r"(\d{1,2})\.(\d{1,3})\.?")
blocks, cur, last, seen0 = [], None, (0, 0), False
for p, s in lines:
    m = NUM.fullmatch(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        ok = (a == last[0] and last[1] < b <= last[1] + 6) or (a > last[0] and a <= last[0] + 3 and (b == 0 or (b == 1 and not seen0)))
        if ok and b == 0:
            seen0 = True
        if ok:
            cur = {"no": f"{a}.{b}", "major": a, "page": p, "text": []}
            blocks.append(cur)
            last = (a, b)
            continue
    if cur is not None:
        cur["text"].append(s)

STOP = {"of", "for", "registration", "on", "the", "manufacture", "Manufacture", "(TIM)", "import", "Import", "expansion",
        "extension", "label", "in", "application", "with", "and", "certificate", "Certificate", "from", "to", "Min", "regularization"}
FORM = r"\b(?:SC|EC|WG|WP|SL|OD|SE|FS|GR|ZC|ME|CS|EW|DP|DF|WDG|SG|FU|MUP|LF|WS|DS|TC|TK|SP|GB|RB|Tablets?|tablets?|Bed Net|Agarbattis)\b|\b[Mm]in(imum)?\b\.?|\bMIN\b\.?"
def product_of(t):
    i = t.find("%")
    if i < 0:
        return ""
    toks = t[:i].rstrip().split(" ")
    k = len(toks)
    while k > 0 and toks[k - 1] not in STOP and not toks[k - 1].endswith(","):
        k -= 1
    head = " ".join(toks[k:])
    m = re.search(FORM + r"|(?=\s+(?:u/s|under|registered|issued|for|from|of M/s|on the|in respect|w\.r\.t|bearing|Registration)\b)|[;]", t[i:])
    tail = t[i:i + m.end()] if m else t[i:i + 60]
    return re.sub(r"\s+", " ", (head + " " + tail).strip(" ,.(")).replace(" %", "%")
GROUP = {}
items = []
for bl in blocks:
    txt = re.sub(r"\s+", " ", " ".join(bl["text"])).strip()
    if bl["no"].endswith(".0"):
        GROUP[bl["major"]] = re.split(r"\s{2,}| NIL| The | RC ", txt)[0].strip()[:60]
        continue
    # title = text up to the RC's decision
    m = re.search(r"\s(RC|The RC|The Registration Committee|The Committee|With the permission|Registration Committee)\s(deliberated|perused|peruse|noted|discussed|considered|granted|recalled|deliberate|Noted|after|approved|confirms|decided|directed|accepted|agreed)\b", txt)
    m2 = re.search(r"\s(After detailed deliberations|After deliberations|Chlobentheram is not)\b", txt)
    if m2 and (not m or m2.start() < m.start()):
        m = m2
    title, decision = (txt[:m.start()], txt[m.start():]) if m else (txt, "")
    if not decision and re.search(r"\b(Approved|merged)\b", txt):
        i = max(txt.rfind(". ", 0, max(txt.find("Approved"), txt.find("merged"))), 0)
        title, decision = txt[:i + 1], txt[i + 1:]
    title, decision = title.strip(), decision.strip()
    CO = r"\b(?:M/[sS]|Mis)\.?\s*(?:M/s\.?\s*)?(.+?)(?=,|\s+for\s|\s+\(|\s+u/s|\s+under\s|\s+has\s|\s+to\s|\s+regarding|\s+on\s|\s+despite|\s+[Aa]pplied|\.$|$)"
    co = re.search(CO, title) or re.search(CO, decision)
    company = co.group(1).strip(" .") if co else ""
    if company.lower().startswith("sterling") or not company:
        co2 = re.search(r"from (Sterling Agrichem Pvt Ltd)", title)
        company = co2.group(1) if co2 else company
    if not company:
        co = re.search(r"submitted by ([A-Z][\w&.\- ]+?(University|Ltd|Limited|Institute))", title)
        company = co.group(1) if co else ""
    sec = re.search(r"9\s*\(\s*(3\s*[bB]|3|4)\s*\)", title + " " + decision)
    section = ("9(" + sec.group(1).replace(" ", "").upper() + ")") if sec else ""
    cat = re.findall(r"\b(TIM|TI|FIM|FI|MUP|FIT)\b", title)
    category = cat[0] if cat else ""
    pr = re.search(r"(?:registration (?:of|for)|for (?:Import|import) of|indigenous manufacture of|Endorsement[^.]*?(?:for|of)|label (?:extension|claim expansion) (?:of|on))\s+(?:Import of |import of |indigenous manufacture of |indigenous manufacturing of )?(.+?)(?=\s+(?:u/s|under\s+[Ss]ection|under\s+9|from M/s|for control|of M/s|registered u/s)|[.;]\s|$)", title)
    product = re.sub(r"^product\s+", "", product_of(title)) or (pr.group(1).strip(" ,.") if pr else "")
    dl = (decision or txt).lower()
    if re.search(r"show cause", dl): status = "Show-cause"
    elif re.search(r"presentation in the next|for (making|a) (detailed )?presentation|make (a )?(detailed )?presentation", dl): status = "Presentation called"
    elif re.search(r"\bdefer", dl): status = "Deferred"
    elif re.search(r"\breject", dl): status = "Rejected"
    elif re.search(r"re-?open", dl) and re.search(r"approved|decided|agreed", dl): status = "Reopened"
    elif re.search(r"\bclos(e|ure|ed)\b", dl): status = "Closed"
    elif re.search(r"presentation", dl): status = "Presentation called"
    elif re.search(r"clarification|ask(ed)? .{0,40}data|seek", dl): status = "Clarification sought"
    elif re.search(r"approved|allowed|accept|granted|confirms|changed the heading|decided as per|decided that|may be read as|decided to constitute|confirmed", dl): status = "Approved / decided"
    elif re.search(r"noted|note of", dl): status = "Noted"
    elif "merged" in dl: status = "Merged"
    elif re.search(r"direct(ed|s) .{0,80}(report|present|compile|look into)", dl): status = "Report / action directed"
    else: status = "Other"
    if re.match(r"(Closure|Applications for closure|Request for closure)", title) and status == "Approved / decided":
        status = "Closed"
    tl = title.lower()
    g = bl["major"]
    gname = GROUP.get(g, "").lower()
    if "export" in gname: typ = "Export"
    elif "9(3b)" in gname: typ = "New registration 9(3B)"
    elif "9(3)" in gname: typ = "New registration 9(3)"
    elif "9(4) tim" in gname: typ = "Me-too 9(4) TIM"
    elif "9(4)" in gname: typ = "Me-too 9(4) TI/FI/FIM"
    elif "endorsement" in gname:
        if company:
            tl = tl.replace(company.lower(), " ")   # company names such as "... Crop Science" are not crops
        typ = ("Packaging" if re.search(r"packag|packing|corrigendum", tl) else
               "Shelf life" if "shelf" in tl else
               "Source / supplier" if re.search(r"source|supplier|purity", tl) else
               "Name / address" if re.search(r"change of (company )?name|address|duplicate|import permit", tl) else
               "Label expansion / crops" if re.search(r"label|deletion of crops|\bcrops?\b", tl) else "Endorsement")
        typ = "Endorsement: " + typ
        # a plain subject for name / address cases
        if typ.endswith("Name / address"):
            nm = re.search(r"change of company name from .+? to (?:M/s\.?\s*)?(.+?)(?: in respect| for |\.$|$)", title, re.I)
            lab = ("Name change to " + nm.group(1).strip(" .") if nm else
                   "Additional factory address" if re.search(r"additional factory address", title, re.I) else
                   "Registered office address change" if re.search(r"registered office address", title, re.I) else
                   "Factory address change" if re.search(r"factory address", title, re.I) else
                   "Duplicate certificate" if "duplicate" in title.lower() else
                   "Office address" if "office address" in title.lower() else "")
            n = re.search(r"in respect of (\d+) Nos", title)
            mol = product if product and not re.match(r"(additional|change)", product, re.I) else ""
            if lab:
                product = lab + (f" · {mol}" if mol else "") + (f" · {int(n.group(1))} certificates" if n else "")
    else:
        typ = "File closure / reopening" if re.search(r"clos|reopen|re-open", tl) else "Policy / other"
    annex = sorted(set(re.findall(r"Annexure\s*[-–]?\s*(\d+\.\d+\.\d+)", txt)))
    cnt = re.search(r"\((\d+)\s+(?:applications|nos?\.?)\)|list of (\d+) applications", txt)
    items.append({
        "no": bl["no"], "group": GROUP.get(bl["major"], ""), "page": bl["page"],
        "title": title, "decision": decision,
        "company": company, "product": product, "section": section, "category": category,
        "status": status, "type": typ, "annex": annex, "count": int(next(g for g in cnt.groups() if g)) if cnt else None,
    })

out = Path(__file__).with_name(f"rc{no}_items.json")
out.write_text(json.dumps({"meeting": no, "url": url, "groups": GROUP, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print(len(items), "items ->", out.name)
print("groups:", GROUP)
print("status:", Counter(i["status"] for i in items))
print("type:", Counter(i["type"] for i in items))
print("no company:", sum(1 for i in items if not i["company"]), " no product:", sum(1 for i in items if not i["product"]))
