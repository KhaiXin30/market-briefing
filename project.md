# Daily Pre-Market News & Movers Briefing Agent (Free-First) — PRD (README)

## 1) Summary
Build an automated agent that emails a **5-minute market briefing** at **7:00am ET**:
- **Weekdays (Mon–Fri):** Pre-Market Edition (news + movers)
- **Weekends (Sat/Sun):** Weekend Wrap (no premarket movers; weekend developments + week-ahead)

Focus:
- **US markets** + **US-traded ADRs / major foreign tickers in US hours** (e.g., TSM, ASML)
- Sectors: **Tech, Semiconductors, Oil & Gas, Retail**

Hard constraints:
- **Trustworthiness above all**
- **No hallucinations**
- **Citations required**
- **Plain language**; jargon must be explained inline **without maintaining a jargon YAML**

Free-first constraints:
- Prefer **free RSS + primary sources**
- Avoid paid subscriptions for V1
- Movers may require fallbacks due to limited free premarket data


---

## 2) Goals
- Deliver a consistent, easy-to-scan premarket briefing before the open.
- Surface what’s most market-relevant across multiple reputable sources (“balanced voices”).
- Explain **why** things are moving **only when supported by evidence**.
- Enforce **grounded summaries** with a strict validation gate.

## 3) Non-Goals (V1)
- Trade recommendations or “buy/sell” signals.
- Real-time intraday alerts.
- Full paywalled content extraction.
- Perfect “top market movers” coverage if free data cannot support it.

---

## 4) User Stories
- As a user, I want a **5-minute email** each morning so I can understand market context quickly.
- As a user, I want **top gainers/losers** with **confirmed catalysts** (or explicitly “unknown” if not confirmed).
- As a user, I want **citations** and **no made-up facts**.
- As a user, I want the language to be **simple**, and any technical term to be explained **in brackets**.

---

## 5) Output Format (5-minute read)
Target: **350–550 words** total.

### Weekdays (Pre-Market)
1) **Overnight / Must-Know (Top 5)** — 5 bullets  
2) **Sector Snapshot** — 1 bullet each:
   - Tech
   - Semiconductors
   - Oil & Gas
   - Retail
3) **Movers (US + ADRs)** — Top 5 gainers + Top 5 losers  
4) **Today’s Calendar** — max 5 items (econ releases, earnings, major events)

### Weekends (Weekend Wrap)
1) Top 5 weekend developments  
2) Sector snapshot  
3) Week-ahead calendar (earnings + macro risks)

---

## 6) Free-First Data Sources

### 6.1 Source trust model
Use:
- **Primary sources (highest trust)**: SEC filings, Fed, BLS, BEA, EIA, company IR press releases.
- **Reputable publishers with accessible feeds** (free access where possible).

Block:
- Any domain not in allowlist.
- Low-quality aggregators, rumor sites, forums.

### 6.2 Initial allowlist (free-first)
Start with domains you can reliably access without subscriptions, plus primary sources.

Primary / official:
- sec.gov (EDGAR)
- federalreserve.gov
- bls.gov
- bea.gov
- eia.gov
- treasury.gov (optional)

Company IR (add as needed):
- investor.apple.com (or Apple IR domain)
- investor.nvidia.com (or NVIDIA IR domain)
- ir.amd.com (or AMD IR domain)
- investor.tsmc.com
- asml.com (investor relations pages)
- (plus major oil/retail IR domains you care about)

Reputable publishers (availability varies by region/time):
- cnbc.com
- apnews.com (if RSS available in your region)
- other reputable outlets that provide RSS and accessible article text

> Note: Some publishers restrict scraping or provide only short snippets. That’s okay for V1: if full text is unavailable, you either (a) skip it or (b) summarize only the snippet and clearly cite it.

### 6.3 Starter RSS feed list (example)
You will likely expand/adjust these based on what’s accessible.

Put these URLs in config (example only; test each feed in your environment):
```txt
CNBC Markets RSS:
https://www.cnbc.com/id/100003114/device/rss/rss.html

CNBC Technology RSS:
https://www.cnbc.com/id/19854910/device/rss/rss.html

CNBC Retail RSS:
https://www.cnbc.com/id/10000115/device/rss/rss.html

US EIA - Today in Energy RSS (primary source):
https://www.eia.gov/rss/todayinenergy.xml

SEC - EDGAR RSS (primary source; choose the most useful feed endpoint for your use case):
https://www.sec.gov/Archives/edgar/usgaap.rss.xml
