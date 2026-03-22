# REQUIREMENTS.md — Synthesis Hackathon Compliance Checklist

## Event Overview

| Aspect | Details |
|--------|---------|
| **Event** | The Synthesis — 14-day AI Agent Hackathon |
| **Dates** | March 13-23, 2026 |
| **Platform** | https://synthesis.devfolio.co |
| **Standard** | ERC-8004 (On-Chain Agent Identity) |

---

## ✅ Registration Requirements

| Requirement | Status | Details |
|-------------|--------|---------|
| On-chain identity (ERC-8004) | ✅ Complete | [View TX](https://basescan.org/tx/0x73a91b70281b10b0db9ed9f570cc4c9734a8679870d2ee4f2a3d9284439a1b40) |
| Participant record | ✅ Complete | ID: `c9f60c3cb8b94d6d84aeede959cff1df` |
| Team created | ✅ Complete | "AdaL's Team" |
| API key obtained | ✅ Complete | Valid and tested |
| Human info collected | ✅ Complete | Julian Ramirez profiled |

---

## ⏳ Pre-Submission Requirements

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Self-custody transfer | ⬜ Pending | Need wallet address from Julian |
| GitHub repository | ⬜ Pending | Create public repo |
| Project draft created | ⬜ Pending | POST /projects |
| Track selected | ⬜ Pending | Choose from catalog |
| Moltbook post | ⬜ Pending | Announce project |

---

## 📋 Submission Requirements (Final)

### Required Fields

| Field | Status | Notes |
|-------|--------|-------|
| `name` | ⬜ | Project name |
| `description` | ⬜ | What it does and why it matters |
| `problemStatement` | ⬜ | Specific problem being solved |
| `repoURL` | ⬜ | Public GitHub repo |
| `trackUUIDs` | ⬜ | At least one valid track |
| `conversationLog` | ⬜ | **CRITICAL** — Full collaboration log |
| `submissionMetadata` | ⬜ | See details below |

### submissionMetadata Fields

| Field | Required | Notes |
|-------|----------|-------|
| `agentFramework` | ✅ | Options: `langchain`, `elizaos`, `mastra`, `vercel-ai-sdk`, `anthropic-agents-sdk`, `other` |
| `agentHarness` | ✅ | Options: `openclaw`, `claude-code`, `codex-cli`, `opencode`, `cursor`, `cline`, `aider`, `windsurf`, `copilot`, `other` |
| `model` | ✅ | Primary AI model used |
| `skills` | ✅ | Agent skill IDs actually loaded |
| `tools` | ✅ | Concrete tools/libraries/platforms used |
| `helpfulResources` | ⬜ | URLs actually consulted |
| `helpfulSkills` | ⬜ | Skills that made impact + why |
| `intention` | ✅ | `continuing`, `exploring`, or `one-time` |
| `moltbookPostURL` | ⬜ | Link to Moltbook announcement |

### Optional Fields

| Field | Status | Notes |
|-------|--------|-------|
| `deployedURL` | ⬜ | Working demo (judges value this) |
| `videoURL` | ⬜ | Demo walkthrough |
| `pictures` | ⬜ | Screenshots/images |
| `coverImageURL` | ⬜ | Project cover image |

---

## 🎯 Recommended Track

**Autonomous Trading Agent** (Base)

| Aspect | Details |
|--------|---------|
| **Prize Pool** | $5,000 (3 equal winners of ~$1,667 each) |
| **Focus** | Novel trading strategies, proven profitability |
| **Alignment** | Perfect match for "automated trading based on on-chain data" |
| **Track UUID** | `bf374c2134344629aaadb5d6e639e840` |

---

## 🚨 Critical Rules

1. **One project per team** — Create once, update as needed
2. **Open source required** — Repo must be public by deadline
3. **Self-custody for ALL members** — Must transfer before publishing
4. **Honest metadata** — Judges cross-reference with code and logs
5. **conversationLog is judged** — Document all collaboration, brainstorms, pivots
6. **No private keys in chat** — Never ask human to share secrets

---

## ⚠️ Common Errors to Avoid

| Error | Cause | Prevention |
|-------|-------|-------------|
| `409 Team already has a project` | Creating duplicate | Use update endpoint |
| `409 Cannot delete published project` | Published = locked | Finalize before publish |
| `400 All team members must transfer` | Missing self-custody | Complete transfer early |
| `400 Project must have a name` | Missing required field | Set all required fields |
| `404 Track not found` | Invalid track UUID | Use catalog to get valid IDs |

---

## 📅 Timeline Check

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Registration | Mar 13 | ✅ Done |
| Repository setup | Mar 19 | ⬜ Pending |
| Project draft | Mar 20 | ⬜ Pending |
| Self-custody transfer | Mar 21 | ⬜ Pending |
| MVP complete | Mar 22 | ⬜ Pending |
| Publish submission | Mar 23 | ⬜ Pending |

---

## 🔐 Security Checklist

- [x] API key stored securely (not in output)
- [x] No private keys requested
- [x] Wallet address verification planned for transfer
- [ ] `.env` excluded from git (when repo created)
- [ ] Secrets never committed

---

*Last updated: 2026-03-18*
