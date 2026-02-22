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
_TICKER_MAP = [
    ("AAK", "AAK.ST"),                              ("ABB", "ABB.ST"),
    ("AFRY", "AFRY.ST"),                            ("AQ Group", "AQ.ST"),
    ("AcadeMedia", "ACAD.ST"),                      ("Acast", "ACAST.ST"),
    ("Acrinova B", "ACRI-B.ST"),                    ("Actic Group", "ATIC.ST"),
    ("Active Biotech", "ACTI.ST"),                  ("AddLife", "ALIF-B.ST"),
    ("Addnode", "ANOD-B.ST"),                       ("Addtech", "ADDT-B.ST"),
    ("Alfa Laval", "ALFA.ST"),                      ("Alimak", "ALIG.ST"),
    ("Alleima", "ALLEI.ST"),                        ("Alligator Bioscience", "ATORX.ST"),
    ("Alligo", "ALLIGO-B.ST"),                      ("Alvotech SDB", "ALVO-SDB.ST"),
    ("Ambea", "AMBEA.ST"),                          ("Annehem Fastigheter", "ANNE-B.ST"),
    ("Anoto", "ANOT.ST"),                           ("Apotea", "APOTEA.ST"),
    ("Arctic Paper", "ARP.ST"),                     ("Arion Banki", "ARION-SDB.ST"),
    ("Arjo", "ARJO-B.ST"),                          ("Arla Plast", "ARPL.ST"),
    ("Ascelia Pharma", "ACE.ST"),                   ("Asker Healthcare", "ASKER.ST"),
    ("Asmodee", "ASMDEE-B.ST"),                     ("Assa Abloy", "ASSA-B.ST"),
    ("AstraZeneca", "AZN.ST"),                      ("Atlas Copco B", "ATCO-B.ST"),
    ("Atrium Ljungberg", "ATRLJ-B.ST"),             ("Attendo", "ATT.ST"),
    ("Autoliv", "ALIV-SDB.ST"),                     ("Avanza Bank", "AZA.ST"),
    ("Axfood", "AXFO.ST"),                          ("B3 Consulting", "B3.ST"),
    ("BE Group", "BEGR.ST"),                        ("BHG Group", "BHG.ST"),
    ("BICO Group", "BICO.ST"),                      ("BTS Group", "BTS-B.ST"),
    ("Bactiguard", "BACTI-B.ST"),                   ("Balco Group", "BALCO.ST"),
    ("Beijer Alma", "BEIA-B.ST"),                   ("Beijer Ref", "BEIJ-B.ST"),
    ("Bergman & Beving", "BERG-B.ST"),              ("Berner Industrier", "BERNER-B.ST"),
    ("Besqab", "BESQAB.ST"),                        ("Besqab Pref B", "BESQAB-PREF-B.ST"),
    ("Betsson", "BETS-B.ST"),                       ("Better Collective", "BETCO.ST"),
    ("Bilia", "BILI-A.ST"),                         ("Billerud", "BILL.ST"),
    ("BioArctic", "BIOA-B.ST"),                     ("BioGaia", "BIOG-B.ST"),
    ("Bioinvent", "BINV.ST"),                       ("Björn Borg", "BORG.ST"),
    ("Boliden", "BOL.ST"),                          ("Bonava B", "BONAV-B.ST"),
    ("Bonesupport", "BONEX.ST"),                    ("Bong Ljungdahl", "BONG.ST"),
    ("Boozt", "BOOZT.ST"),                          ("Boule Diagnostics", "BOUL.ST"),
    ("Bravida", "BRAV.ST"),                         ("Brinova Fastigheter", "BRIN-B.ST"),
    ("Bufab", "BUFAB.ST"),                          ("Bulten", "BULTEN.ST"),
    ("Bure Equity", "BURE.ST"),                     ("Byggmax", "BMAX.ST"),
    ("Byggmästare AJ Ahlström", "AJA-B.ST"),        ("C-RAD", "CRAD-B.ST"),
    ("CTEK", "CTEK.ST"),                            ("CTT Systems", "CTT.ST"),
    ("Camurus", "CAMX.ST"),                         ("Cantargia", "CANTA.ST"),
    ("Carasent", "CARA.ST"),                        ("Castellum", "CAST.ST"),
    ("Catella B", "CAT-B.ST"),                      ("Catena", "CATE.ST"),
    ("Catena Media", "CTM.ST"),                     ("Cavotec", "CCC.ST"),
    ("CellaVision", "CEVI.ST"),                     ("Cibus Nordic", "CIBUS.ST"),
    ("Cinclus Pharma", "CINPHA.ST"),                ("Cint Group", "CINT.ST"),
    ("Clas Ohlson", "CLAS-B.ST"),                   ("Cloetta", "CLA-B.ST"),
    ("CoinShares", "CS.ST"),                        ("Concejo B", "CNCJO-B.ST"),
    ("Coor Service Management", "COOR.ST"),         ("Corem Property B", "CORE-B.ST"),
    ("Corem Property D", "CORE-D.ST"),              ("Creades", "CRED-A.ST"),
    ("Dedicare", "DEDI.ST"),                        ("Diös Fastigheter", "DIOS.ST"),
    ("Dometic", "DOM.ST"),                          ("Duni", "DUNI.ST"),
    ("Duroc", "DURC-B.ST"),                         ("Dustin Group", "DUST.ST"),
    ("Dynavox Group", "DYVOX.ST"),                  ("EQL Pharma", "EQL.ST"),
    ("EQT", "EQT.ST"),                              ("Eastnine", "EAST.ST"),
    ("Egetis Therapeutics", "EGTX.ST"),             ("Elanders", "ELAN-B.ST"),
    ("Electrolux B", "ELUX-B.ST"),                  ("Electrolux Professional B", "EPRO-B.ST"),
    ("Elekta", "EKTA-B.ST"),                        ("Elon", "ELON.ST"),
    ("Eltel", "ELTEL.ST"),                          ("Embracer", "EMBRAC-B.ST"),
    ("Enad Global 7", "EG7.ST"),                    ("Enea", "ENEA.ST"),
    ("Engcon", "ENGCON-B.ST"),                      ("Eniro", "ENRO.ST"),
    ("Enity", "ENITY.ST"),                          ("Eolus", "EOLU-B.ST"),
    ("Ependion", "EPEN.ST"),                        ("Epiroc B", "EPI-B.ST"),
    ("Episurf Medical", "EPIS-B.ST"),               ("Ericsson B", "ERIC-B.ST"),
    ("Essity B", "ESSITY-B.ST"),                    ("Evolution", "EVO.ST"),
    ("FM Mattsson", "FMM-B.ST"),                    ("Fabege", "FABG.ST"),
    ("Fagerhult", "FAG.ST"),                        ("Fasadgruppen", "FG.ST"),
    ("Fast Balder", "BALD-B.ST"),                   ("Fastator", "FASTAT.ST"),
    ("Fastighetsbolag Emilshus Pref", "EMIL-PREF.ST"), ("Fastighetsbolaget Emilshus", "EMIL-B.ST"),
    ("Fastpartner A", "FPAR-A.ST"),                 ("Fastpartner D", "FPAR-D.ST"),
    ("Fenix Outdoor", "FOI-B.ST"),                  ("Ferronordic", "FNM.ST"),
    ("Fingerprint Cards", "FING-B.ST"),             ("Flerie", "FLERIE.ST"),
    ("Formpipe Software", "FPIP.ST"),               ("Fortinova", "FNOVA-B.ST"),
    ("G5 Entertainment", "G5EN.ST"),                ("Garo", "GARO.ST"),
    ("Genova Property", "GPG.ST"),                  ("Gentoo Media", "G2M.ST"),
    ("Getinge", "GETI-B.ST"),                       ("Green Landscaping", "GREEN.ST"),
    ("Gruvaktiebolaget Viscaria", "VISC.ST"),        ("Gränges", "GRNG.ST"),
    ("HAKI Safety B", "HAKI-B.ST"),                 ("HMS Networks", "HMS.ST"),
    ("Hacksaw", "HACK.ST"),                         ("Handelsbanken B", "SHB-B.ST"),
    ("Hansa Biopharma", "HNSA.ST"),                 ("Hanza", "HANZA.ST"),
    ("Havsfrun Investment", "HAV-B.ST"),             ("Heba", "HEBA-B.ST"),
    ("Hemnet", "HEM.ST"),                           ("Hennes & Mauritz", "HM-B.ST"),
    ("Hexagon", "HEXA-B.ST"),                       ("Hexatronic", "HTRO.ST"),
    ("Hexpol", "HPOL-B.ST"),                        ("Hoist Finance", "HOFI.ST"),
    ("Holmen B", "HOLM-B.ST"),                      ("Hufvudstaden A", "HUFV-A.ST"),
    ("Humana", "HUM.ST"),                           ("Humble Group", "HUMBLE.ST"),
    ("Husqvarna B", "HUSQ-B.ST"),                   ("IRLAB Therapeutics", "IRLAB-A.ST"),
    ("ITAB Shop Concept", "ITAB.ST"),               ("Image Systems", "IS.ST"),
    ("Immunovia", "IMMNOV.ST"),                     ("Industrivärden C", "INDU-C.ST"),
    ("Indutrade", "INDT.ST"),                       ("Infant Bacterial", "IBT-B.ST"),
    ("Infrea", "INFREA.ST"),                        ("Inission", "INISS-B.ST"),
    ("Instalco", "INSTAL.ST"),                      ("Intea Fastigheter B", "INTEA-B.ST"),
    ("Intea Fastigheter D", "INTEA-D.ST"),          ("International Petroleum", "IPCO.ST"),
    ("Intrum", "INTRUM.ST"),                        ("Investor B", "INVE-B.ST"),
    ("Invisio", "IVSO.ST"),                         ("Inwido", "INWI.ST"),
    ("Isofol Medical", "ISOFOL.ST"),                ("JM", "JM.ST"),
    ("John Mattson", "JOMA.ST"),                    ("K-Fast Holding", "KFAST-B.ST"),
    ("K2A", "K2A-B.ST"),                            ("K2A Knaust & Andersson Pref", "K2A-PREF.ST"),
    ("KDventures", "KDV-B.ST"),                     ("Kabe", "KABE-B.ST"),
    ("Karnell Group", "KARNEL-B.ST"),               ("Karnov", "KAR.ST"),
    ("Kinnevik B", "KINV-B.ST"),                    ("KlaraBo", "KLARA-B.ST"),
    ("KnowIT", "KNOW.ST"),                          ("Lagercrantz", "LAGR-B.ST"),
    ("Lammhults Design", "LAMM-B.ST"),              ("Latour", "LATO-B.ST"),
    ("Lifco", "LIFCO-B.ST"),                        ("Lime Technologies", "LIME.ST"),
    ("Linc", "LINC.ST"),                            ("Lindab", "LIAB.ST"),
    ("Logistea B", "LOGI-B.ST"),                    ("Loomis", "LOOMIS.ST"),
    ("Lundbergföretagen", "LUND-B.ST"),             ("Lundin Gold", "LUG.ST"),
    ("Lundin Mining", "LUMI.ST"),                   ("MEKO", "MEKO.ST"),
    ("Maha Capital", "MAHA-A.ST"),                  ("Malmbergs Elektriska", "MEAB-B.ST"),
    ("Mangold", "MANG.ST"),                         ("MedCap", "MCAP.ST"),
    ("Medicover", "MCOV-B.ST"),                     ("Medivir", "MVIR.ST"),
    ("Mendus", "IMMU.ST"),                          ("Meren Energy", "MER.ST"),
    ("Micro Systemation", "MSAB-B.ST"),             ("Midsona B", "MSON-B.ST"),
    ("Mildef Group", "MILDEF.ST"),                  ("Mips", "MIPS.ST"),
    ("Moberg Pharma", "MOB.ST"),                    ("Modern Times Group B", "MTG-B.ST"),
    ("Moment Group", "MOMENT.ST"),                  ("Momentum Group", "MMGR-B.ST"),
    ("Morrow Bank", "MORROW.ST"),                   ("Munters", "MTRS.ST"),
    ("Mycronic", "MYCR.ST"),                        ("NAXS", "NAXS.ST"),
    ("NCAB Group", "NCAB.ST"),                      ("NCC B", "NCC-B.ST"),
    ("NIBE Industrier", "NIBE-B.ST"),               ("NOBA Bank", "NOBA.ST"),
    ("NOTE", "NOTE.ST"),                            ("NP3 Fastigheter", "NP3.ST"),
    ("Nanologica", "NICA.ST"),                      ("Nederman", "NMAN.ST"),
    ("Nelly Group", "NELLY.ST"),                    ("Neobo Fastigheter", "NEOBO.ST"),
    ("Net Insight", "NETI-B.ST"),                   ("Netel Holding", "NETEL.ST"),
    ("New Wave", "NEWA-B.ST"),                      ("Nilörngruppen", "NIL-B.ST"),
    ("Nivika Fastigheter", "NIVI-B.ST"),             ("Nobia", "NOBI.ST"),
    ("Nokia", "NOKIA-SEK.ST"),                      ("Nolato", "NOLA-B.ST"),
    ("Nordea Bank", "NDA-SE.ST"),                   ("Nordisk Bergteknik", "NORB-B.ST"),
    ("Nordnet", "SAVE.ST"),                         ("Norion Bank", "NORION.ST"),
    ("Novotek", "NTEK-B.ST"),                       ("Nyfosa", "NYF.ST"),
    ("OEM International", "OEM-B.ST"),              ("Oncopeptides", "ONCO.ST"),
    ("Orexo", "ORX.ST"),                            ("Orrön Energy", "ORRON.ST"),
    ("Ovzon", "OVZON.ST"),                          ("PION Group", "PION-B.ST"),
    ("Pandox", "PNDX-B.ST"),                        ("Peab", "PEAB-B.ST"),
    ("Pierce Group", "PIERCE.ST"),                  ("Platzer Fastigheter", "PLAZ-B.ST"),
    ("PowerCell", "PCELL.ST"),                      ("Precise Biometrics", "PREC.ST"),
    ("Prevas", "PREV-B.ST"),                        ("Pricer", "PRIC-B.ST"),
    ("Prisma Properties", "PRISMA.ST"),             ("Proact IT", "PACT.ST"),
    ("ProfilGruppen", "PROF-B.ST"),                 ("Profoto", "PRFO.ST"),
    ("Q-Linea", "QLINEA.ST"),                       ("Qliro", "QLIRO.ST"),
    ("Railcare", "RAIL.ST"),                        ("Ratos B", "RATO-B.ST"),
    ("RaySearch Laboratories", "RAY-B.ST"),         ("Rejlers", "REJL-B.ST"),
    ("Revolutionrace", "RVRC.ST"),                  ("Rottneros", "RROS.ST"),
    ("Rusta", "RUSTA.ST"),                          ("Röko", "ROKO-B.ST"),
    ("SCA B", "SCA-B.ST"),                          ("SEB C", "SEB-C.ST"),
    ("SKF B", "SKF-B.ST"),                          ("SSAB B", "SSAB-B.ST"),
    ("Saab", "SAAB-B.ST"),                          ("Sagax B", "SAGA-B.ST"),
    ("Sagax D", "SAGA-D.ST"),                       ("Samhällsbyggnadsbolag B", "SBB-B.ST"),
    ("Samhällsbyggnadsbolag D", "SBB-D.ST"),        ("Sampo", "SAMPO-SDB.ST"),
    ("Sandvik", "SAND.ST"),                         ("Saniona", "SANION.ST"),
    ("Scandi Standard", "SCST.ST"),                 ("Scandic Hotels", "SHOT.ST"),
    ("Sdiptech", "SDIP-B.ST"),                      ("Seafire", "SEAF.ST"),
    ("Sectra", "SECT-B.ST"),                        ("Securitas", "SECU-B.ST"),
    ("Sedana Medical", "SEDANA.ST"),                ("Sensys Gatso", "SGG.ST"),
    ("Senzime", "SEZI.ST"),                         ("Sinch", "SINCH.ST"),
    ("SinterCast", "SINT.ST"),                      ("Sivers Semiconductors", "SIVE.ST"),
    ("Skanska", "SKA-B.ST"),                        ("SkiStar", "SKIS-B.ST"),
    ("Sleep Cycle", "SLEEP.ST"),                    ("Softronic", "SOF-B.ST"),
    ("Solid Försäkring", "SFAB.ST"),                ("Starbreeze B", "STAR-B.ST"),
    ("Stendörren Fastigheter", "STEF-B.ST"),        ("Stenhus Fastigheter", "SFAST.ST"),
    ("Stillfront", "SF.ST"),                        ("Stockwik Förvaltning", "STWK.ST"),
    ("Stora Enso A", "STE-A.ST"),                   ("Stora Enso R", "STE-R.ST"),
    ("Storskogen", "STOR-B.ST"),                    ("Studsvik", "SVIK.ST"),
    ("Sveafastigheter", "SVEAF.ST"),                ("Svedbergs Group", "SVED-B.ST"),
    ("Svolder B", "SVOL-B.ST"),                     ("Sweco B", "SWEC-B.ST"),
    ("Swedbank", "SWED-A.ST"),                      ("Swedish Logistic Property", "SLP-B.ST"),
    ("Swedish Orphan Biovitrum", "SOBI.ST"),        ("SynAct Pharma", "SYNACT.ST"),
    ("Synsam", "SYNSAM.ST"),                        ("Systemair", "SYSR.ST"),
    ("TF Bank", "TFBANK.ST"),                       ("Tele2 B", "TEL2-B.ST"),
    ("Telia Company", "TELIA.ST"),                  ("Thule", "THULE.ST"),
    ("TietoEVRY", "TIETOS.ST"),                     ("Tobii", "TOBII.ST"),
    ("Traction", "TRAC-B.ST"),                      ("TradeDoubler", "TRAD.ST"),
    ("Transtema", "TRANS.ST"),                      ("Traton", "8TRA.ST"),
    ("Trelleborg", "TREL-B.ST"),                    ("Trianon", "TRIAN-B.ST"),
    ("Troax Group", "TROAX.ST"),                    ("Truecaller", "TRUE-B.ST"),
    ("VBG Group", "VBG-B.ST"),                      ("VEF", "VEFAB.ST"),
    ("VNV Global", "VNV.ST"),                       ("Verisure", "VSURE.ST"),
    ("Vestum", "VESTUM.ST"),                        ("Viaplay B", "VPLAY-B.ST"),
    ("Vicore Pharma", "VICO.ST"),                   ("Vimian Group", "VIMIAN.ST"),
    ("Vitec Software", "VIT-B.ST"),                 ("Vitrolife", "VITR.ST"),
    ("Viva Wine", "VIVA.ST"),                       ("Vivesto", "VIVE.ST"),
    ("Volati", "VOLO.ST"),                          ("Volvo B", "VOLV-B.ST"),
    ("Volvo Car", "VOLCAR-B.ST"),                   ("Wall to Wall", "WTW-A.ST"),
    ("Wallenstam", "WALL-B.ST"),                    ("Wihlborgs Fastigheter", "WIHL.ST"),
    ("Wise Group", "WISE.ST"),                      ("Wästbygg", "WBGR-B.ST"),
    ("XANO Industri", "XANO-B.ST"),                 ("Xbrane Biopharma", "XBRANE.ST"),
    ("Xspray Pharma", "XSPRAY.ST"),                 ("Xvivo Perfusion", "XVIVO.ST"),
    ("Yubico", "YUBICO.ST"),                        ("eWork", "EWRK.ST"),
    ("mySafety", "SAFETY-B.ST"),                    ("Öresund", "ORES.ST"),
]

# Flat ticker list used by the screener loop
TICKERS = [t for _, t in _TICKER_MAP]

# Name lookup: ticker → company name
TICKER_NAMES = {t: n for n, t in _TICKER_MAP}

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
