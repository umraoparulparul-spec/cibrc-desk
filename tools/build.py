import fitz, re, json, sys
from pathlib import Path

DIR = Path(r"C:\Users\Admin\Desktop\472 RC guideline")
SRC = DIR / "472 RCguidelines.pdf"
OUT_PDF = DIR / "472 RC guidelines (bookmarked).pdf"
TEMPLATE = Path(__file__).with_name("finder_template.html")
OUT_HTML = DIR / "CIB&RC Registration Desk.html"

d = fitz.open(SRC)
N = d.page_count

# (level, title, page) - page = PDF page number (matches printed page number)
manual = [
    (1, "Introduction", 5),
    (1, "Category 1 - General Guidelines", 7),
    (2, "1.1 KYC on CROP portal", 8),
    (2, "1.2 Inclusion of pesticide in the Insecticide Schedule", 41),
    (2, "1.2 Infrastructure - botanical biopesticides (Pyrethrum, Azadirachtin, Cymbopogon)", 42),
    (2, "1.3 Infrastructure - Baculoviruses (NPV, GV)", 45),
    (2, "1.4 Infrastructure - microbial biopesticides", 47),
    (2, "1.5 Infrastructure - pesticide manufacturers (State licence)", 50),
    (2, "1.6 Endorsement of additional manufacturing site", 53),
    (2, "1.7 Enhancement of shelf life u/s 9(4)", 55),
    (1, "Category 2 - Export & Import", 57),
    (2, "2.1 Indigenous manufacture for export u/s 9(3)", 62),
    (2, "2.2 Import for export u/s 9(3)", 67),
    (2, "2.3 Import of sample quantity for RTT", 70),
    (2, "2.4 Export of small quantity samples for RTT", 72),
    (1, "Category 3 - Chemical Pesticides (Agriculture)", 73),
    (2, "3.1 Division-wise data requirements 9(3B), 9(3), 9(4)", 74),
    (2, "3.2 Post-harvest treatment (Ethephon)", 91),
    (2, "3.3 Petroleum derived spray oil (PDSO)", 96),
    (2, "3.4 Combination of two registered herbicides", 99),
    (2, "3.5 Combination pesticides (not herbicides) - indigenous 9(3)", 101),
    (2, "3.6 Insecticide + Fungicide combination - foliar spray", 106),
    (2, "3.7 New formulation for seed treatment 9(3)", 108),
    (2, "3.8 Insecticide + Fungicide combination - seed treatment", 112),
    (2, "3.9 New formulation (same a.i.) for seed treatment", 114),
    (2, "3.10 FIM vs FIT u/s 9(3)", 116),
    (2, "3.11 Three a.i. pre-mix - indigenous manufacture", 118),
    (2, "3.12 Three a.i. pre-mix - import", 123),
    (2, "3.13 TIM where formulation registered for import without technical", 128),
    (2, "3.14 TIM by original registrant under FI", 133),
    (2, "3.15 Manufacture Use Product (MUP)", 135),
    (2, "3.16 TI - New Source vs FIM-WRT / FI-WRT / TI", 138),
    (1, "Category 4 - Biorational / Biopesticides", 143),
    (2, "4.1 Microbial pest control agents", 144),
    (2, "4.1.1 Already registered formulation / strain 9(3)", 150),
    (2, "4.1.2 Consortium of biopesticides", 159),
    (2, "4.2 Botanical / plant origin pesticides", 184),
    (2, "4.2.1 Eucalyptus based products (Eucalyptol)", 192),
    (2, "4.2.2 Rotenone for pisciculture", 195),
    (2, "4.2.3 Cymbopogon based plant extract", 197),
    (2, "4.2.4 Import of concentrated Pyrethrum extract", 199),
    (2, "4.2.5 Herbal / botanical plant growth regulators", 201),
    (2, "4.2.6 Neem (Azadirachtin) household insecticides", 203),
    (2, "4.3 Pheromones / Semiochemicals", 206),
    (1, "Category 5 - Household, Public Health, Aircraft etc.", 213),
    (2, "5.1 Household insecticides", 214),
    (2, "5.2 Public Health Programme", 220),
    (2, "5.3 Aircraft disinfection", 221),
    (2, "5.4 Ectoparasites (mites, bedbugs, ticks)", 224),
    (2, "5.5 Biocides & Biocide products (MUP); paints", 229),
    (1, "Additional Information - Requirements & Endorsements", 240),
]

def lines_of(p):
    t = d[p - 1].get_text()
    return [l.strip() for l in t.split("\n")
            if l.strip() and "Guidelines for the Registration of Pesticides" not in l
            and not re.fullmatch(r"\d+", l.strip())]

