"""Refresh updates.json from the CIB&RC website and email any new items.

Run by GitHub Actions twice a day (see .github/workflows/site.yml); can also be run by hand:
    python scripts/update_site.py
Email is sent only when these environment variables are set (GitHub secrets):
    SMTP_USER   the Gmail address that sends the alert
    SMTP_PASS   a Gmail "App password" for that address
    NOTIFY_TO   who receives the alert (comma-separated for several people)
"""
import hashlib, html, json, os, re, smtplib, sys, urllib.request
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "scripts" / "seen.json"
OUT = ROOT / "updates.json"
IST = timezone(timedelta(hours=5, minutes=30))
BASE = "https://ppqs.gov.in"
SOURCES = [
    ("news", BASE + "/divisions/cib-rc/news-update", 3),      # ~30 newest notices, minutes, gazettes
    ("guidelines", BASE + "/divisions/cib-rc/guidelines", 5),  # whole guideline list
]
KEEP = 200

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CIB&RC update watcher)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def kind_of(source, title):
    t = title.lower()
    if re.search(r"gazette|\bs\.?o\.? ?\d|\bg\.?s\.?r\.? ?\d", t):
        return "Gazette"
    if re.search(r"^minutes|regarding minutes|minutes of (the )?\d+", t):
        return "RC minutes"
    if source == "guidelines" or "guideline" in t or "sop" in t:
        return "Guideline"
    return "Public notice"

def parse(source, page_html):
    items = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page_html, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 3:
            continue
        title = clean(cells[1])
        if source == "guidelines" and len(cells) >= 4:
            desc = clean(cells[2])
            if desc and desc.lower() != title.lower():
                title = f"{title}: {desc}"
        m = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", clean(cells[2]))
        date = m.group(1) if m else ""
        links = re.findall(r'href="([^"]+)"', row)
        url = links[0] if links else ""
        if url.startswith("/"):
            url = BASE + url
        if title:
            iid = hashlib.sha1((source + "|" + title + "|" + url).encode()).hexdigest()[:16]
            items.append({"id": iid, "kind": kind_of(source, title), "title": title, "date": date, "url": url, "source": source})
    return items

def scrape():
    found, latest = [], []
    for source, url, pages in SOURCES:
        for p in range(pages):
            items = parse(source, fetch(url + (f"?page={p}" if p else "")))
            if not items:
                break
            found += items
            if source == "news":
                latest += items
    if not found:
        raise RuntimeError("no rows found; the CIB&RC website layout may have changed")
    return found, latest

def as_doc(it, now, fresh):
    d = it["date"]
    iso = f"{d[6:10]}-{d[3:5]}-{d[0:2]}" if len(d) == 10 else now[:10]
    return {**it, "sortKey": f"{iso}|{now}", "addedAt": now, "fresh": fresh}

def send_email(new):
    user, pw, to = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"), os.environ.get("NOTIFY_TO")
    if not (user and pw and to):
        print("email skipped: SMTP_USER / SMTP_PASS / NOTIFY_TO not set")
        return
    order = {"Gazette": 0, "RC minutes": 1, "Guideline": 2, "Public notice": 3}
    new = sorted(new, key=lambda i: order.get(i["kind"], 9))
    kinds = ", ".join(sorted({i["kind"] for i in new}, key=lambda k: order.get(k, 9)))
    site = os.environ.get("SITE_URL", "")
    rows = "".join(f'<li><b>{html.escape(i["kind"])}</b> · {html.escape(i["date"] or "")} · {html.escape(i["title"])}'
                   + (f' · <a href="{html.escape(i["url"])}">Open PDF</a>' if i["url"] else "") + "</li>" for i in new)
    body_html = (f"<p>{len(new)} new item(s) on the CIB&amp;RC website:</p><ul>{rows}</ul>"
                 + (f'<p><a href="{html.escape(site)}">CIB&amp;RC Registration Desk</a> · ' if site else "<p>")
                 + '<a href="https://ppqs.gov.in/divisions/cib-rc/news-update">Official CIB&amp;RC News &amp; Update</a></p>')
    body_text = f"{len(new)} new item(s) on the CIB&RC website:\n\n" + "\n".join(
        f'- {i["kind"]} | {i["date"]} | {i["title"]}\n  {i["url"]}' for i in new) + \
        (f"\n\nCIB&RC Registration Desk: {site}" if site else "") + "\nOfficial page: https://ppqs.gov.in/divisions/cib-rc/news-update\n"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"CIB&RC update: {len(new)} new item(s) - {kinds}"
    msg["From"], msg["To"] = user, to
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(user, pw)
        s.sendmail(user, [a.strip() for a in to.split(",") if a.strip()], msg.as_string())
    print(f"email sent to {to}")

def main():
    now = datetime.now(IST).isoformat(timespec="seconds")
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"items": []}
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else None
    try:
        found, latest = scrape()
    except Exception as e:
        old.update(checkedAt=now, ok=False, error=f"{type(e).__name__}: {e}")
        OUT.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
        print("check failed:", e)
        return 1
    if seen is None:   # first run: show the latest items, alert nothing
        new, docs = [], [as_doc(i, now, False) for i in latest[:30]]
    else:
        new = [i for i in found if i["id"] not in seen]
        docs = [as_doc(i, now, True) for i in new]
    known = {d["id"] for d in docs}
    items = docs + [d for d in old.get("items", []) if d["id"] not in known]
    items.sort(key=lambda d: d.get("sortKey", ""), reverse=True)
    OUT.write_text(json.dumps({"checkedAt": now, "ok": True, "items": items[:KEEP]}, ensure_ascii=False, indent=1), encoding="utf-8")
    SEEN.write_text(json.dumps(sorted((seen or set()) | {i["id"] for i in found})))
    print(f"{len(new)} new item(s)")
    if new:
        send_email(new)
    return 0

if __name__ == "__main__":
    sys.exit(main())
