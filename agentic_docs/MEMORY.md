# MEMORY.md — Long-Term Insights & Lessons

## Project Context

### Synthesis Hackathon 2026
- **Dates**: March 13-23, 2026
- **Goal**: Prescient Information Hub — social intelligence platform
- **Pivot**: From autonomous trading agent → curated social intelligence hub with Filecoin storage
- **Track Focus**: "Let the Agent Cook" (Protocol Labs) + "Agents With Receipts — ERC-8004"

---

## Architecture (Final State)

### Backend (Python/FastAPI)
- `prescient/api/main.py` — FastAPI app with 14+ endpoints
- `prescient/agent/groups.py` — 4 curated tweet groups (Crypto, Stocks, Tech, Geopolitics), 11 accounts
- `prescient/agent/discovery/sentiment.py` — X API v2 user timeline fetcher + NLP keyword scorer
- `prescient/agent/analysis/nlp_insights.py` — Advanced scoring (1-10 overview, 0-100 virality, signal classification)
- `prescient/agent/data/scheduler.py` — Automated daily collection pipeline
- `prescient/agent/storage/filecoin.py` — Lighthouse SDK uploads to IPFS/Filecoin

### Frontend (Next.js 15 + Tailwind)
- Landing page: Hero, Features, HowItWorks, TechStack, Groups, FAQ, CTA, Footer
- App pages: Dashboard, Intelligence, History, Pipeline, Methodology, Suggest & Contact, Storage, Settings
- Auth: Clerk (social + email login)

### Data Flow
1. Scheduler triggers `job_fetch_group_tweets()` daily
2. For each group: lookup user IDs → fetch timelines → NLP scoring → store SQLite → upload Filecoin
3. Frontend reads from `/api/x-data`, `/api/groups`, `/api/insights/:symbol`

---

## Key Learnings

### X API v2 (Critical)
- **New pricing model**: Pay-per-use ($0.005/tweet, $0.010/user lookup) — no more fixed subscriptions
- **Budget management**: With $0.50 remaining, a full cycle costs ~$0.41 (60 tweets + 11 lookups)
- **Legacy Search API disabled**: `job_fetch_sentiment` was burning credits with broad keyword search — now returns "skipped"
- **Encrypted uploads**: Lighthouse Kavach encryption returns 401 — plain `uploadBlob` works fine
- **User ID caching**: `_user_id_cache` prevents redundant $0.010 lookups across groups

### Filecoin/Lighthouse
- API key: `...4e7c1f86` — works for plain uploads, Kavach encryption needs separate auth
- All 4 groups have verified CIDs on IPFS
- CIDs stored in SQLite `sentiment_data.filecoin_cid` column
- Internal-only: CIDs marked with 🔒 badge in UI

### Scoring System
- **Crypto Card %**: `(sentiment_score + 1) * 50` → 0-100% (keyword ratio of bullish vs bearish)
- **Overview Score (1-10)**: Sentiment(4pts) + Signal Clarity(2pts) + Engagement(2pts) + Volume(2pts)
- **Virality (0-100)**: Mention volume(40%) + Engagement(20%) × Sentiment multiplier

### Curated Accounts (11 total)
- **Crypto**: @Zeneca, @intocryptoverse, @IncomeSharks, @Nebraskangooner
- **Stocks**: @arny_trezzi, @amitisinvesting
- **Tech**: @andrewchen, @skominers, @jason
- **Geopolitics**: @TuckerCarlson, @DonMiami3

---

## Human Preferences

### Julian Ramirez (@juls95)
- **Background**: Builder
- **Crypto Experience**: Yes
- **AI Agent Experience**: Learning
- **Coding Comfort**: 7/10
- **Communication**: Prefers direct, concise explanations
- **Budget-conscious**: Very careful with API costs

---

## Common Pitfalls to Avoid

1. **Never run legacy Search API** → Disabled, use group timelines only
2. **Budget before API calls** → Calculate exact cost before hitting X API
3. **User ID cache** → Server restart clears cache, adds $0.11 for lookups
4. **Lighthouse encryption** → Kavach auth broken, use plain uploadBlob
5. **MAX_TWEETS_PER_GROUP=15** → Don't increase without budget check

---

*Last updated: 2026-03-22*
