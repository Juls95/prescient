"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Brain,
  MessageSquare,
  ArrowLeft,
  Clock,
  BarChart3,
  Zap,
} from "lucide-react";
import Link from "next/link";

// ── Types ───────────────────────────────────────────────────────────

interface TweetData {
  text: string;
  username: string;
}

interface Collection {
  id: number | null;
  source: string;
  score: number;
  mention_count: number;
  sample_texts: TweetData[];
  fetched_at: string;
  filecoin_cid: string | null;
}

interface AssetGroup {
  symbol: string;
  collections: Collection[];
  collection_count: number;
  total_tweets: number;
  latest_score: number;
  latest_fetched: string;
}

interface SymbolInsight {
  symbol: string;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: number;
  sentiment_score: number;
  mention_count: number;
  summary: string;
  reasons: string[];
  signals: {
    bullish: string[];
    bearish: string[];
    technical: string[];
    fundamental: string[];
  };
  entities: string[];
  pct_moves: { pct: number; context: string }[];
  price_targets: { value: number; context: string }[];
  all_tweets: TweetData[];
  collections: { fetched_at: string; score: number; mention_count: number; tweet_count: number }[];
  total_collections: number;
  total_tweets_analyzed: number;
  analyzed_at: string;
}

// ── Components ──────────────────────────────────────────────────────

function SignalTag({ label, type }: { label: string; type: "bull" | "bear" | "tech" | "fund" | "entity" }) {
  const colors = {
    bull: "bg-emerald-50 text-emerald-700 border-emerald-200",
    bear: "bg-red-50 text-red-700 border-red-200",
    tech: "bg-blue-50 text-blue-700 border-blue-200",
    fund: "bg-purple-50 text-purple-700 border-purple-200",
    entity: "bg-orange-50 text-orange-700 border-orange-200",
  };
  return (
    <span className={`text-[11px] px-2.5 py-1 rounded-full border ${colors[type]}`}>{label}</span>
  );
}

