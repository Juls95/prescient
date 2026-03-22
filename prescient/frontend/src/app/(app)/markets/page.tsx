"use client";

import { useEffect, useState } from "react";
import { api, MarketDetail as MarketType, SentimentEntry, MarketsResponse } from "@/lib/api";
import { Search, ThumbsUp, ThumbsDown, ExternalLink, Clock, Users, DollarSign } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";

type FilterStatus = "all" | "active" | "resolved" | "expired";

function VoteButton({ label, icon: Icon, active, color, onClick }: {
  label: string; icon: React.ElementType; active: boolean; color: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition border ${
        active
          ? `${color} text-white border-transparent`
          : "bg-white text-[#666] border-[#e5e5e5] hover:border-[#ccc]"
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );
}

function MarketDetailView({ market, onBack }: { market: MarketType; onBack: () => void }) {
  const [sentiment, setSentiment] = useState<SentimentEntry[]>([]);
  const [voted, setVoted] = useState<"YES" | "NO" | null>(null);
  const [voting, setVoting] = useState(false);
  const [probability, setProbability] = useState<{ yes: number; no: number; recommendation: string; dune: string; sentiment: string } | null>(null);
  const [votes, setVotes] = useState<{ YES: number; NO: number; total_votes: number } | null>(null);
  const [loadingProb, setLoadingProb] = useState(true);

  useEffect(() => {
    // Load sentiment, probability, and vote data in parallel
    Promise.allSettled([
      api.getSentiment(),
      api.getMarketProbability(market.market_id),
      api.getMarketVotes(market.market_id),
    ]).then(([sentResult, probResult, votesResult]) => {
      if (sentResult.status === "fulfilled") setSentiment(sentResult.value.sentiment);
      if (probResult.status === "fulfilled") {
        const p = probResult.value;
        setProbability({
          yes: p.yes_probability,
          no: p.no_probability,
          recommendation: p.recommendation,
          dune: p.components.dune.detail,
          sentiment: p.components.sentiment.detail,
        });
      }
      if (votesResult.status === "fulfilled") {
        setVotes({ YES: votesResult.value.YES, NO: votesResult.value.NO, total_votes: votesResult.value.total_votes });
      }
      setLoadingProb(false);
    });
  }, [market.market_id]);

  const handleVote = async (vote: "YES" | "NO") => {
    setVoting(true);
    try {
      const result = await api.castVote(market.market_id, vote);
      setVoted(vote);
      // Refresh vote counts
      const fresh = await api.getMarketVotes(market.market_id);
      setVotes({ YES: fresh.YES, NO: fresh.NO, total_votes: fresh.total_votes });
    } catch { /* noop */ }
    setVoting(false);
  };

  const prob = probability?.yes ?? market.yes_probability ?? 0.5;
  const pieData = [
    { name: "Yes", value: prob },
    { name: "No", value: 1 - prob },
  ];
  const COLORS = ["#7c3aed", "#e5e5e5"];

  // Time remaining calculation
  const deadline = market.deadline ? new Date(market.deadline) : null;
  const now = new Date();
  const hoursRemaining = deadline ? Math.max(0, (deadline.getTime() - now.getTime()) / (1000 * 60 * 60)) : null;
  const timeLabel = hoursRemaining !== null
    ? hoursRemaining < 1 ? `${Math.round(hoursRemaining * 60)}m remaining`
    : hoursRemaining < 24 ? `${hoursRemaining.toFixed(1)}h remaining`
    : `${Math.round(hoursRemaining / 24)}d remaining`
    : "TBD";

  return (
    <div>
      <button onClick={onBack} className="text-sm text-[#7c3aed] hover:underline mb-4">← Back to markets</button>

      <div className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
            market.status === "active" ? "bg-emerald-50 text-emerald-700" :
            market.status === "resolved" ? "bg-blue-50 text-blue-700" : "bg-gray-50 text-gray-600"
          }`}>{market.status}</span>
          {probability && (
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
              probability.recommendation === "YES" ? "bg-emerald-50 text-emerald-700" :
              probability.recommendation === "NO" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"
            }`}>
              AI: {probability.recommendation}
            </span>
          )}
          {hoursRemaining !== null && hoursRemaining < 24 && (
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-orange-50 text-orange-700">
              ⏰ {timeLabel}
            </span>
          )}
        </div>

        <h2 className="text-xl font-bold text-[#0a0a0a] tracking-tight mb-2">{market.question}</h2>
        <p className="text-sm text-[#666] mb-6">{market.resolution_criteria}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Probability chart */}
          <div className="flex flex-col items-center">
            <div className="w-40 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} dataKey="value" strokeWidth={0}>
                    {pieData.map((_, idx) => <Cell key={idx} fill={COLORS[idx]} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <p className="text-2xl font-bold text-[#7c3aed] mt-2">{(prob * 100).toFixed(1)}%</p>
            <p className="text-xs text-[#999]">Yes probability</p>
          </div>

          {/* Market stats */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <DollarSign size={16} className="text-[#999]" />
              <div>
                <p className="text-sm font-medium text-[#0a0a0a]">${(market.total_volume || 0).toLocaleString()}</p>
                <p className="text-xs text-[#999]">Total Volume</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Users size={16} className="text-[#999]" />
              <div>
                <p className="text-sm font-medium text-[#0a0a0a]">{votes?.total_votes ?? market.participants ?? 0}</p>
                <p className="text-xs text-[#999]">Votes ({votes?.YES ?? 0} Yes / {votes?.NO ?? 0} No)</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock size={16} className="text-[#999]" />
              <div>
                <p className="text-sm font-medium text-[#0a0a0a]">{timeLabel}</p>
                <p className="text-xs text-[#999]">{deadline ? deadline.toLocaleString() : "No deadline"}</p>
              </div>
            </div>
          </div>

          {/* AI Analysis breakdown */}
          <div>
            <h3 className="text-sm font-medium text-[#0a0a0a] mb-3">AI Analysis</h3>
            {loadingProb ? (
              <p className="text-sm text-[#999]">Calculating...</p>
            ) : probability ? (
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-[#666]">Dune (60%)</span>
                    <span className="font-medium text-[#0a0a0a]">{(probability.yes * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 bg-[#f0f0f0] rounded-full overflow-hidden">
                    <div className="h-full bg-[#7c3aed] rounded-full" style={{ width: `${probability.yes * 100}%` }} />
                  </div>
                  <p className="text-[10px] text-[#999] mt-0.5">{probability.dune}</p>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-[#666]">Sentiment (40%)</span>
                    <span className="font-medium text-[#0a0a0a]">{((probability.yes - 0.1) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 bg-[#f0f0f0] rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.max(0, (probability.yes - 0.1)) * 100}%` }} />
                  </div>
                  <p className="text-[10px] text-[#999] mt-0.5">{probability.sentiment}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-[#0a0a0a] mb-3">Sentiment</h3>
                {sentiment.length > 0 ? (
                  sentiment.slice(0, 3).map((s, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-[#666]">{s.symbol} ({s.source})</span>
                      <span className={`font-medium ${(s.score ?? 0) > 0 ? "text-emerald-600" : (s.score ?? 0) < 0 ? "text-red-500" : "text-[#999]"}`}>
                        {(s.score ?? 0) > 0 ? "+" : ""}{(s.score ?? 0).toFixed(2)}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[#999]">No data available</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Voting section */}
        {market.status === "active" && (
          <div className="mt-6 pt-6 border-t border-[#e5e5e5]">
            <h3 className="text-sm font-medium text-[#0a0a0a] mb-3">Cast your vote</h3>
            <div className="flex gap-3">
              <VoteButton label="Yes" icon={ThumbsUp} active={voted === "YES"} color="bg-emerald-600" onClick={() => handleVote("YES")} />
              <VoteButton label="No" icon={ThumbsDown} active={voted === "NO"} color="bg-red-500" onClick={() => handleVote("NO")} />
            </div>
            {voted && <p className="text-xs text-[#999] mt-2 text-center">You voted {voted}</p>}
          </div>
        )}

        {/* On-chain evidence */}
        {market.evidence_cids && market.evidence_cids.length > 0 && (
          <div className="mt-4 pt-4 border-t border-[#e5e5e5]">
            <p className="text-xs text-[#666] mb-2">On-chain evidence:</p>
            {market.evidence_cids.map((cid) => (
              <a key={cid} href={`https://gateway.lighthouse.storage/ipfs/${cid}`} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-[#7c3aed] hover:underline mr-3">
                <ExternalLink size={12} /> {cid.slice(0, 12)}…
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function MarketsPage() {
  const [markets, setMarkets] = useState<MarketType[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [search, setSearch] = useState("");
  const [selectedMarket, setSelectedMarket] = useState<MarketType | null>(null);

  useEffect(() => {
    api.getMarkets()
      .then((res) => setMarkets(res.markets))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (id && markets.length > 0) {
      const m = markets.find((x) => x.market_id === id);
      if (m) setSelectedMarket(m);
    }
  }, [markets]);

  const filtered = markets.filter((m) => {
    if (filter !== "all" && m.status !== filter) return false;
    if (search && !m.question.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const statusCounts = {
    all: markets.length,
    active: markets.filter((m) => m.status === "active").length,
    resolved: markets.filter((m) => m.status === "resolved").length,
    expired: markets.filter((m) => m.status === "expired").length,
  };

  if (selectedMarket) {
    return <MarketDetailView market={selectedMarket} onBack={() => setSelectedMarket(null)} />;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Prediction Markets</h1>
        <p className="text-[#666] mt-1">AI-discovered markets powered by Uniswap v4</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#999]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search markets..."
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-[#e5e5e5] bg-white text-sm text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:ring-2 focus:ring-[#7c3aed]/20 focus:border-[#7c3aed] transition"
          />
        </div>
        <div className="flex gap-1.5 bg-white border border-[#e5e5e5] rounded-lg p-1">
          {(["all", "active", "resolved", "expired"] as FilterStatus[]).map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                filter === s ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)} ({statusCounts[s]})
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-sm text-[#999]">Loading markets...</div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-sm text-[#999] mb-2">No markets found</p>
          <p className="text-xs text-[#ccc]">Markets are created automatically by the AI agent during discovery cycles</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((m) => (
            <button key={m.market_id} onClick={() => setSelectedMarket(m)} className="text-left bg-white rounded-xl border border-[#e5e5e5] p-5 hover:border-[#7c3aed]/30 hover:shadow-sm transition">
              <div className="flex items-center justify-between mb-3">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  m.status === "active" ? "bg-emerald-50 text-emerald-700" :
                  m.status === "resolved" ? "bg-blue-50 text-blue-700" : "bg-gray-50 text-gray-600"
                }`}>{m.status}</span>
              </div>
              <p className="text-sm font-medium text-[#0a0a0a] mb-4 line-clamp-2">{m.question}</p>
              <div className="flex items-center gap-2 mb-3">
                <div className="flex-1 h-2 bg-[#f0f0f0] rounded-full overflow-hidden">
                  <div className="h-full bg-[#7c3aed] rounded-full transition-all" style={{ width: `${(m.yes_probability || 0.5) * 100}%` }} />
                </div>
                <span className="text-xs font-medium text-[#7c3aed]">{((m.yes_probability || 0.5) * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between text-xs text-[#999]">
                <span>${(m.total_volume || 0).toLocaleString()} vol</span>
                <span>{m.participants || 0} traders</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
