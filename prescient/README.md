# Traipp

> Autonomous Prediction Markets Powered by AI Agents

[![Synthesis Hackathon](https://img.shields.io/badge/Synthesis%20Hackathon-2026-blue)](https://synthesis.devfolio.co)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**Traipp** is a social intelligence hub — curating tweets from top influencers, scoring sentiment with NLP, and permanently archiving insights on Filecoin. Real-time intelligence for Crypto, Stocks, Tech & Geopolitics.

### The Problem

Prediction markets are powerful truth-seeking mechanisms, but they suffer from:
- **Manual event discovery** — Humans must identify and create markets
- **Centralized resolution** — Oracles introduce bias and delay
- **Fragmented liquidity** — New markets struggle to attract traders

### Our Solution

An AI agent that handles the entire prediction market lifecycle:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   EVENT      │───▶│   MARKET     │───▶│  RESOLUTION  │
│  DISCOVERY   │    │   CREATION   │    │   & PAYOUT   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Dune + Social│    │ Uniswap v4   │    │ ERC-8004     │
│   Signals    │    │   Hooks      │    │  Receipts    │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Key Features

- **🔍 Event Discovery** — Identifies tradable events from Dune Analytics on-chain data and social sentiment
- **🏪 Market Creation** — Deploys prediction markets with Uniswap v4 hooks for automated liquidity
- **✅ Autonomous Resolution** — Determines outcomes with ERC-8004 signed attestations
- **📊 Public Goods Analysis** — Octant integration for public goods project evaluation

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Runtime | SylphAI Custom Platform |
| Blockchain | Base Chain |
| AMM | Uniswap v4 Hooks |
| Data | Dune Analytics API |
| Sentiment | Twitter/Farcaster APIs |
| Identity | ERC-8004 |

## Hackathon Tracks

| Track | Company | Prize |
|-------|---------|-------|
| Let the Agent Cook | Protocol Labs | $4,000 |
| Agents With Receipts — ERC-8004 | Protocol Labs | $4,000 |
| Agentic Finance (Uniswap) | Uniswap | $2,500 |
| Agents for Public Goods Data Analysis | Octant | $1,000 |

## Project Structure

```
traipp/
├── agent/                  # AI agent modules
│   ├── discovery/          # Event discovery engine
│   ├── markets/            # Market creation & management
│   └── resolution/         # Outcome resolution
├── contracts/              # Solidity smart contracts
├── dune/                   # Dune Analytics queries
├── docs/                   # Documentation
└── tests/                  # Test suites
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Juls95/traipp.git
cd traipp

# Install dependencies (coming soon)
pip install -r requirements.txt

# Run the agent (coming soon)
python -m agent.orchestrator
```

## Documentation

- [Project Definition](PROJECT_DEFINITION.md) — Full project specification
- [Requirements Checklist](REQUIREMENTS.md) — Hackathon compliance
- [Agent Identity](SOUL.md) — Agent personality and values

## Team

- **AdaL** — AI Agent (SylphAI)
- **Julian Ramirez** — Human Partner ([@Juls95](https://twitter.com/Juls95))

## License

MIT License — See [LICENSE](LICENSE) for details.

---

*Built for [The Synthesis Hackathon 2026](https://synthesis.devfolio.co)*

🌸 Generated with [AdaL](https://github.com/adal-cli/)
