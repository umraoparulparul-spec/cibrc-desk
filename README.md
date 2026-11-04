# CIB&RC Registration Desk

A free website for pesticide registration work under the Insecticides Act, 1968: search the 472 RC guidelines, read sections with highlights, build checklists, see the original PDF pages, and get email alerts for new CIB&RC notices, RC minutes and Gazettes.

Website: `https://<your-github-username>.github.io/cibrc-desk/` (after the steps below)

---

## Website ko GitHub par kaise daalein (ek baar ka kaam, ~15 minute)

### Step 1: GitHub account
1. https://github.com/signup par free account banayein.
2. Username yaad rakhein; website ka link isi se banega.

### Step 2: Naya repository banayein
1. https://github.com/new kholein.
2. **Repository name:** `cibrc-desk`
3. **Public** chunein (free website ke liye zaruri hai).
4. **Create repository** dabayein.

### Step 3: Files upload karein
1. Naye repository page par **"uploading an existing file"** link dabayein.
2. Is folder (`cibrc-desk-site`) ke **andar ki saari cheezein** select karke browser mein drag karein:
   `index.html`, `guidelines.pdf`, `updates.json`, `README.md`, `.gitignore`, aur folders `scripts`, `tools`, `.github`.
   - `.github` folder chhupa (hidden) ho sakta hai: File Explorer mein **View → Show → Hidden items** on karein.
3. Neeche **Commit changes** dabayein.
4. Check karein ki repository mein `.github/workflows/site.yml` dikh raha hai. Agar `.github` upload nahi hua: **Add file → Create new file**, naam likhein `.github/workflows/site.yml`, aur is folder ki `site.yml` file ka text paste karke commit karein.

### Step 4: Website chalu karein
1. Repository mein **Settings → Pages** kholein.
2. **Source** mein **GitHub Actions** chunein.
3. **Actions** tab kholein → **Update and publish site** → **Run workflow** dabayein.
4. 1-2 minute baad website khulegi: `https://<username>.github.io/cibrc-desk/`

### Updates aur email
CIB&RC website GitHub ke servers ko block karti hai (HTTP 403), isliye check aapke computer se hota hai: Claude app ka scheduled task roz 9 AM par check karke `updates.json` yahan bhejta hai. Email hafte mein ek baar aata hai (Monday), CROP portal update par turant. Claude app band ho to check agli baar app kholne par chalta hai.

---

## Kya-kya hai website mein
- **Ask a question:** apne shabdon mein sawal likhein; guidelines ke sabse milte-julte paragraphs page number ke saath dikhte hain (is free version mein AI nahi hai).
- **Checklist wizard:** 9(3B) / 9(3) / 9(4) aur TI / TIM / FI / FIM chunein; Section 3.1 ki tables se poori checklist. Tick aur notes isi browser mein save hote hain.
- **Search pages**, **contents**, **section reader** (must/shall, numbers, Act sections highlighted), **original PDF page viewer**.
- **Latest updates:** CIB&RC News & Update aur Guidelines pages se.
- **CROP portal** aur official links upar.

## Files
| File | Kya hai |
|---|---|
| `index.html` | Website |
| `guidelines.pdf` | 472 RC guidelines (bookmarks ke saath) |
| `updates.json` | Latest CIB&RC items (GitHub khud update karta hai) |
| `scripts/update_site.py` | CIB&RC site check |
| `.github/workflows/site.yml` | Files badalne par website publish karne ka setup |
| `tools/` | Website dobara banane ke liye (`python tools/build.py`) |

Page numbers are PDF page numbers (the number in your PDF viewer), not the printed footer numbers, which restart in places.
