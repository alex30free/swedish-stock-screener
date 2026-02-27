"""
swedish_screener.py
====================
Low-Volatility Screener — Nasdaq OMX Stockholm
Based on: "High Returns from Low Risk" by Pim van Vliet

Universe: Large Cap + Mid Cap + Small Cap (~200 tickers)

HOW TO RUN:
  python -m pip install yfinance pandas requests
  python screener.py

OUTPUT:
  data.json  — loaded by index.html to display the table
"""

import json
import math
import time
import datetime
import warnings
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("ERROR: Run: python -m pip install yfinance pandas")
    raise

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

VOLATILITY_PERCENTILE = 0.30   # Keep bottom 30% by volatility
MOMENTUM_CUTOFF       = 0.25   # Remove bottom 25% by momentum
TOP_N                 = 10     # Final output count
W_VOL                 = 0.40   # Composite weight: volatility
W_MOM                 = 0.35   # Composite weight: momentum
W_YILD                = 0.25   # Composite weight: yield
OUTPUT_FILE           = "data.json"

# ─────────────────────────────────────────────────────────────────────────────
# FULL SWEDISH STOCK UNIVERSE — 372 tickers
# Source: Nasdaq OMX Stockholm (Large + Mid + Small Cap)
# Ticker list sourced from Swedish_Stocks_Yahoo.csv — all Yahoo Finance .ST tickers
# ─────────────────────────────────────────────────────────────────────────────

# Format: (Company Name, Yahoo Finance Ticker)
from fetch_swedish_tickers import get_tickers

TICKERS = get_tickers(verbose=True)
TICKER_NAMES = {t: n for n, t in TICKERS}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_volatility(prices: pd.Series) -> float:
    """Annualised 12-month volatility from daily close prices."""
    returns = prices.pct_change().dropna()
    if len(returns) < 50:
        return float('nan')
    return returns.std() * math.sqrt(252) * 100

def calculate_momentum(prices: pd.Series) -> float:
    """12-month momentum: return from 12 months ago to 1 month ago."""
    if len(prices) < 220:
        return float('nan')
    price_12m_ago = prices.iloc[0]
    price_1m_ago  = prices.iloc[-21]
    if price_12m_ago == 0 or pd.isna(price_12m_ago):
        return float('nan')
    return ((price_1m_ago / price_12m_ago) - 1) * 100

def get_div_yield(ticker_info: dict) -> float:
    """
    Robust dividend yield for Swedish stocks.
    Calculates from dividend amount / price to avoid
    Yahoo Finance returning raw SEK amounts instead of yield %.
    """
    # Best: calculate directly from annual dividend / current price
    div_rate = ticker_info.get('trailingAnnualDividendRate')
    price    = ticker_info.get('currentPrice') or ticker_info.get('regularMarketPrice')
    if div_rate and price and price > 0 and div_rate > 0:
        dy = (div_rate / price) * 100
        if 0 < dy < 20:   # sanity check — no Swedish stock yields 20%+
            return round(dy, 2)

    # Fallback: trailingAnnualDividendYield (decimal like 0.067 = 6.7%)
    dy2 = ticker_info.get('trailingAnnualDividendYield')
    if dy2 and 0 < dy2 < 0.20:
        return round(dy2 * 100, 2)

    return 0.0

def get_sector(info: dict) -> str:
    return info.get('sector') or info.get('industry') or 'Unknown'

def get_name(info: dict, ticker: str) -> str:
    # Prefer the known name from our CSV universe, fall back to Yahoo Finance info
    return TICKER_NAMES.get(ticker) or info.get('shortName') or info.get('longName') or ticker

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCREENER
# ─────────────────────────────────────────────────────────────────────────────

