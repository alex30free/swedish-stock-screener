"""
swedish_screener.py
====================
Van Vliet Low-Volatility Screener for Nasdaq OMX Stockholm
Based on: "High Returns from Low Risk" by Pim van Vliet

HOW TO RUN:
  pip install pandas yfinance requests
  python swedish_screener.py

OUTPUT:
  data.json  — loaded by index.html to display the table

SELECTION LOGIC:
  1. Fetch all tickers from OMX Stockholm
  2. Download 13 months of daily price history via yfinance
  3. Calculate 12M annualised volatility (std dev of daily returns × √252)
  4. Calculate 12M momentum (return from month-12 to month-1)
  5. Calculate dividend yield
  6. Filter: keep bottom 30% by volatility
  7. Filter: remove bottom 25% by momentum (avoid value traps)
  8. Rank remaining by composite score
  9. Output top 10 as data.json
"""

import json
import math
import datetime
import warnings
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("ERROR: Missing libraries. Run: pip install yfinance pandas")
    raise

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# These are example large-cap OMX Stockholm tickers in Yahoo Finance format.
# Yahoo Finance appends ".ST" for Stockholm Exchange stocks.
# Expand this list with more tickers for a broader universe.
# Full lists can be found at: https://finance.yahoo.com or NasdaqOMX website.

TICKERS = [
    "ERIC-B.ST", "VOLV-B.ST", "ATCO-A.ST", "ATCO-B.ST", "SWED-A.ST",
    "SEB-A.ST",  "SHB-A.ST",  "INVE-B.ST", "NDA-SE.ST", "ESSITY-B.ST",
    "SAND.ST",   "SKF-B.ST",  "ALFA.ST",   "LATO-B.ST", "CAST.ST",
    "HEXA-B.ST", "HUSQ-B.ST", "KINV-B.ST", "NIBE-B.ST", "SAAB-B.ST",
    "ASSA-B.ST", "BALD-B.ST", "GETI-B.ST", "HM-B.ST",   "INDU-C.ST",
    "ELUX-B.ST", "SSAB-A.ST", "SWEC-B.ST", "TELIA.ST",  "TREL-B.ST",
    "AAK.ST",    "ALIV-SDB.ST","AZN.ST",   "BEIA-B.ST", "BEWI.ST",
    "BIOT.ST",   "BOOL.ST",   "BUFAB.ST",  "CLAS-B.ST", "COOR.ST",
    "DIOS.ST",   "DUNI.ST",   "EKTA-B.ST", "EMBRAC-B.ST","EQT.ST",
    "FABG.ST",   "FAST-B.ST", "FING-B.ST", "GARO.ST",   "HOLM-B.ST",
]

VOLATILITY_PERCENTILE = 0.30   # Keep bottom 30% by volatility
MOMENTUM_CUTOFF       = 0.25   # Remove bottom 25% by momentum
TOP_N                 = 10     # Final output count

# Composite weight
W_VOL  = 0.40
W_MOM  = 0.35
W_YILD = 0.25

OUTPUT_FILE = "data.json"

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_volatility(prices: pd.Series) -> float:
    """Annualised 12-month volatility from daily close prices."""
    returns = prices.pct_change().dropna()
    if len(returns) < 50:
        return float('nan')
    return returns.std() * math.sqrt(252) * 100  # as percentage

def calculate_momentum(prices: pd.Series) -> float:
    """
    12-month momentum: return from 12 months ago to 1 month ago.
    Skips most recent month (standard academic convention).
    """
    if len(prices) < 260:
        return float('nan')
    price_12m_ago = prices.iloc[0]
    price_1m_ago  = prices.iloc[-21]   # ~1 month back
    if price_12m_ago == 0 or pd.isna(price_12m_ago):
        return float('nan')
    return ((price_1m_ago / price_12m_ago) - 1) * 100  # as percentage

def get_sector(ticker_info: dict) -> str:
    """Extract sector from yfinance ticker info."""
    return ticker_info.get('sector', ticker_info.get('industry', 'Unknown'))

def get_div_yield(ticker_info: dict) -> float:
    """Get trailing dividend yield as percentage."""
    dy = ticker_info.get('dividendYield', 0)
    if dy is None:
        return 0.0
    return dy * 100

def get_company_name(ticker_info: dict, ticker: str) -> str:
    name = ticker_info.get('shortName', ticker_info.get('longName', ticker))
    return name

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCREENER
# ─────────────────────────────────────────────────────────────────────────────

