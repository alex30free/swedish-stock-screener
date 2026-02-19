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
# FULL SWEDISH STOCK UNIVERSE
# Large Cap (~1B EUR+), Mid Cap (150M-1B EUR), Small Cap (<150M EUR)
# All listed on Nasdaq OMX Stockholm
# Format: Yahoo Finance ticker with .ST suffix
# ─────────────────────────────────────────────────────────────────────────────

TICKERS = [
    # ── LARGE CAP ────────────────────────────────────────────────────────────
    "ABB.ST",       # ABB Ltd
    "ALFA.ST",      # Alfa Laval
    "ASSA-B.ST",    # Assa Abloy B
    "ATCO-A.ST",    # Atlas Copco A
    "ATCO-B.ST",    # Atlas Copco B
    "AZN.ST",       # AstraZeneca
    "BOL.ST",       # Boliden
    "ERIC-B.ST",    # Ericsson B
    "ESSITY-B.ST",  # Essity B
    "EVO.ST",       # Evolution Gaming
    "EQT.ST",       # EQT AB
    "GETI-B.ST",    # Getinge B
    "HM-B.ST",      # H&M B
    "HEXA-B.ST",    # Hexagon B
    "INDU-C.ST",    # Industrivärden C
    "INVE-B.ST",    # Investor B
    "KINV-B.ST",    # Kinnevik B
    "LATO-B.ST",    # Latour B
    "NDA-SE.ST",    # Nordea Bank
    "NIBE-B.ST",    # NIBE Industrier B
    "SAND.ST",      # Sandvik
    "SCA-B.ST",     # SCA B
    "SEB-A.ST",     # SEB A
    "SHB-A.ST",     # Handelsbanken A
    "SKF-B.ST",     # SKF B
    "SWED-A.ST",    # Swedbank A
    "TELIA.ST",     # Telia Company
    "VOLV-B.ST",    # Volvo B
    "SAAB-B.ST",    # Saab B
    "ELUX-B.ST",    # Electrolux B
    "SSAB-A.ST",    # SSAB A
    "SSAB-B.ST",    # SSAB B
    "ALIV-SDB.ST",  # Aliv SDB
    "EMBRAC-B.ST",  # Embracer Group B

    # ── MID CAP ──────────────────────────────────────────────────────────────
    "AAK.ST",       # AAK AB
    "BALD-B.ST",    # Balders B
    "BEIA-B.ST",    # Beijer Alma B
    "BEIJ-B.ST",    # Beijer Ref B
    "BUFAB.ST",     # Bufab
    "CAST.ST",      # Castellum
    "CLAS-B.ST",    # Clas Ohlson B
    "COOR.ST",      # Coor Service
    "DIOS.ST",      # Diös Fastigheter
    "DUNI.ST",      # Duni AB
    "EKTA-B.ST",    # Elekta B
    "FABG.ST",      # Fabege
    "GARO.ST",      # Garo AB
    "HOLM-B.ST",    # Holmen B
    "HUFV-A.ST",    # Hufvudstaden A
    "HUSQ-B.ST",    # Husqvarna B
    "ICA.ST",       # ICA Gruppen
    "INTRUM.ST",    # Intrum
    "JM.ST",        # JM AB
    "LIFCO-B.ST",   # Lifco B
    "LUND-B.ST",    # Lundbergföretagen B
    "NENT-B.ST",    # NENT Group B
    "NOLA-B.ST",    # Nolato B
    "NOTE.ST",      # NOTE AB
    "PEAB-B.ST",    # Peab B
    "PNDX-B.ST",    # Pandox B
    "PRIC-B.ST",    # Pricer B
    "SAGAX-B.ST",   # Sagax B
    "SECU-B.ST",    # Securitas B
    "SKISTAR-B.ST", # SkiStar B
    "SWEC-B.ST",    # Sweco B
    "SYSR.ST",      # Systemair
    "THULE.ST",     # Thule Group
    "TREL-B.ST",    # Trelleborg B
    "VBG-B.ST",     # VBG Group B
    "VITR.ST",      # Vitrolife
    "WALL-B.ST",    # Wallenstam B
    "WIHL.ST",      # Wihlborgs
    "XANO-B.ST",    # Xano Industri B
    "BURE.ST",      # Bure Equity
    "CATE.ST",      # Catena
    "ENEA.ST",      # Enea AB
    "HEXPOL-B.ST",  # Hexpol B
    "NEWA-B.ST",    # New Wave B
    "NP3.ST",       # NP3 Fastigheter
    "TROAX.ST",     # Troax Group
    "BRG-B.ST",     # Bergman & Beving B
    "DORO.ST",      # Doro AB
    "KABE-B.ST",    # Kabe Group B
    "MEKO.ST",      # Mekonomen
    "OEM-B.ST",     # OEM International B
    "RATO-B.ST",    # Ratos B
    "SCST.ST",      # Scandi Standard
    "SDIP-B.ST",    # Sdiptech B

    # ── SMALL CAP ────────────────────────────────────────────────────────────
    "ADDV-B.ST",    # Addvise Group B
    "ALLIGO-B.ST",  # Alligo B
    "AMBEA.ST",     # Ambea AB
    "ARJO-B.ST",    # Arjo B
    "AXFO.ST",      # Axfood
    "BEWI.ST",      # BEWi ASA
    "BOOL.ST",      # Boolean
    "BRAV.ST",      # Bravida Holding
    "CDON.ST",      # CDON AB
    "CRED-A.ST",    # Creades A
    "ELAN-B.ST",    # Elanders B
    "ELTEL.ST",     # Eltel AB
    "EWRK.ST",      # eWork Group
    "FING-B.ST",    # Fingerprint Cards B
    "HANSA.ST",     # Hansa Biopharma
    "HEBA-B.ST",    # Heba Fastighets B
    "HTRO.ST",      # Hoist Finance
    "INDT.ST",      # Indutrade
    "ITAB.ST",      # ITAB Shop Concept
    "KNOW-IT.ST",   # Know IT
    "LAMM-B.ST",    # Lammhults Design B
    "MIPS.ST",      # MIPS AB
    "MSAB-B.ST",    # MSAB B
    "NAXS.ST",      # NAXS Nordic
    "NEWA-A.ST",    # New Wave A
    "NOLA-A.ST",    # Nolato A
    "ONCO.ST",      # Oncopeptides
    "OREX.ST",      # Orexo AB
    "PLAZ-B.ST",    # Platzer Fastigheter B
    "PNDX-A.ST",    # Pandox A
    "PROB.ST",      # Probi AB
    "PROF-B.ST",    # Profilgruppen B
    "RAIL.ST",      # Railcare Group
    "SAGA-A.ST",    # Sagax A
    "SENS.ST",      # Sensys Gatso Group
    "SIVERS.ST",    # Sivers Semiconductors
    "SOBI.ST",      # Swedish Orphan Biovitrum
    "SOLT.ST",      # Soltech Energy Sweden
    "SSM.ST",       # SSM Holding
    "TRAD.ST",      # Tradedoubler
    "VEFAB.ST",     # VEF AB
    "VIGS.ST",      # Vigs
    "VPLAY-B.ST",   # Viaplay B
    "WISE.ST",      # Wise Group
    "XANO-B.ST",    # Xano Industri B
    "YUBICO.ST",    # Yubico AB
    "NTEK.ST",      # Nordic Tech
    "FPAR-A.ST",    # Fastpartner A
    "LOGI-B.ST",    # Logistea B
    "FLAT-B.ST",    # Flat Capital B
    "PRIC-A.ST",    # Pricer A
    "SKIS-B.ST",    # Skistar B
]

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
    return info.get('shortName') or info.get('longName') or ticker

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCREENER
# ─────────────────────────────────────────────────────────────────────────────

def run_screener():
    print(f"\n{'='*65}")
    print(f"  Van Vliet Low-Vol Screener — OMX Stockholm")
    print(f"  Universe: {len(TICKERS)} tickers (Large + Mid + Small Cap)")
    print(f"  Running at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}\n")

    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=400)

    records = []
    skipped = 0

    for i, ticker in enumerate(TICKERS):
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