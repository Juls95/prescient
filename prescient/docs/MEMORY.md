# MEMORY.md — Long-Term Insights & Lessons

## Project Context

### Synthesis Hackathon 2026
- **Dates**: March 13-23, 2026
- **Goal**: Autonomous trading agent based on on-chain data
- **Track Focus**: "Autonomous Trading Agent" (Base, $5,000 prize pool)

---

## Key Learnings

### Technical Insights

1. **ERC-8004 Registration**
   - On-chain identity is minted as NFT (Agent ID)
   - Registration must go through Synthesis API, not just on-chain
   - Previous on-chain registration without Synthesis API record = no participant access
   - Solution: Re-register through `/register` endpoint

2. **Self-Custody Requirement**
   - All team members must transfer to self-custody before publishing
   - Two-step process: `/transfer/init` → `/transfer/confirm`
   - Requires wallet address (no private keys needed)
   - Token expires in 15 minutes

3. **Submission Metadata Honesty**
   - Judges cross-reference `skills`, `tools`, `helpfulResources` with code
   - Only list what was actually used — inflated lists hurt credibility
   - `conversationLog` is judged and "matters more than README"

### Workflow Insights

1. **Path Verification**
   - Never guess paths — always glob/ls first
   - Reading non-existent files is a hard error
   - Line numbers required for edits

2. **Tool Output Format**
   - ONE step per response
   - Wait for observation before next action
   - Never predict results

---

## Human Preferences

### Julian Ramirez
- **Background**: Builder
- **Crypto Experience**: Yes (familiar with on-chain concepts)
- **AI Agent Experience**: No (this is new territory)
- **Coding Comfort**: 7/10
- **Goal**: Automated trading based on on-chain data
- **Communication**: Prefers direct, concise explanations

---

## Common Pitfalls to Avoid

1. **Hallucinating paths** → Always verify before reading
2. **Listing unused skills/tools** → Be honest in submission metadata
3. **Skipping conversation log** → Document all collaboration
4. **Forgetting self-custody** → Complete early to avoid blockers
5. **Last-minute publishing** → Get everything right before publish

---

## Next Steps (Prioritized)

1. [ ] Explore trading strategies and on-chain data sources
2. [ ] Set up GitHub repository
3. [ ] Complete self-custody transfer
4. [ ] Create project draft on Synthesis
5. [ ] Build and test trading agent
6. [ ] Write conversation log
7. [ ] Post on Moltbook
8. [ ] Publish submission

---

*Last updated: 2026-03-18*
