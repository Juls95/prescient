# DOCS_REPLICATION_PLAN.md

**Date:** 2026-03-20  
**POC:** Julian Ramirez  
**TL;DR:** `docsReplicate/` is now git-ignored, and this document defines how to replicate similar market-analysis PDFs: what each document likely contains, where to source equivalent data, and how to automate production.

---

## 1) Git Safety Status

- ✅ `docsReplicate/` is ignored via root `.gitignore`.
- Verification result:
  - `.gitignore` → untracked file pending commit
  - `docsReplicate/` → ignored (`!! docsReplicate/`)

### Current `.gitignore`
```gitignore
# Local large/source documents
docsReplicate/
```

---

## 2) What the Files Contain (Inferred Content Map)

Based on file titles + extracted representative samples, the documents are recurring **macro + tactical trade briefings** with a consistent structure:

1. **Macro context**
   - SP500 regime (range, topping, breakdown risk, relief rebound)
   - Volatility regime (VIX behavior)
   - Event risk (Fed/Powell/CPI/PPI/NVDA/geopolitics like Hormuz)

2. **Theme / sector focus**
   - Rotation between growth vs defensive sectors
   - Frequent references to energy, uranium/lithium, metals, index ETFs

3. **Actionable setups**
   - Directional bias (long/short/neutral)
   - Entry/activation levels
   - Stop-loss / invalidation levels
   - Profit targets
   - Sometimes hedge overlays / re-entries

4. **Risk handling**
   - Per-trade risk budgeting (often small % risk guidance)
   - Break-even migration after first objective
   - Caution in high-volatility ranges

5. **Execution framing**
   - “Wait for confirmation” when indecisive
   - Scenario-based outcomes (bull trap vs continuation)

---

## 3) File-by-File Theme Index (Title-Derived)

> Note: This section maps likely emphasis per file from titles. A full deterministic parser pass can be added later for exact extraction per PDF.

- **3 ACCIONES RÁPIDAS...** → Short-term bullish opportunities, fast setups
- **A PUNTO DE ROMPER SOPORTES...** → Support-breakdown risk, bearish trigger watch
- **ANÁLISIS DEL MERCADO...** → Broad market state + active decisions
- **ANÁLISIS PREVIO A LA FED...** → Pre-Fed positioning + “explosive sectors”
- **ATAQUES EN EL ESTRECHO DE HORMUZ...** → Geopolitical shock, energy/defensive response
- **CADA VEZ TIENE MENOS ASPECTO DE BARRIDA...** → Less likely fakeout, trend confirmation watch
- **COMENTARIOS DEL MERCADO, COBERTURAS...** → Commentary + hedges + re-entries
- **EL MERCADO ES UNA LOCURA...** → High-noise volatility with selective trades
- **EL MERCADO ESTÁ INDECISO A LA ESPERA DE NVDA** → Event-wait regime
- **EL MERCADO ESTÁ LENTO...** → Low momentum with isolated opportunities
- **EL MERCADO RECHAZA A NVDA... VIX...** → Earnings reaction + volatility confirmation
- **EL MERCADO SE ANTICIPA A NVDA...** → Pre-earnings positioning
- **EL MERCADO VA ALINEÁNDOSE...** → Directional alignment phase
- **El SP500 sigue en rango...** → Range continuation + tactical setups
- **EL TECHO ESTÁ CASI TERMINADO...** → Top formation thesis
- **EL TRUMP-PUMP FRACASA... TENEMOS TECHO** → Narrative rally failure, bearish confirmation
- **ENORME GAP BAJISTA EN BOLSA...** → Gap-down risk protocol
- **FUERTE VOLATILIDAD... BARRIDA O CAÍDA REAL** → Distinguish shakeout vs true breakdown
- **GUERRA EN IRÁN... REBOTAN...** → Conflict-driven rebound dynamics
- **INICIA LA SEMANA DE LA FED...** → Fed week volatility plan
- **INICIA SEMANA... NUEVAS OPERACIONES** → Weekly setup batch
- **LUEGO DE UNA TORMENTA... ¿LLEGA LA CALMA?** → Post-shock normalization check
- **MERCADO LATERAL... IMPULSO NATURAL...** → Sideways with directional drift
- **NUEVAS OPERACIONES Y UN ANUNCIO IMPORTANTE** → New setups + catalyst
- **NUEVO ATAQUE DE LOS OSOS...** → Bearish pressure escalation
- **PERÍODO DE ALTA VOLATILIDAD...** → Volatility regime playbook
- **REBOTES DE ALIVIO...** → Relief rally setups
- **SP500 EN ESTADO DE LOCURA VOLÁTIL...** → Extreme volatility response steps
- **TRUMP TACO! ¿QUÉ ESPERAR AHORA?** → Policy/news-driven scenario update
- **UNA COBERTURA RÁPIDA Y COMENTARIOS** → Fast hedge tactics
- **VIENE POWELL!!...** → Powell event strategy
- **techo_!.pdf** → Likely concise “top” thesis snapshot