def run_screener():
    print(f"\n{'='*60}")
    print(f"  Van Vliet Low-Vol Screener — OMX Stockholm")
    print(f"  Running at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=400)  # 13+ months

    records = []

    for i, ticker in enumerate(TICKERS):
        print(f"[{i+1:>3}/{len(TICKERS)}] Fetching {ticker:<20}", end="", flush=True)

        try:
            stock = yf.Ticker(ticker)
            hist  = stock.history(start=start_date.strftime('%Y-%m-%d'),
                                   end=end_date.strftime('%Y-%m-%d'),
                                   auto_adjust=True)

            if hist.empty or len(hist) < 50:
                print(" ✗  Insufficient data")
                continue

            prices = hist['Close'].dropna()
            vol    = calculate_volatility(prices)
            mom    = calculate_momentum(prices)

            if pd.isna(vol) or pd.isna(mom):
                print(" ✗  Could not compute metrics")
                continue

            info   = stock.info
            dy     = get_div_yield(info)
            name   = get_company_name(info, ticker)
            sector = get_sector(info)

            records.append({
                'ticker':     ticker.replace('.ST', ''),
                'name':       name,
                'sector':     sector,
                'volatility': round(vol, 2),
                'momentum':   round(mom, 2),
                'div_yield':  round(dy,  2),
            })

            print(f" ✓  Vol={vol:5.1f}%  Mom={mom:+6.1f}%  Yield={dy:.1f}%")

        except Exception as e:
            print(f" ✗  Error: {e}")
            continue

    if len(records) < TOP_N:
        print(f"\n⚠  Only {len(records)} stocks had valid data. Need at least {TOP_N}.")

    df = pd.DataFrame(records)
    universe_count = len(df)
    print(f"\n→ Valid universe: {universe_count} stocks")

    # ── Step 1: Filter by volatility ────────────────────────────────────────
    vol_threshold = df['volatility'].quantile(VOLATILITY_PERCENTILE)
    df = df[df['volatility'] <= vol_threshold].copy()
    print(f"→ After volatility filter (bottom {int(VOLATILITY_PERCENTILE*100)}%): {len(df)} stocks")

    # ── Step 2: Filter by momentum ──────────────────────────────────────────
    mom_threshold = df['momentum'].quantile(MOMENTUM_CUTOFF)
    df = df[df['momentum'] >= mom_threshold].copy()
    print(f"→ After momentum filter (remove bottom {int(MOMENTUM_CUTOFF*100)}%): {len(df)} stocks")

    # ── Step 3: Rank each metric (lower rank = better for vol, higher = better for mom/yield) ──
    df['rank_vol']  = df['volatility'].rank(ascending=True)   # lower vol = better
    df['rank_mom']  = df['momentum'].rank(ascending=False)    # higher mom = better
    df['rank_yild'] = df['div_yield'].rank(ascending=False)   # higher yield = better

    # Normalize ranks to 0-100
    n = len(df)
    df['rank_vol']  = (df['rank_vol']  / n) * 100
    df['rank_mom']  = (df['rank_mom']  / n) * 100
    df['rank_yild'] = (df['rank_yild'] / n) * 100

    # Composite score (higher = better)
    df['score'] = (
        (100 - df['rank_vol'])  * W_VOL  +
        (100 - df['rank_mom'])  * W_MOM  +
        (100 - df['rank_yild']) * W_YILD
    ).round(1)

    # ── Step 4: Top 10 ──────────────────────────────────────────────────────
    top10 = df.nlargest(TOP_N, 'score').reset_index(drop=True)
    top10['rank'] = top10.index + 1

    print(f"\n{'─'*60}")
    print(f"  TOP {TOP_N} RESULTS")
    print(f"{'─'*60}")
    for _, row in top10.iterrows():
        print(f"  #{int(row['rank']):>2} {row['ticker']:<15} Vol={row['volatility']:5.1f}%"
              f"  Mom={row['momentum']:+6.1f}%  Yield={row['div_yield']:.1f}%"
              f"  Score={row['score']:.0f}")

    # ── Build output JSON ────────────────────────────────────────────────────
    output = {
        "updated":        datetime.datetime.utcnow().isoformat() + "Z",
        "universe_count": universe_count,
        "stocks": []
    }

    for _, row in top10.iterrows():
        output["stocks"].append({
            "rank":       int(row['rank']),
            "ticker":     row['ticker'],
            "name":       row['name'],
            "sector":     row['sector'],
            "volatility": float(row['volatility']),
            "momentum":   float(row['momentum']),
            "div_yield":  float(row['div_yield']),
            "score":      int(row['score'])
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved → {OUTPUT_FILE}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_screener()