def run_screener():
    print(f"\n{'='*65}")
    print(f"  Van Vliet Low-Vol Screener — OMX Stockholm")
    print(f"  Universe: {len(TICKERS)} tickers (Large + Mid + Small Cap — sourced from Swedish_Stocks_Yahoo.csv)")
    print(f"  Running at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}\n")

    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=400)

    records = []
    skipped = 0

  for i, (name, ticker) in enumerate(TICKERS):
        print(f"[{i+1:>3}/{len(TICKERS)}] {ticker:<20}", end="", flush=True)

        try:
            stock = yf.Ticker(ticker)
            hist  = stock.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                auto_adjust=True
            )

            if hist.empty or len(hist) < 50:
                print("✗  Insufficient price history")
                skipped += 1
                time.sleep(0.3)
                continue

            prices = hist['Close'].dropna()
            vol    = calculate_volatility(prices)
            mom    = calculate_momentum(prices)

            if pd.isna(vol) or pd.isna(mom):
                print("✗  Could not compute metrics")
                skipped += 1
                time.sleep(0.3)
                continue

            info   = stock.info
            dy     = get_div_yield(info)
            name   = get_name(info, ticker)
            sector = get_sector(info)

            records.append({
                'ticker':     ticker.replace('.ST', ''),
                'name':       name,
                'sector':     sector,
                'volatility': round(vol, 2),
                'momentum':   round(mom, 2),
                'div_yield':  round(dy,  2),
            })

            print(f"✓  Vol={vol:5.1f}%  Mom={mom:+6.1f}%  Yield={dy:.1f}%")

        except Exception as e:
            print(f"✗  {str(e)[:50]}")
            skipped += 1

        time.sleep(0.3)   # be polite to Yahoo Finance

    print(f"\n{'─'*65}")
    print(f"  Valid: {len(records)} stocks   Skipped: {skipped}")
    print(f"{'─'*65}")

    if len(records) < TOP_N:
        print(f"⚠  Only {len(records)} valid stocks — need at least {TOP_N}.")
        return

    df = pd.DataFrame(records)
    universe_count = len(df)

    # ── Step 1: Volatility filter ────────────────────────────────────────────
    vol_threshold = df['volatility'].quantile(VOLATILITY_PERCENTILE)
    df = df[df['volatility'] <= vol_threshold].copy()
    print(f"\n→ After volatility filter (bottom {int(VOLATILITY_PERCENTILE*100)}%): {len(df)} stocks")

    # ── Step 2: Momentum filter ──────────────────────────────────────────────
    mom_threshold = df['momentum'].quantile(MOMENTUM_CUTOFF)
    df = df[df['momentum'] >= mom_threshold].copy()
    print(f"→ After momentum filter (remove bottom {int(MOMENTUM_CUTOFF*100)}%): {len(df)} stocks")

    # ── Step 3: Composite score ──────────────────────────────────────────────
    n = len(df)
    df['rank_vol']  = df['volatility'].rank(ascending=True)  / n * 100
    df['rank_mom']  = df['momentum'].rank(ascending=False)   / n * 100
    df['rank_yild'] = df['div_yield'].rank(ascending=False)  / n * 100

    df['score'] = (
        (100 - df['rank_vol'])  * W_VOL  +
        (100 - df['rank_mom'])  * W_MOM  +
        (100 - df['rank_yild']) * W_YILD
    ).round(1)

    # ── Top 10 ───────────────────────────────────────────────────────────────
    top10 = df.nlargest(TOP_N, 'score').reset_index(drop=True)
    top10['rank'] = top10.index + 1

    print(f"\n{'='*65}")
    print(f"  TOP {TOP_N} — VAN VLIET LOW-VOL SCREENER")
    print(f"{'='*65}")
    for _, row in top10.iterrows():
        print(f"  #{int(row['rank']):>2} {row['ticker']:<15}"
              f" Vol={row['volatility']:5.1f}%"
              f" Mom={row['momentum']:+6.1f}%"
              f" Yield={row['div_yield']:.1f}%"
              f" Score={row['score']:.0f}")
    print(f"{'='*65}\n")

    # ── Output JSON ──────────────────────────────────────────────────────────
    output = {
        "updated":        datetime.datetime.utcnow().isoformat() + "Z",
        "universe_count": universe_count,
        "stocks": [
            {
                "rank":       int(r['rank']),
                "ticker":     r['ticker'],
                "name":       r['name'],
                "sector":     r['sector'],
                "volatility": float(r['volatility']),
                "momentum":   float(r['momentum']),
                "div_yield":  float(r['div_yield']),
                "score":      int(r['score'])
            }
            for _, r in top10.iterrows()
        ]
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅  Saved → {OUTPUT_FILE}")
    print(f"    Universe screened: {universe_count} stocks")
    print(f"    Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

if __name__ == "__main__":
    run_screener()
