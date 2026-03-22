"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Calendar,
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  Filter,
} from "lucide-react";

interface HistoryEntry {
  date: string;
  group: string;
  tweet_count: number;
  avg_score: number;
  overview_score: number;
  sentiment: string;
  summary: string;
  coin_cards: { symbol: string; mentions: number; virality_score: number }[];
}

interface HistoryData {
  history: HistoryEntry[];
  period: string;
  group_filter: string;
}

const GROUPS = [
  { slug: "", label: "All Groups" },
  { slug: "CryptoTweets", label: "Crypto" },
  { slug: "StockTweets", label: "Stocks" },
  { slug: "TechTweets", label: "Tech" },
  { slug: "GeopoliticsTweets", label: "Geopolitics" },
];

function SentimentIcon({ sentiment }: { sentiment: string }) {
  if (sentiment === "bullish") return <TrendingUp size={14} className="text-emerald-600" />;
  if (sentiment === "bearish") return <TrendingDown size={14} className="text-red-500" />;
  return <Activity size={14} className="text-amber-600" />;
}

export default function HistoryPage() {
  const [data, setData] = useState<HistoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [groupFilter, setGroupFilter] = useState("");
  const [periodFilter, setPeriodFilter] = useState("week");

  const loadHistory = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (groupFilter) params.set("group", groupFilter);
    params.set("period", periodFilter);

    api.request<HistoryData>(`/api/history?${params}`)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadHistory(); }, [groupFilter, periodFilter]);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">History</h1>
        <p className="text-[#666] mt-1">Historical analysis of tweet groups over time</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-[#999]" />
          <span className="text-sm text-[#666]">Group:</span>
        </div>
        <div className="flex gap-1.5 bg-white border border-[#e5e5e5] rounded-lg p-1">
          {GROUPS.map((g) => (
            <button
              key={g.slug}
              onClick={() => setGroupFilter(g.slug)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                groupFilter === g.slug ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>

        <div className="flex gap-1.5 bg-white border border-[#e5e5e5] rounded-lg p-1 ml-auto">
          {["week", "month", "year"].map((p) => (
            <button
              key={p}
              onClick={() => setPeriodFilter(p)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition capitalize ${
                periodFilter === p ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="py-20 text-center text-sm text-[#999]">
          <Brain size={32} className="mx-auto text-[#ccc] mb-3 animate-pulse" />
          Loading history...
        </div>
      ) : !data?.history.length ? (
        <div className="py-20 text-center">
          <Calendar size={40} className="mx-auto text-[#ccc] mb-4" />
          <p className="text-sm text-[#999]">No historical data available yet</p>
          <p className="text-xs text-[#ccc] mt-1">Data will appear after the first daily collection runs</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.history.map((entry, i) => (
            <div key={`${entry.date}-${entry.group}-${i}`}
              className="bg-white rounded-xl border border-[#e5e5e5] p-5 hover:shadow-sm transition">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-[#999]" />
                    <span className="text-sm font-semibold text-[#0a0a0a]">{entry.date}</span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[#f5f5f5] text-[#666] border border-[#e5e5e5]">
                    {entry.group}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <SentimentIcon sentiment={entry.sentiment} />
                    <span className="text-xs font-medium capitalize">{entry.sentiment}</span>
                  </div>
                  <span className={`text-sm font-bold px-2.5 py-0.5 rounded-lg border ${
                    entry.overview_score >= 7 ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                    entry.overview_score >= 4 ? "bg-amber-50 text-amber-700 border-amber-200" :
                    "bg-red-50 text-red-700 border-red-200"
                  }`}>
                    {entry.overview_score}/10
                  </span>
                </div>
              </div>

              <p className="text-sm text-[#444] leading-relaxed mb-3">{entry.summary}</p>

              <div className="flex items-center gap-4 text-xs text-[#999]">
                <span>{entry.tweet_count} tweets analyzed</span>
                <span>Avg score: {(entry.avg_score * 100).toFixed(0)}%</span>
                {entry.coin_cards.length > 0 && (
                  <span className="flex items-center gap-1">
                    Top coins: {entry.coin_cards.slice(0, 3).map(c => c.symbol).join(", ")}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
