# Project Definition: Prescient Information Hub
**Created:** 2026-03-22 | **Hackathon:** Synthesis 2026

---

## TL;DR
An information hub that curates, analyzes, and stores tweets from verified accounts across 4 domains (Crypto, Stocks, Tech, Geopolitics). Uses X API for collection, Lighthouse+Kavach for encrypted Filecoin storage, and NLP for pattern extraction. Users get daily sentiment scores, summaries, and historical tracking.

---

## Prize Categories Targeted

| Prize | Amount | How We Qualify |
|-------|--------|----------------|
| **Agents for Public Goods Data Analysis** | $1,000 | NLP extracts patterns (sentiment, keywords, signals) from messy social data that humans can't scale to process |
| **Agents for Public Goods Data Collection** | $1,000 | Gathers signals from curated accounts to assess information quality and relevance |
| **Filecoin Best Use Case** | $2,000 | Encrypted tweet storage on mainnet via Lighthouse SDK + Kavach, with agent-driven autonomous collection |

**Total Eligible:** Up to $4,000

---

## Core Workflow

```
1. User registers → Profile stored on Filecoin
2. Daily job: Fetch tweets from curated account groups (max 50/group)
3. Encrypt tweets with Kavach → Upload to Filecoin
4. NLP analysis: score (1-10), sentiment, keywords, summary
5. User views Dashboard, History, Info pages
6. User suggests new accounts via "Suggest Person" form
```

---

## Curated Account Groups

| Group | Accounts | Selection Criteria |
|-------|----------|-------------------|
| **CryptoTweets** | @Zeneca, @intocryptoverse, @IncomeSharks, @Nebraskangooner | High-quality analysis, consistent posting, strong engagement |
| **StockTweets** | @arny_trezzi, @amitisinvesting | Market insights, technical analysis |
| **TechTweets** | @andrewchen, @skominers, @jason | VC/startup ecosystem, emerging tech |
| **GeopoliticsTweets** | @TuckerCarlson, @DonMiami3 | Alternative geopolitical analysis |

**Selection Methodology:** Quality of information, posting frequency, engagement metrics, topic consistency.

---

## Data Model per Tweet

```json
{
  "tweet_id": "string",
  "user_handle": "string",
  "user_name": "string",
  "content": "string",
  "likes": 0,
  "comments": 0,
  "reposts": 0,
  "user_followers": 0,
  "user_created_at": "date",
  "tweeted_at": "date",
  "group": "CryptoTweets|StockTweets|TechTweets|GeopoliticsTweets"
}
```

**Storage:** Encrypted JSON on Filecoin (Lighthouse + Kavach), CID indexed in SQLite.

---

## NLP Analysis Output (per group, per day)

```json
{
  "date": "2026-03-22",
  "group": "CryptoTweets",
  "overview_score": 7.5,
  "sentiment": "bullish|neutral|bearish",
  "summary": "Bitcoin dominance rising, institutional interest growing...",
  "keywords": ["bitcoin", "etf", "institutional", "adoption"],
  "tweets_analyzed": 42,
  "accounts_tweeted": 3,
  "top_topics": ["market analysis", "trading signals", "macro"],
  "filecoin_cid": "Qm..."
}
```

**Scoring Logic (1-10):**
- Engagement quality (likes/reposts ratio)
- Information density (keywords, substance vs noise)
- Sentiment consistency across accounts
- Recency and relevance to current events

---

## Top 10 Crypto Cards (Dune Analytics Integration)

Dashboard displays small cards for top 10 cryptocurrencies (excluding stablecoins) with:

| Card Field | Source |
|------------|--------|
| **Token Name** | Dune Analytics |
| **Market Cap** | Dune Analytics |
| **Current Value** | Dune Analytics |
| **Mentions** | Count from group tweets (e.g., "BTC" mentioned 20 times) |
| **Virality Score** | Derived from sentiment + engagement (higher = more buzz) |

**Example Card:**
```
┌─────────────────────────┐
│ Bitcoin (BTC)           │
│ Market Cap: $1.2T       │
│ Value: $67,450          │
│ Mentions: 47            │
│ Virality: ████████░░ 82 │
└─────────────────────────┘
```

