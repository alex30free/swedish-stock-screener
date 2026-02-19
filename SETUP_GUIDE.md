# 📘 Complete Setup Guide — Swedish Low-Vol Stock Screener

> Based on Pim Van Vliet's *High Returns from Low Risk*  
> **Total cost: FREE** (GitHub Pages + GitHub Actions + Yahoo Finance)

---

## What You're Building

```
screener.py       ← Python script that fetches stock data & ranks them
data.json         ← Output file with Top 10 stocks (auto-generated)
index.html        ← Webpage that reads data.json and displays it beautifully
.github/workflows/
  weekly-screener.yml  ← Automation: runs every Monday at 06:00 CET
```

---

## PHASE 1 — Install Tools on Your Computer (One-time, ~30 minutes)

### Step 1.1 — Install Python
1. Go to: https://python.org/downloads
2. Download Python 3.11 or newer
3. During install: ✅ check **"Add Python to PATH"**
4. Verify: open Terminal/Command Prompt and type:
   ```
   python --version
   ```
   You should see: `Python 3.11.x`

### Step 1.2 — Install Python Libraries
In Terminal/Command Prompt:
```bash
pip install yfinance pandas requests
```

### Step 1.3 — Install VS Code (Code Editor)
1. Go to: https://code.visualstudio.com
2. Download and install
3. Open VS Code → install extension: **Python** (by Microsoft)

### Step 1.4 — Install Git
1. Go to: https://git-scm.com/downloads
2. Download and install (use all default options)
3. Verify: in Terminal type:
   ```
   git --version
   ```

---

## PHASE 2 — Create GitHub Repository (Free Hosting, ~20 minutes)

### Step 2.1 — Create GitHub Account
1. Go to: https://github.com
2. Sign up with your email (free)

### Step 2.2 — Create Your Repository
1. Click **"New"** (green button, top left)
2. Repository name: `swedish-stock-screener`
3. Set to **Public** (required for free GitHub Pages)
4. Click **"Create repository"**

### Step 2.3 — Enable GitHub Pages (Free Hosting)
1. Go to your repository → click **Settings**
2. Left sidebar → click **Pages**
3. Under "Source": select **Deploy from a branch**
4. Branch: select **main** → folder: **/ (root)**
5. Click **Save**

Your website will be live at:
```
https://YOUR_USERNAME.github.io/swedish-stock-screener
```
(takes 2–3 minutes to activate)

---

## PHASE 3 — Upload Your Files (~15 minutes)

### Step 3.1 — Create Local Folder
Create a folder on your computer, e.g. `C:\Projects\stock-screener` (Windows) or `~/projects/stock-screener` (Mac)

### Step 3.2 — Add the Files
Copy these files into your folder:
- `index.html`
- `screener.py`
- Create subfolder `.github/workflows/` and put `weekly-screener.yml` inside it

Your folder should look like:
```
stock-screener/
├── index.html
├── screener.py
└── .github/
    └── workflows/
        └── weekly-screener.yml
```

### Step 3.3 — Run the Screener Locally (First Time)
In Terminal, navigate to your folder:
```bash
cd C:\Projects\stock-screener    # Windows
cd ~/projects/stock-screener     # Mac/Linux
```

Run the screener:
```bash
python screener.py
```

This will:
- Download stock data from Yahoo Finance (takes ~5–10 minutes)
- Generate `data.json` with your Top 10 stocks
- You'll see progress printed in the terminal

### Step 3.4 — Test Locally
Open `index.html` in your browser. You should see the screener with real data.

> ⚠️ **Important**: Open it by starting a local server, not by double-clicking.
> In your project folder, run:
> ```bash
> python -m http.server 8000
> ```
> Then open: http://localhost:8000 in your browser.

---

## PHASE 4 — Publish to GitHub (~10 minutes)

### Step 4.1 — Initialize Git in Your Folder
In Terminal (inside your project folder):
```bash
git init
git add .
git commit -m "Initial commit: Van Vliet screener"
```

### Step 4.2 — Connect to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/swedish-stock-screener.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 4.3 — Verify
1. Go to your GitHub repository — you should see all files
2. Go to the Pages URL: `https://YOUR_USERNAME.github.io/swedish-stock-screener`
3. Your screener is live! 🎉

---

## PHASE 5 — Set Up Automation (Every Monday, Free)

The file `.github/workflows/weekly-screener.yml` is already uploaded.  
GitHub Actions will **automatically** run it every Monday at 06:00 CET.

### To Verify It Works:
1. Go to your GitHub repository
2. Click the **"Actions"** tab
3. Click on **"Weekly Stock Screener"** on the left
4. Click **"Run workflow"** (blue button) → **"Run workflow"**
5. Watch it run (takes ~10 minutes)
6. When done: check your website — the data should be updated!

---

## PHASE 6 — Expanding the Stock Universe

The `screener.py` currently has ~50 tickers. To get a better screener:

### Add More Tickers
Find all OMX Stockholm tickers here:
- https://finance.yahoo.com/screener/ (filter: Exchange = Stockholm)
- https://www.nasdaqomxnordic.com/shares

Format: Add `.ST` to the ticker symbol. Examples:
- `BOLS.ST` = Boliden
- `HUFV-A.ST` = Hufvudstaden
- `LIFCO-B.ST` = Lifco

Add them to the `TICKERS` list in `screener.py`, then push to GitHub.

---

## Maintenance Schedule

| Task | Frequency | Time Required |
|------|-----------|---------------|
| Check website is working | Weekly | 2 minutes |
| Review Top 10 for anomalies | Monthly | 10 minutes |
| Update ticker list | Quarterly | 20 minutes |
| Review/adjust weights | Annually | 1 hour |

---

## Cost Breakdown

| Item | Cost |
|------|------|
| GitHub account | FREE |
| GitHub Pages hosting | FREE |
| GitHub Actions automation | FREE (2000 min/month) |
| Yahoo Finance data (via yfinance) | FREE |
| Domain name (optional) | ~$10/year |
| **Total** | **€0/month** |

---

## Troubleshooting

**Website shows "DEMO data" instead of real stocks**  
→ Run `screener.py` first to generate `data.json`, then push to GitHub.

**Some stocks show as "insufficient data"**  
→ Normal — some tickers have limited history or are unavailable on Yahoo Finance. Keep expanding your ticker list.

**GitHub Actions fails**  
→ Go to Actions tab → click the failed run → read the error log. Most common fix: check that `screener.py` is in the root of the repository.

**Rate limiting from Yahoo Finance**  
→ Add `time.sleep(0.5)` between ticker fetches in `screener.py` (already handled in the loop).

---

## Next Level Improvements (When You're Ready)

1. **Add a price chart** per stock using Chart.js
2. **Email alerts** when the Top 10 changes (use GitHub Actions + Gmail API)
3. **Historical tracking** — store weekly snapshots in a CSV
4. **Upgrade data source** to Financial Modeling Prep (free tier, more reliable)
5. **Add custom domain** — buy `yourname.se` (~100 SEK/year) and connect to GitHub Pages

---

*Guide written for: Swedish Low-Vol Screener · Van Vliet Methodology*  
*Based on: High Returns from Low Risk (2016) by Pim van Vliet & Jan de Koning*