def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\(Approved.*$", "", s, flags=re.I).strip()
    return s[:110]

# Auto-detect headings in the un-indexed back half
auto = []
for p in range(241, N + 1):
    L = lines_of(p)
    if not L:
        continue
    head = L[0]
    if re.match(r"Requirements? (for|For|under|Under)", head):
        title = head if len(head) > 60 or len(L) < 2 else head + " " + L[1]
        auto.append((2, clean(title), p))
    elif head.startswith("Agricultural Chemicals for which no Maximum Residue"):
        auto.append((1, "No-MRL agricultural chemicals list (FSSAI)", p))
    elif head.startswith("Standard Operating Procedure (SOP) for use of Drone"):
        auto.append((1, "SOP - Drone application of pesticides", p))
    elif head.startswith("Standard Operating Procedures (SOP) on aerial"):
        auto.append((1, "SOP - Aerial spraying for Desert Locust", p))
    elif head.startswith("Coronavirus"):
        auto.append((1, "Coronavirus safety tips", p))
    elif head.startswith("Annexure-3.2.1"):
        auto.append((1, "Scrutiny Templates / Proformas", p))
    elif head == "CHEMISTRY" or head == "TOXICOLOGY" or head == "PACKAGING":
        auto.append((2, "Templates - " + head.title(), p))
    elif head == "BIOEFFICACY":
        auto.append((2, "Templates - Bioefficacy", p))
    elif head.startswith("COMPREHENSIVE TECHNICAL DOSSIER TEMPLATE"):
        auto.append((3, "Chemistry dossier template", p))
    elif head.startswith("TEMPLATES 9(3) BIO-PESTICIDES"):
        auto.append((3, clean(head + " " + L[1]).title(), p))
    elif head.startswith("Format for"):
        auto.append((3, clean(head + " - " + L[1]), p))
    elif head.startswith("TOXICOLOGY TEMPLATE"):
        sub = head.replace("TOXICOLOGY TEMPLATE", "").strip(" -")
        sub = (sub + " " + (L[1] if len(L) > 1 and len(L[1]) < 40 else "")).strip()
        auto.append((3, "Toxicology template " + sub, p))
    elif head.startswith("Template for Packaging") or head.startswith("Template for Endorsement"):
        title = head if len(L) < 2 or len(L[1]) > 45 else head + " " + L[1]
        auto.append((3, clean(title.replace("S. No. Parameters", "")), p))

# fix Chemistry dossier labels with ordinal
cnt = 0
for i, (lv, t, p) in enumerate(auto):
    if t == "Chemistry dossier template":
        cnt += 1
        auto[i] = (lv, f"Chemistry dossier template #{cnt}", p)

FIX = {"Toxicology template 1. General Information:": "Toxicology template - Label & leaflet / general",
       "Template for Packaging Discipline for Applications U/s 9(3)-Bio-": "Template for Packaging Discipline U/s 9(3) - Biopesticides",
       "Template for Endorsement Applications of New Pack Size with": "Template for Endorsement of New Pack Size (approved packing material)"}
auto = [(lv, FIX.get(t, re.sub(r"\s+(in|of|the|in the|for|by)$", "", t.rstrip(" ,:"))), p) for lv, t, p in auto]
outline = manual + auto
# The scrutiny templates heading should be level 1 children nest under it -> already levels 2/3
# PyMuPDF needs levels to never jump by >1
fixed, prev = [], 0
for lv, t, p in outline:
    lv = min(lv, prev + 1)
    fixed.append([lv, t, p])
    prev = lv

# --- bookmarked PDF
d.set_toc(fixed)
d.save(OUT_PDF, garbage=3, deflate=True)
print("bookmarks:", len(fixed))

# --- page text + section map for finder
sections = []  # flat list with page ranges
flat = sorted([(p, lv, t) for lv, t, p in fixed], key=lambda x: (x[0], x[1]))
pages = []
for i in range(N):
    paras = []
    for b in d[i].get_text("blocks", sort=True):
        t = re.sub(r"\s+", " ", b[4].replace("Guidelines for the Registration of Pesticides", "")).strip()
        if not t or re.fullmatch(r"\d{1,3}", t):
            continue
        # rejoin wrapped lines of one paragraph (justified text comes out one line per block)
        listlike = re.match(r"(\d{1,2}(\.\d{1,2})*[.)]|\(?[ivx]{1,4}[.)]|\(?[a-z][.)]|[•●▪◦\-–])\s", t, re.I)
        if paras and not listlike and not re.search(r"[.:;?!]$", paras[-1]) and (t[0].islower() or len(paras[-1]) > 70):
            paras[-1] += " " + t
        else:
            paras.append(t)
    pages.append("\n".join(paras))

def section_for(p):
    best = {}
    for sp, lv, t in flat:
        if sp <= p:
            best[lv] = t
            for k in list(best):
                if k > lv: del best[k]
    return " › ".join(best[k] for k in sorted(best))

secmap = [section_for(p) for p in range(1, N + 1)]
import os
PDF_ONLINE = os.environ.get("PDF_ONLINE", "/_blob/2a0ff1fd816dcc2488fb77005683bd92")
ONLINE = os.environ.get("ONLINE_URL", "https://claude.ai/artifact/Eiy6yMtxqKKNBjPS5BisHD")
SITE = Path(__file__).resolve().parent.parent   # the cibrc-desk-site folder
tpl = TEMPLATE.read_text(encoding="utf-8")
# pages with tables or forms (slow to detect, so cached): python tools/build.py --tables to refresh
TP = Path(__file__).with_name("tablepages.json")
if "--tables" in sys.argv or not TP.exists():
    TP.write_text(json.dumps([i + 1 for i in range(N) if any(t.row_count >= 3 and t.col_count >= 2 for t in d[i].find_tables().tables)]))
TABLE_PAGES = json.loads(TP.read_text())
def render(pdf_url, online, inline=False, mode="local"):
    # mode: "claude" (artifact with AI + database), "site" (free static website), "local" (offline file)
    data = {"pdfUrl": pdf_url, "onlineUrl": online, "inlineViewer": inline, "mode": mode, "pages": pages, "sec": secmap, "tbl": TABLE_PAGES,
            "toc": [[lv, t, p] for lv, t, p in fixed]}
    return tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\/"))
def page(body):
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + body + '\n</html>')
from urllib.parse import quote
OUT_HTML.write_text(page(render(quote(OUT_PDF.name), ONLINE, mode="local")), encoding="utf-8")
(SITE / "index.html").write_text(page(render("guidelines.pdf", "", True, mode="site")), encoding="utf-8")
Path(__file__).with_name("rc-guideline-finder.html").write_text(render(PDF_ONLINE, ONLINE, True, mode="claude"), encoding="utf-8")
print("html MB:", round(OUT_HTML.stat().st_size / 1e6, 2))