**Virality Score Calculation:**
- Base: mention count normalized (0-40 points)
- Sentiment multiplier: bullish +20%, bearish +10%, neutral 0%
- Engagement boost: avg likes/reposts per mention (0-20 points)
- Scale: 0-100

---

## Frontend Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | All 4 groups displayed with today's score, sentiment, summary, tweet count. Click group for detail. **+ Top 10 Crypto Cards** (market cap, value, mentions, virality from Dune). |
| **History** | Filter by group + date range (week/month/year). View historical analysis with charts. |
| **Info** | Technical methodology: scoring algorithm, NLP approach, data sources, encryption proof. |
| **Suggest Person** | Form to submit @handle + group + reason for consideration. Stored to Filecoin. |

---

## 2-Hour MVP Scope

### What We Already Have ✅
- X API v2 integration (SentimentAnalyzer)
- Filecoin storage via Lighthouse SDK
- SQLite + FastAPI backend
- Next.js 15 frontend with Clerk auth
- NLP analysis engine (InsightEngine)
- Dashboard components
- **Dune Analytics API** (already integrated for market data)

### What We Need to Build (2 hours) 🚧

| Task | Time | Priority |
|------|------|----------|
| 1. Switch X API from keyword search → user timeline fetch | 20 min | P0 |
| 2. Define curated account groups in config | 10 min | P0 |
| 3. Add Kavach encryption before Filecoin upload | 15 min | P0 |
| 4. Update NLP scoring to 1-10 scale + group summaries | 20 min | P0 |
| 5. Build Top 10 Crypto Cards (Dune data + mentions + virality) | 15 min | P0 |
| 6. Create History page with date filtering | 20 min | P1 |
| 7. Create Info page with methodology | 15 min | P1 |
| 8. Create Suggest Person form + storage | 10 min | P1 |
| 9. Update Dashboard for 4 groups view | 10 min | P0 |

**Total Estimated:** ~2 hours 15 min

---

## Technical Implementation Notes

### X API Change: User Timeline
**Current:** `GET /2/tweets/search/recent` (keyword-based)
**New:** `GET /2/users/:id/tweets` (user timeline)

Requires:
- User ID lookup: `GET /2/users/by/username/:username`
- Batch requests for each account in group
- Rate limit: 15 requests/15 min per endpoint (Basic tier)

### Encryption: Lighthouse + Kavach
```python
from lighthouseweb3 import Lighthouse

# Encrypt before upload
lh = Lighthouse(token=api_key)
encrypted = lh.uploadEncrypted(file_path, public_key)
# Returns CID, requires private key to decrypt
```

### Historic Data Persistence
- Daily analysis stored as `analysis_{group}_{date}.json` on Filecoin
- SQLite indexes: group, date, CID
- Frontend fetches from Filecoin via gateway for history view

---

## Eligibility Checklist

- [x] Agent extracts patterns from messy public data (NLP on tweets)
- [x] Agent gathers signals about real-world impact (curated accounts)
- [x] Filecoin mainnet storage (Lighthouse SDK already integrated)
- [x] Encrypted storage (Kavach to be added)
- [x] Real autonomous agent (scheduled daily collection)
- [x] Production-ready frontend
- [x] User authentication and data ownership

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| X API rate limits | Stagger requests, cache user IDs, max 50 tweets/day per group |
| X API credits depleted | Fallback to mock data for demo, highlight architecture |
| Kavach setup complexity | Lighthouse SDK handles encryption in 2 lines of code |
| 2-hour timeline tight | Prioritize P0 items, ship working MVP before polish |

---

## Next Steps

1. **Immediate:** Update `SentimentAnalyzer` to fetch from user timelines
2. **Then:** Wire Kavach encryption into storage pipeline
3. **Then:** Build frontend pages (History, Info, Suggest)
4. **Final:** Test E2E flow, deploy to Railway

---

*This document confirms the pivot from "Crypto Prediction Markets" to "Information Hub" while reusing 80% of existing infrastructure.*