function TweetCard({ tweet, index }: { tweet: TweetData; index: number }) {
  return (
    <div className="bg-[#fafafa] rounded-lg p-3 border border-[#f0f0f0] text-sm text-[#444] leading-relaxed">
      <div className="flex items-start gap-2">
        <span className="text-[10px] text-[#999] bg-white px-1.5 py-0.5 rounded border border-[#e5e5e5] shrink-0">
          #{index + 1}
        </span>
        <div className="flex-1 min-w-0">
          {tweet.username && (
            <a
              href={`https://x.com/${tweet.username}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-medium text-[#7c3aed] hover:underline"
            >
              @{tweet.username}
            </a>
          )}
          <p className="whitespace-pre-wrap break-words mt-0.5">{tweet.text}</p>
        </div>
      </div>
    </div>
  );
}

function CollectionGroup({ collection, index }: { collection: Collection; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const date = new Date(collection.fetched_at);
  const dateStr = date.toLocaleString();

  return (
    <div className="border border-[#e5e5e5] rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 hover:bg-[#fafafa] transition text-left"
      >
        <Clock size={14} className="text-[#999] shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[#0a0a0a]">{dateStr}</p>
          <p className="text-xs text-[#999]">
            {collection.mention_count} mentions · Score: {(collection.score * 100).toFixed(0)}% · {collection.sample_texts.length} tweets stored
          </p>
        </div>
        {collection.filecoin_cid && (
          <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
            <a
              href={`https://gateway.lighthouse.storage/ipfs/${collection.filecoin_cid}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-[#7c3aed] hover:underline"
            >
              <ExternalLink size={12} /> Filecoin
            </a>
            <span className="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200" title="This CID links to encrypted data stored on Filecoin. Do not share outside Prescient.">
              🔒 Internal
            </span>
          </div>
        )}
        {expanded ? <ChevronDown size={16} className="text-[#ccc]" /> : <ChevronRight size={16} className="text-[#ccc]" />}
      </button>

      {expanded && collection.sample_texts.length > 0 && (
        <div className="px-4 pb-4 space-y-2">
          {collection.sample_texts.map((t, i) => (
            <TweetCard key={i} tweet={t} index={i} />
          ))}
        </div>
      )}

      {expanded && collection.sample_texts.length === 0 && (
        <div className="px-4 pb-4">
          <p className="text-sm text-[#999]">No tweet text stored for this collection.</p>
        </div>
      )}
    </div>
  );
}

function AssetDetailView({ symbol, onBack }: { symbol: string; onBack: () => void }) {
  const [insight, setInsight] = useState<SymbolInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"analysis" | "tweets">("analysis");

  useEffect(() => {
    api.request<SymbolInsight>(`/api/insights/${symbol}`)
      .then((data) => setInsight(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-[#999]">
        <Brain size={32} className="mx-auto text-[#ccc] mb-3 animate-pulse" />
        Analyzing ${symbol} data...
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="py-20 text-center">
        <p className="text-sm text-[#999]">Failed to load analysis for {symbol}</p>
        <button onClick={onBack} className="mt-3 text-sm text-[#7c3aed] hover:underline">← Go back</button>
      </div>
    );
  }

  const dirColor = insight.direction === "BULLISH" ? "text-emerald-600" :
    insight.direction === "BEARISH" ? "text-red-500" : "text-amber-600";
  const dirBg = insight.direction === "BULLISH" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
    insight.direction === "BEARISH" ? "bg-red-50 text-red-700 border-red-200" : "bg-amber-50 text-amber-700 border-amber-200";
  const DirIcon = insight.direction === "BULLISH" ? TrendingUp :
    insight.direction === "BEARISH" ? TrendingDown : Activity;

  return (
    <div>
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-[#7c3aed] hover:underline mb-6">
        <ArrowLeft size={14} /> Back to all assets
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-[#0a0a0a]">${insight.symbol}</h2>
            <span className={`text-xs font-medium px-3 py-1 rounded-full border ${dirBg}`}>
              {insight.direction}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <DirIcon size={20} className={dirColor} />
            <span className={`text-lg font-bold ${dirColor}`}>
              {(insight.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
        </div>

        {/* AI Summary */}
        <div className="p-4 rounded-lg bg-[#7c3aed]/5 border border-[#7c3aed]/20 mb-4">
          <div className="flex items-start gap-2">
            <Brain size={16} className="text-[#7c3aed] mt-0.5 shrink-0" />
            <p className="text-sm text-[#444] leading-relaxed">{insight.summary}</p>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-[#fafafa] rounded-lg">
            <p className="text-lg font-bold text-[#0a0a0a]">{(insight.sentiment_score * 100).toFixed(0)}%</p>
            <p className="text-xs text-[#999]">Sentiment</p>
          </div>
          <div className="text-center p-3 bg-[#fafafa] rounded-lg">
            <p className="text-lg font-bold text-[#0a0a0a]">{insight.mention_count}</p>
            <p className="text-xs text-[#999]">Mentions</p>
          </div>
          <div className="text-center p-3 bg-[#fafafa] rounded-lg">
            <p className="text-lg font-bold text-[#0a0a0a]">{insight.total_tweets_analyzed}</p>
            <p className="text-xs text-[#999]">Tweets Analyzed</p>
          </div>
          <div className="text-center p-3 bg-[#fafafa] rounded-lg">
            <p className="text-lg font-bold text-[#0a0a0a]">{insight.total_collections}</p>
            <p className="text-xs text-[#999]">Collections</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1.5 bg-white border border-[#e5e5e5] rounded-lg p-1 mb-6 w-fit">
        <button onClick={() => setActiveTab("analysis")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition flex items-center gap-2 ${
            activeTab === "analysis" ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
          }`}>
          <Brain size={14} /> Classification Analysis
        </button>
        <button onClick={() => setActiveTab("tweets")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition flex items-center gap-2 ${
            activeTab === "tweets" ? "bg-[#0a0a0a] text-white" : "text-[#666] hover:bg-[#f5f5f5]"
          }`}>
          <MessageSquare size={14} /> All Tweets ({insight.total_tweets_analyzed})
        </button>
      </div>

      {activeTab === "analysis" ? (
        <div className="space-y-6">
          {/* Reasons */}
          <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
            <h3 className="text-sm font-semibold text-[#0a0a0a] mb-3 flex items-center gap-2">
              <Zap size={14} className="text-[#7c3aed]" /> Why {insight.direction}?
            </h3>
            <ul className="space-y-2">
              {insight.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[#444]">
                  <span className="text-[#7c3aed] mt-1">•</span>
                  <span className="capitalize">{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Signals breakdown */}
          <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
            <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
              <BarChart3 size={14} className="text-[#7c3aed]" /> Detected Signals
            </h3>
            <div className="space-y-4">
              {insight.signals.bullish.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Bullish ({insight.signals.bullish.length})</p>
                  <div className="flex flex-wrap gap-1.5">
                    {insight.signals.bullish.map((s) => <SignalTag key={s} label={s} type="bull" />)}
                  </div>
                </div>
              )}
              {insight.signals.bearish.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Bearish ({insight.signals.bearish.length})</p>
                  <div className="flex flex-wrap gap-1.5">
                    {insight.signals.bearish.map((s) => <SignalTag key={s} label={s} type="bear" />)}
                  </div>
                </div>
              )}
              {insight.signals.technical.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Technical ({insight.signals.technical.length})</p>
                  <div className="flex flex-wrap gap-1.5">
                    {insight.signals.technical.map((s) => <SignalTag key={s} label={s} type="tech" />)}
                  </div>
                </div>
              )}
              {insight.signals.fundamental.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Fundamental ({insight.signals.fundamental.length})</p>
                  <div className="flex flex-wrap gap-1.5">
                    {insight.signals.fundamental.map((s) => <SignalTag key={s} label={s} type="fund" />)}
                  </div>
                </div>
              )}
              {insight.entities.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Notable Entities ({insight.entities.length})</p>
                  <div className="flex flex-wrap gap-1.5">
                    {insight.entities.map((e) => <SignalTag key={e} label={e} type="entity" />)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Price targets & moves */}
          {(insight.price_targets.length > 0 || insight.pct_moves.length > 0) && (
            <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
              <h3 className="text-sm font-semibold text-[#0a0a0a] mb-3">Extracted Price Data</h3>
              {insight.price_targets.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-[#666] mb-2">Price Targets Mentioned</p>
                  {insight.price_targets.map((t, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm py-1">
                      <span className="font-mono font-medium text-[#0a0a0a]">${t.value.toLocaleString()}</span>
                      <span className="text-xs text-[#999]">— {t.context}</span>
                    </div>
                  ))}
                </div>
              )}
              {insight.pct_moves.length > 0 && (
                <div>
                  <p className="text-xs text-[#666] mb-2">Percentage Moves Discussed</p>
                  {insight.pct_moves.map((m, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm py-1">
                      <span className={`font-mono font-medium ${m.pct > 0 ? "text-emerald-600" : "text-red-500"}`}>
                        {m.pct > 0 ? "+" : ""}{m.pct.toFixed(1)}%
                      </span>
                      <span className="text-xs text-[#999]">— {m.context.slice(0, 80)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Collection history */}
          <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
            <h3 className="text-sm font-semibold text-[#0a0a0a] mb-3">Collection History</h3>
            <div className="space-y-2">
              {insight.collections.map((c, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[#f0f0f0] last:border-0 text-sm">
                  <span className="text-[#666]">{new Date(c.fetched_at).toLocaleString()}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-[#999]">{c.tweet_count} tweets</span>
                    <span className="text-[#999]">{c.mention_count} mentions</span>
                    <span className={`font-medium ${c.score > 0.3 ? "text-emerald-600" : c.score > 0.15 ? "text-amber-600" : "text-red-500"}`}>
                      {(c.score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* All tweets tab */
        <div className="space-y-2">
          {insight.all_tweets.length > 0 ? (
            insight.all_tweets.map((t, i) => <TweetCard key={i} tweet={t} index={i} />)
          ) : (
            <div className="py-12 text-center text-sm text-[#999]">No tweets stored</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────

export default function IntelligencePage() {
  const [assets, setAssets] = useState<AssetGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  useEffect(() => {
    api.request<{ assets: AssetGroup[] }>("/api/x-data")
      .then((data) => setAssets(data.assets))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (selectedSymbol) {
    return <AssetDetailView symbol={selectedSymbol} onBack={() => setSelectedSymbol(null)} />;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Intelligence</h1>
        <p className="text-[#666] mt-1">All X/Twitter data with AI classification per asset</p>
      </div>

      {loading ? (
        <div className="py-20 text-center text-sm text-[#999]">Loading X data...</div>
      ) : assets.length === 0 ? (
        <div className="py-20 text-center">
          <MessageSquare size={40} className="mx-auto text-[#ccc] mb-4" />
          <p className="text-sm text-[#999] mb-2">No X data collected yet</p>
          <Link href="/pipeline" className="text-xs text-[#7c3aed] hover:underline">Trigger sentiment collection →</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {assets.map((asset) => (
            <div key={asset.symbol} className="bg-white rounded-xl border border-[#e5e5e5] overflow-hidden">
              {/* Asset header */}
              <div className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#f5f5f5] flex items-center justify-center text-sm font-bold text-[#0a0a0a]">
                    {asset.symbol.slice(0, 3)}
                  </div>
                  <div>
                    <p className="text-base font-semibold text-[#0a0a0a]">${asset.symbol}</p>
                    <p className="text-xs text-[#999]">
                      {asset.collection_count} collections · {asset.total_tweets} tweets · Last: {asset.latest_fetched?.slice(0, 16)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-sm font-medium ${(asset.latest_score ?? 0) > 0.3 ? "text-emerald-600" : (asset.latest_score ?? 0) > 0.15 ? "text-amber-600" : "text-red-500"}`}>
                    {((asset.latest_score ?? 0) * 100).toFixed(0)}% positive
                  </span>
                  <button
                    onClick={() => setSelectedSymbol(asset.symbol)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#7c3aed]/10 text-[#7c3aed] text-xs font-medium hover:bg-[#7c3aed]/20 transition"
                  >
                    <Brain size={12} /> View Analysis
                  </button>
                </div>
              </div>

              {/* Collections */}
              <div className="px-5 pb-5 space-y-2">
                {asset.collections.map((c, i) => (
                  <CollectionGroup key={`${asset.symbol}-${i}`} collection={c} index={i} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
