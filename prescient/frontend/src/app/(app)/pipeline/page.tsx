"use client";

import { useEffect, useState } from "react";
import { api, HealthStatus, SchedulerStatus, SchedulerRun, RateLimitStatus, SentimentEntry, PriceEntry } from "@/lib/api";
import { Activity, RefreshCw, Wifi, WifiOff, Clock, AlertTriangle, CheckCircle, Database, Shield, Info } from "lucide-react";

function StatusDot({ ok }: { ok: boolean }) {
  return <div className={`w-2.5 h-2.5 rounded-full ${ok ? "bg-emerald-500" : "bg-red-400"}`} />;
}

function getNextRunLabel(lastRun: string | null | undefined, intervalHours: number): string {
  if (!lastRun) return "Pending first run";
  const next = new Date(new Date(lastRun).getTime() + intervalHours * 3600000);
  const now = new Date();
  if (next <= now) return "Due now";
  const diffMs = next.getTime() - now.getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 60) return `In ~${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return `In ~${hrs}h ${remainMins}m`;
}

export default function PipelinePage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [runs, setRuns] = useState<SchedulerRun[]>([]);
  const [rateLimits, setRateLimits] = useState<Record<string, RateLimitStatus>>({});
  const [prices, setPrices] = useState<PriceEntry[]>([]);
  const [sentiment, setSentiment] = useState<SentimentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, s, r, rl, p, se] = await Promise.allSettled([
        api.getHealth(),
        api.getSchedulerStatus(),
        api.getSchedulerRuns(15),
        api.getRateLimits(),
        api.getPrices(),
        api.getSentiment(),
      ]);
      if (h.status === "fulfilled") setHealth(h.value);
      else setError("Backend not reachable. Start it with: cd prescient && python3 -m uvicorn api.main:app --reload");
      if (s.status === "fulfilled") setScheduler(s.value);
      if (r.status === "fulfilled") setRuns(r.value.runs);
      if (rl.status === "fulfilled") setRateLimits(rl.value);
      if (p.status === "fulfilled") setPrices(p.value.prices);
      if (se.status === "fulfilled") setSentiment(se.value.sentiment);
    } catch {
      setError("Failed to connect to backend");
    }
    setLoading(false);
  };

  useEffect(() => { loadAll(); }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Data Pipeline</h1>
          <p className="text-[#666] mt-1">Automated data collection status — Dune Analytics, CoinGecko, Twitter/X & Farcaster</p>
        </div>
        <button onClick={loadAll} disabled={loading} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#e5e5e5] text-sm text-[#666] hover:bg-[#f5f5f5] transition">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">Connection Error</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Automated Pipeline Notice */}
      <div className="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm flex items-start gap-3">
        <Info size={18} className="mt-0.5 shrink-0" />
        <div>
          <p className="font-medium">Fully Automated Pipeline</p>
          <p className="mt-1 text-blue-700">
            Data collection runs automatically on a schedule. No manual intervention needed — the system fetches prices, sentiment, and social data at optimized intervals to minimize API costs.
          </p>
        </div>
      </div>

      {/* Service Health */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Wifi size={18} className="text-[#999]" /> Service Health
        </h2>
        {health ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {(["dune", "uniswap", "lighthouse", "twitter", "farcaster", "scheduler"] as const).map((svc) => (
              <div key={svc} className="flex items-center gap-2.5 p-3 rounded-lg bg-[#fafafa]">
                <StatusDot ok={health[svc] === "configured" || health[svc] === "running"} />
                <div>
                  <p className="text-sm font-medium text-[#0a0a0a] capitalize">{svc}</p>
                  <p className="text-xs text-[#999]">{health[svc]}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-[#999]">
            <WifiOff size={16} /> Backend not connected
          </div>
        )}
      </section>

      {/* Scheduler Status + Next Run */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Clock size={18} className="text-[#999]" /> Scheduler & Next Runs
        </h2>
        {scheduler ? (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <StatusDot ok={scheduler.running} />
              <span className="text-sm font-medium text-[#0a0a0a]">{scheduler.running ? "Running" : "Stopped"}</span>
              {scheduler.running && (
                <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Automated</span>
              )}
            </div>
            <div className="space-y-0">
              {Object.entries(scheduler.jobs || {}).map(([name, job]) => (
                <div key={name} className="flex items-center justify-between py-3 border-t border-[#f0f0f0]">
                  <div>
                    <p className="text-sm font-medium text-[#0a0a0a] capitalize">{name.replace(/_/g, " ")}</p>
                    <p className="text-xs text-[#999]">Every {job.interval_hours}h</p>
                  </div>
                  <div className="text-right space-y-0.5">
                    <p className="text-xs text-[#666]">
                      {job.last_run ? `Last: ${new Date(job.last_run).toLocaleString()}` : "Never run"}
                    </p>
                    <p className="text-xs font-medium text-[#7c3aed]">
                      Next: {getNextRunLabel(job.last_run, job.interval_hours)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-[#999]">Scheduler not available</p>
        )}
      </section>

      {/* API Usage & Cost */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Shield size={18} className="text-[#999]" /> API Usage & Costs
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div className="p-3 rounded-lg bg-[#fafafa] border border-[#f0f0f0]">
            <p className="text-xs text-[#999] mb-1">X/Twitter (Post Read)</p>
            <p className="text-lg font-bold text-[#0a0a0a]">$0.005</p>
            <p className="text-xs text-[#666]">per tweet fetched</p>
          </div>
          <div className="p-3 rounded-lg bg-[#fafafa] border border-[#f0f0f0]">
            <p className="text-xs text-[#999] mb-1">X/Twitter (User Read)</p>
            <p className="text-lg font-bold text-[#0a0a0a]">$0.010</p>
            <p className="text-xs text-[#666]">per user profile</p>
          </div>
          <div className="p-3 rounded-lg bg-[#fafafa] border border-[#f0f0f0]">
            <p className="text-xs text-[#999] mb-1">CoinGecko</p>
            <p className="text-lg font-bold text-emerald-600">Free</p>
            <p className="text-xs text-[#666]">Public API tier</p>
          </div>
          <div className="p-3 rounded-lg bg-[#fafafa] border border-[#f0f0f0]">
            <p className="text-xs text-[#999] mb-1">Filecoin/Lighthouse</p>
            <p className="text-lg font-bold text-emerald-600">Free</p>
            <p className="text-xs text-[#666]">1GB free storage</p>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
          <p className="text-xs text-amber-800">
            <strong>Cost Optimization:</strong> X API uses pay-per-use billing at $0.005/tweet + $0.010/user lookup (previously $100-$5,000/mo subscription). Our pipeline collects up to 60 tweets/day across 4 groups (15/group). Estimated ~$0.41 per full cycle — 99% cheaper than the old model.
          </p>
        </div>
      </section>

      {/* Rate Limits */}
      {Object.keys(rateLimits).length > 0 && (
        <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
          <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4">API Rate Limits</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(rateLimits).map(([name, rl]) => (
              <div key={name} className="p-3 rounded-lg bg-[#fafafa]">
                <p className="text-sm font-medium text-[#0a0a0a] capitalize mb-2">{name}</p>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-[#666]">Window</span>
                    <span className="text-[#0a0a0a]">{rl.requests_remaining} remaining</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-[#666]">Daily</span>
                    <span className="text-[#0a0a0a]">{rl.daily_remaining} remaining</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent Runs */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4">Recent Collection Runs</h2>
        {runs.length === 0 ? (
          <p className="text-sm text-[#999] py-4">No runs recorded yet. The scheduler will start collecting data automatically.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e5e5e5]">
                  <th className="text-left py-2 text-[#666] font-medium">Job</th>
                  <th className="text-left py-2 text-[#666] font-medium">Status</th>
                  <th className="text-left py-2 text-[#666] font-medium">Started</th>
                  <th className="text-right py-2 text-[#666] font-medium">Records</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run, i) => (
                  <tr key={i} className="border-b border-[#f0f0f0]">
                    <td className="py-2 capitalize">{run.job_name.replace(/_/g, " ")}</td>
                    <td className="py-2">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${run.status === "success" ? "text-emerald-600" : "text-red-500"}`}>
                        {run.status === "success" ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2 text-[#666]">{new Date(run.started_at).toLocaleString()}</td>
                    <td className="py-2 text-right">{run.records_fetched ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Live Data Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white rounded-xl border border-[#e5e5e5] p-6">
          <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
            <Database size={18} className="text-[#999]" /> Latest Prices ({prices.length})
          </h2>
          {prices.length === 0 ? (
            <p className="text-sm text-[#999]">No price data collected yet</p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {prices.map((p) => (
                <div key={p.symbol} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[#0a0a0a]">{p.symbol}</span>
                    {p.name && <span className="text-xs text-[#999]">{p.name}</span>}
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-[#0a0a0a]">${p.price_usd.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                    <span className={`text-xs ml-2 ${p.change_24h >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                      {p.change_24h >= 0 ? "+" : ""}{p.change_24h.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="bg-white rounded-xl border border-[#e5e5e5] p-6">
          <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
            <Activity size={18} className="text-[#999]" /> Latest Sentiment ({sentiment.length})
          </h2>
          {sentiment.length === 0 ? (
            <p className="text-sm text-[#999]">No sentiment data collected yet</p>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {sentiment.map((s, i) => (
                <div key={i} className="flex items-center justify-between py-1.5">
                  <div>
                    <span className="text-sm font-medium text-[#0a0a0a]">{s.symbol}</span>
                    <span className="text-xs text-[#999] ml-2">{s.source}</span>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-medium ${s.score > 0 ? "text-emerald-600" : s.score < 0 ? "text-red-500" : "text-[#999]"}`}>
                      {s.score > 0 ? "+" : ""}{s.score.toFixed(2)}
                    </span>
                    <span className="text-xs text-[#999] ml-2">{s.mention_count} mentions</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