---

## 4) Where to Get Equivalent Information (Data Source Stack)

## A) Market Prices / OHLCV
- **Primary (free/fast MVP):** Yahoo Finance (`yfinance`)
- **Higher quality / production:** Polygon, TwelveData, Alpha Vantage, Tiingo
- **Assets to track:** SPY, QQQ, IWM, XLK, XLE, XLF, XLU, URA, LIT, GLD, SLV, BTC proxies

## B) Volatility / Risk Proxies
- **VIX:** CBOE feeds or market-data vendors
- **DXY / rates proxies:** FRED + market data APIs
- **Crypto risk proxies (if needed):** BTC volatility, dominance metrics, perp funding

## C) Macro Calendar / Event Risk
- **Fed/FOMC schedule:** Federal Reserve website
- **CPI/PPI/NFP:** BLS / BEA / FRED calendar integration
- **Earnings dates (e.g., NVDA):** Nasdaq calendar, vendor APIs

## D) Geopolitical & Headline Triggers
- **News APIs:** NewsAPI, GDELT, FinancialModelingPrep news, major wire summaries
- **Use case:** Flag narrative shifts (Hormuz, sanctions, policy headlines)

## E) Optional Sentiment / Positioning
- Put/Call ratios, breadth indicators, volatility term structure, ETF flows

---

## 5) Template to Produce Similar Reports

Each report should have:

1. **Executive Bias (3-5 bullets)**
2. **Macro Dashboard**
   - SP500 regime, VIX regime, key events this week
3. **Sector Rotation**
   - Leaders/laggards, relative strength notes
4. **Trade Ideas Table**
   - Ticker | Direction | Entry | Stop | Targets | Risk% | Status
5. **Hedge/Contingency**
   - If-then actions for downside/upside invalidations
6. **Operational Notes**
   - Position sizing rules, max concurrent risk
7. **Appendix**
   - Levels, charts, and data timestamps

---

## 6) Minimal Reproducible Pipeline (MVP)

## Step 1 — Ingest
- Pull daily + intraday data for watchlist and indices.
- Pull event calendar (FOMC, CPI/PPI, major earnings).

## Step 2 — Compute Signals
- Trend/range classifiers (ATR, moving averages, range width)
- Volatility flags (VIX higher-lows, volatility expansion)
- Relative strength by sector ETF

## Step 3 — Generate Candidate Setups
- Rule-driven long/short candidates
- Auto-calculate stop/targets and R-multiple
- Position sizing from fixed risk budget

## Step 4 — Human-in-the-loop Review
- Accept/reject candidates
- Add narrative and scenario commentary

## Step 5 — Render Report
- Markdown template → PDF via Pandoc/WeasyPrint/ReportLab
- Save machine-readable JSON alongside PDF

## Step 6 — Archive & Feedback
- Store outcome metrics (win rate, MAE/MFE, expectancy)
- Improve rules from realized performance

---

## 7) Suggested Tech Stack

- **Python packages:** `pandas`, `numpy`, `yfinance`, `pydantic`, `jinja2`, `matplotlib`/`plotly`
- **Report generation:** `pandoc` or `weasyprint` or `reportlab`
- **Orchestration:** scheduled job (cron/GitHub Actions/local runner)
- **Storage:** local `data/` + `reports/` + `signals/` JSON artifacts

---

## 8) Suggested Project Structure

```text
market-reports/
  data/
  signals/
  reports/
  templates/
    daily_report.md.j2
  src/
    ingest.py
    events.py
    signals.py
    risk.py
    render.py
    pipeline.py
  config/
    watchlist.yaml
    risk.yaml
```

---

## 9) Next Practical Actions

1. Build a first `watchlist.yaml` (index + sector + macro proxies).
2. Implement `ingest.py` + `signals.py` for 1D timeframe.
3. Define one report template in markdown.
4. Generate first automated PDF from yesterday’s data.
5. Compare output quality against `docsReplicate/` style and iterate.

---

## 10) Caveats / Quality Controls

- These documents appear to include **discretionary judgment**, not only pure quant rules.
- Keep **human override** capability for event-heavy days.
- Avoid overfitting narrative indicators; log every decision reason.
- Track realized outcomes to enforce objective improvement over time.