"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  MessageSquare,
  Users,
  ExternalLink,
  Flame,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";

// ── Types ───────────────────────────────────────────────────────────

interface CoinCard {
  symbol: string;
  mentions: number;
  virality_score: number;
  current_price: number;
  market_cap: number;
  price_change_24h: number;
}

interface GroupAnalysis {
  overview_score: number;
  sentiment: string;
  summary: string;
  keywords: string[];
  tweets_analyzed: number;
  accounts_tweeted: number;
  coin_cards: { symbol: string; mentions: number; virality_score: number }[];
  avg_engagement: number;
  total_likes: number;
  total_comments: number;
  total_reposts: number;
}

interface GroupData {
  name: string;
  slug: string;
  description: string;
  accounts: string[];
  analysis: GroupAnalysis;
  collection_count: number;
  total_tweets: number;
  latest_score: number;
  latest_fetched: string;
  filecoin_cids: string[];
}

interface DashboardData {
  groups: GroupData[];
  coin_cards: CoinCard[];
  total_groups: number;
}

// ── Components ──────────────────────────────────────────────────────

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 7 ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
    score >= 4 ? "bg-amber-50 text-amber-700 border-amber-200" :
    "bg-red-50 text-red-700 border-red-200";
  return (
    <span className={`text-lg font-bold px-3 py-1 rounded-lg border ${color}`}>
      {score}/10
    </span>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const config = {
    bullish: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: TrendingUp },
    bearish: { color: "bg-red-50 text-red-700 border-red-200", icon: TrendingDown },
    neutral: { color: "bg-amber-50 text-amber-700 border-amber-200", icon: Activity },
  };
  const { color, icon: Icon } = config[sentiment as keyof typeof config] || config.neutral;
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${color}`}>
      <Icon size={12} /> {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
    </span>
  );
}

function ViralityBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-[#f0f0f0] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-amber-400 to-red-500 rounded-full transition-all"
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className="text-xs font-mono text-[#666] w-8">{score}</span>
    </div>
  );
}

function CoinCardComponent({ coin }: { coin: CoinCard }) {
  const priceColor = coin.price_change_24h >= 0 ? "text-emerald-600" : "text-red-500";
  return (
    <div className="bg-white rounded-xl border border-[#e5e5e5] p-4 hover:shadow-sm transition">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#f5f5f5] flex items-center justify-center text-xs font-bold">
            {coin.symbol.slice(0, 3)}
          </div>
          <span className="text-sm font-semibold text-[#0a0a0a]">{coin.symbol}</span>
        </div>
        <span className={`text-xs font-medium ${priceColor}`}>
          {coin.price_change_24h >= 0 ? "+" : ""}{(coin.price_change_24h ?? 0).toFixed(1)}%
        </span>
      </div>
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-[#999]">Price</span>
          <span className="font-medium text-[#0a0a0a]">
            ${coin.current_price >= 1 ? coin.current_price.toLocaleString(undefined, {maximumFractionDigits: 2}) : coin.current_price.toFixed(6)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#999]">Market Cap</span>
          <span className="font-medium text-[#0a0a0a]">
            ${coin.market_cap >= 1e9 ? (coin.market_cap / 1e9).toFixed(1) + "B" : (coin.market_cap / 1e6).toFixed(0) + "M"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#999]">Mentions</span>
          <span className="font-medium text-[#7c3aed]">{coin.mentions}</span>
        </div>
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[#999]">Virality</span>
          </div>
          <ViralityBar score={coin.virality_score} />
        </div>
      </div>
    </div>
  );
}

function GroupCard({ group }: { group: GroupData }) {
  const a = group.analysis;
  return (
    <Link href={`/intelligence?group=${group.slug}`}>
      <div className="bg-white rounded-xl border border-[#e5e5e5] p-6 hover:shadow-md hover:border-[#7c3aed]/30 transition cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-[#0a0a0a]">{group.name}</h3>
            <p className="text-xs text-[#999] mt-0.5">{group.description}</p>
          </div>
          <ScoreBadge score={a.overview_score} />
        </div>

        <div className="flex items-center gap-2 mb-4">
          <SentimentBadge sentiment={a.sentiment} />
          <span className="text-xs text-[#999]">
            {a.tweets_analyzed} tweets · {a.accounts_tweeted} accounts
          </span>
        </div>

        <p className="text-sm text-[#444] leading-relaxed mb-4 line-clamp-2">{a.summary}</p>

        {/* Accounts */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {group.accounts.map((acc) => (
            <span key={acc} className="text-[10px] px-2 py-0.5 rounded-full bg-[#f5f5f5] text-[#666] border border-[#e5e5e5]">
              @{acc}
            </span>
          ))}
        </div>

        {/* Keywords */}
        {a.keywords && a.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {a.keywords.slice(0, 5).map((kw) => (
              <span key={kw} className="text-[10px] px-2 py-0.5 rounded bg-[#7c3aed]/10 text-[#7c3aed]">
                {kw}
              </span>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-[#f0f0f0]">
          <div className="flex items-center gap-3 text-xs text-[#999]">
            <span>{group.collection_count} collections</span>
            {group.filecoin_cids.length > 0 && (
              <span className="flex items-center gap-1 text-[#7c3aed]">
                <ExternalLink size={10} /> Filecoin
              </span>
            )}
          </div>
          <ChevronRight size={14} className="text-[#ccc]" />
        </div>
      </div>
    </Link>
  );
}

// ── Main Page ───────────────────────────────────────────────────────

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.request<DashboardData>("/api/groups")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-[#999]">
        <Brain size={32} className="mx-auto text-[#ccc] mb-3 animate-pulse" />
        Loading dashboard...
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Dashboard</h1>
        <p className="text-[#666] mt-1">Information Hub — curated tweet groups with AI analysis</p>
      </div>

      {/* Tweet Groups */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Users size={16} className="text-[#7c3aed]" /> Tweet Groups
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.groups.map((group) => (
            <GroupCard key={group.slug} group={group} />
          ))}
        </div>
      </div>

      {/* Top 10 Crypto Cards */}
      {data?.coin_cards && data.coin_cards.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
            <Flame size={16} className="text-[#7c3aed]" /> Top Coins by Mentions
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {data.coin_cards.map((coin) => (
              <CoinCardComponent key={coin.symbol} coin={coin} />
            ))}
          </div>
        </div>
      )}

      {!data?.groups.length && (
        <div className="py-20 text-center">
          <MessageSquare size={40} className="mx-auto text-[#ccc] mb-4" />
          <p className="text-sm text-[#999] mb-2">No data collected yet</p>
          <Link href="/pipeline" className="text-xs text-[#7c3aed] hover:underline">
            Trigger data collection →
          </Link>
        </div>
      )}
    </div>
  );
}
