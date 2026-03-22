# NEXT_STEPS.md — Prioritized Task Queue

_Last updated: 2026-03-22_

## Completed This Session ✅
- [x] Intelligence page: Default collapse all tweet groups
- [x] Suggest page: Added "Contact @juls95" via Twitter DM/mention buttons
- [x] Pipeline page: Removed manual triggers, added API cost info + next run estimates
- [x] Filecoin CID confidentiality: 🔒 Internal badges on Intelligence + Suggest pages
- [x] X API cost audit: Disabled legacy Search API, right-sized limits for budget
- [x] Tweet collection: 58 tweets fetched from all 4 groups, stored in SQLite + Filecoin
- [x] Methodology page: Added "Crypto Card Percentage" section explaining scoring
- [x] Landing page: Complete rewrite matching actual app functionality
- [x] Updated MEMORY.md and NEXT_STEPS.md

## Current Priorities (Next Session)
1. [ ] **Railway deployment**: Create Dockerfile, configure env vars, deploy backend + frontend
2. [ ] **Fix Lighthouse Kavach encryption**: Either regenerate key or configure Kavach auth for encrypted uploads
3. [ ] **End-to-end test on production**: Sign-in → Dashboard → Intelligence → Pipeline → Suggest flow
4. [ ] **History page verification**: Ensure date filters work with the new group-based sentiment data
5. [ ] **Budget replenishment**: Add more X API credits before next collection cycle ($0.09 remaining)

## Secondary Priorities
6. [ ] Add more curated accounts to groups (user suggestions)
7. [ ] Implement coin-specific insights from group tweets (extract BTC/ETH mentions from CryptoTweets)
8. [ ] Storage explorer page: Wire to display all Filecoin CIDs from master index
9. [ ] Add rate limiting middleware to protect public API endpoints
10. [ ] Backend test coverage for sentiment pipeline, Filecoin upload, and NLP scoring

## Infrastructure
11. [ ] Fix Python packaging (`pyproject.toml`) for clean installs
12. [ ] Configure production database (PostgreSQL) for multi-user concurrency
13. [ ] Set up CI/CD pipeline (GitHub Actions)
14. [ ] CORS lockdown (remove `allow_origins=["*"]` for production)

## Submission Pipeline
15. [ ] Maintain full `conversationLog`
16. [ ] Prepare submission metadata (honest tools/skills/resources)
17. [ ] Publish Moltbook post
18. [ ] Publish final project submission

## Key Metrics
- **X API Budget**: ~$0.09 remaining (was $0.50 before last run)
- **Total tweets collected**: 58 (15 Crypto, 14 Stocks, 15 Tech, 14 Geopolitics)
- **Filecoin CIDs**: 8 total (4 groups × 2 runs)
- **Cost per cycle**: ~$0.41

## Session-End Checklist
- [x] Update `MEMORY.md` with durable decisions/architecture
- [x] Update `NEXT_STEPS.md` with priorities
- [ ] Append today's entry to `SESSION_LOG.md`
- [ ] Generate resume prompt for next session

## Suggested Resume Prompt
> Read NEXT_STEPS.md, then focus on Priority #1: Railway deployment. Create a Dockerfile for the backend (FastAPI + SQLite + .env), configure frontend for production build, and deploy both services. Budget: $0.09 X API credits remaining — do NOT trigger collection without adding credits first.
