# market-briefing-agent

Daily pre-market briefing agent (RSS-first) with Postgres storage and SendGrid email delivery.

## What it does
- Ingests RSS feeds into Postgres.
- Builds a weekday or weekend briefing with citations.
- Sends via SendGrid (or prints to stdout with `--no-send`).

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
python src/main.py --no-send
```

## Config
RSS sources and allowlist are in `config/sources.yaml`. Add more feeds and allowlisted domains as you expand coverage.
Portfolio tracking keywords live in `config/sources.yaml` under `portfolio`.

## GitHub Actions
The workflow runs daily at 11:00 UTC (7:00am ET during standard time). Set these repo secrets:
- `DATABASE_URL`
- `SENDGRID_API_KEY`
- `FROM_EMAIL`
- `TO_EMAILS`
- `FMP_API_KEY` (optional, for movers)
- `HF_TOKEN` (optional, for Llama summaries via Hugging Face Router)
- `HF_BASE_URL` (optional, override HF base URL)
- `HF_MODEL` (optional, override HF model id)
- `VERIFY_LINKS` (optional, set to `1` to drop items with inaccessible links)
- `OPENFIGI_API_KEY` (optional, for OpenFIGI fallback)

## Notes
- Movers are optional and rely on free RSS sources. Add them to `movers_feeds` when available.
- FMP movers use the `FMP_API_KEY` env var and show price/percent moves only (no catalysts).
- Portfolio premarket quotes use FMP `stable/quote` and require `FMP_API_KEY`.
- Llama summaries use Hugging Face Router with `HF_TOKEN`. Defaults to `meta-llama/Llama-3.2-1B-Instruct:novita`.
- Mover company blurbs use Yahoo Finance (with rate-limited requests) and fall back to FMP profile if available.
- If FMP fails, the system falls back to OpenFIGI (if available) for basic company info.
- Link verification adds extra HTTP requests and can slow ingestion; enable only if needed.
- The agent only summarizes RSS titles/snippets for trustworthiness.
