# market-briefing-agent

This repository builds a **daily market briefing agent** that delivers a **5-minute read pre-market email** focused on **US stocks + ADRs/major foreign tickers trading in US hours** (e.g., TSM, ASML), with emphasis on **Tech, Semiconductors, Oil & Gas, and Retail** everyday at 7am ET.

The agent runs an end-to-end pipeline that:
- **Ingests news from free-first RSS + primary sources** (government releases, company IR, etc.) using a strict **source allowlist**
- **Extracts and deduplicates** articles by clustering similar headlines into story groups
- Generates a structured briefing with:
  - **Top 5 overnight market stories**
  - **Sector snapshots** (Tech / Semis / Oil & Gas / Retail)
  - **Premarket portfolio data** (pre-market pricing/changes for the tracked watchlist)
  - **Daily movers** (top **gainers and losers**) with catalysts **only when supported by allowlisted sources**
- Enforces **no hallucinations** by requiring **citations for every claim** and storing **evidence spans** (verbatim supporting text) that are checked by a **validation gate** before anything is sent
- Outputs the briefing in **plain, easy-to-understand language**, avoiding jargon where possible and explaining technical terms inline when needed

The system is designed to be **trustworthy-first**:
- If a claim cannot be supported by retrieved sources, it is omitted or explicitly labeled as **“not confirmed by allowlisted sources yet.”**
- A **validation gate** blocks sending if citations/evidence are missing or sources are not approved.

## What it does
- Ingests RSS feeds into Postgres.
- Builds a weekday or weekend briefing with citations.
- Sends via SendGrid (or prints to stdout with `--no-send`).
- Adds a portfolio watch section plus optional premarket quotes.

## Setup
1) Start Postgres locally:
```bash
docker-compose up -d
```

2) Create a `.env` from the example:
```bash
cp .env.example .env
```

3) Install dependencies:
```bash
pip install -r requirements.txt
```

4) Run once (no email):
```bash
python -m src.main --no-send
```

## Supabase (Hosted Postgres)
If you want GitHub Actions to run without a local database, use Supabase:
1) Create a project at https://supabase.com
2) Settings → Database → Connection string → URI
3) Set GitHub Actions secret `DATABASE_URL` to that URI (URL-encode your password if it has special characters).

## Config
RSS sources and allowlist are in `config/sources.yaml`. Add more feeds and allowlisted domains as you expand coverage.
Portfolio tracking keywords live in `config/sources.yaml` under `portfolio`.

## GitHub Actions
The workflow runs daily at 11:00 and 12:00 UTC (covers 7:00am ET across DST). Set these repo secrets:
- `DATABASE_URL`
- `SENDGRID_API_KEY`
- `FROM_EMAIL`
- `TO_EMAILS`
- `FMP_API_KEY` (optional, for movers)
- `HF_TOKEN` (optional, for Llama summaries via Hugging Face Router)
- `HF_BASE_URL` (optional, override HF base URL)
- `HF_MODEL` (optional, override HF model id)
- `VERIFY_LINKS` (optional, set to `1` to drop items with inaccessible links)

## Notes
- Movers are optional and rely on free RSS sources. Add them to `movers_feeds` when available.
- FMP movers use the `FMP_API_KEY` env var and show price/percent moves only (no catalysts).
- Portfolio premarket quotes use FMP `stable/quote` and require `FMP_API_KEY`.
- Llama summaries use Hugging Face Router with `HF_TOKEN`. Defaults to `meta-llama/Llama-3.2-1B-Instruct:novita`.
- Mover company blurbs use FMP profiles first, then Wikipedia (company name), then Yahoo Finance.
- Link verification adds extra HTTP requests and can slow ingestion; enable only if needed.
- The agent only summarizes RSS titles/snippets for trustworthiness.
