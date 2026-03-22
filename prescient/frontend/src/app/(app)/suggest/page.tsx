"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { MessageSquare, Send, CheckCircle, ExternalLink, Twitter } from "lucide-react";

const GROUP_OPTIONS = [
  { slug: "crypto", label: "CryptoTweets" },
  { slug: "stocks", label: "StockTweets" },
  { slug: "tech", label: "TechTweets" },
  { slug: "geopolitics", label: "GeopoliticsTweets" },
];

export default function SuggestPage() {
  const [handle, setHandle] = useState("");
  const [group, setGroup] = useState("crypto");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ status: string; filecoin_cid?: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim()) return;

    setSubmitting(true);
    try {
      const res = await api.request<{ status: string; filecoin_cid?: string }>("/api/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ handle: handle.trim(), group, reason }),
      });
      setResult(res);
      setHandle("");
      setReason("");
    } catch {
      setResult({ status: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  const twitterDMUrl = "https://x.com/messages/compose?recipient_id=juls95";
  const twitterMentionUrl = "https://x.com/intent/tweet?text=%40juls95%20";

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Suggest & Contact</h1>
        <p className="text-[#666] mt-1">Recommend accounts for our curated groups or reach out directly</p>
      </div>

      <div className="max-w-lg space-y-6">
        {/* Contact via Twitter */}
        <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#1DA1F2]/10 flex items-center justify-center">
              <Twitter size={20} className="text-[#1DA1F2]" />
            </div>
            <div>
              <p className="text-sm font-semibold text-[#0a0a0a]">Contact the Team</p>
              <p className="text-xs text-[#999]">Send a message via X/Twitter to @juls95</p>
            </div>
          </div>

          <p className="text-sm text-[#666] mb-4">
            Have feedback, questions, or partnership ideas? Reach out directly on X/Twitter.
          </p>

          <div className="space-y-2">
            <a
              href={twitterDMUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#1DA1F2] text-white text-sm font-medium hover:bg-[#1a8cd8] transition"
            >
              <MessageSquare size={14} /> Send Direct Message to @juls95
            </a>
            <a
              href={twitterMentionUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-[#1DA1F2]/30 text-[#1DA1F2] text-sm font-medium hover:bg-[#1DA1F2]/5 transition"
            >
              <Send size={14} /> Mention @juls95 on X
            </a>
          </div>
        </div>

        {/* Suggest Account */}
        <div className="bg-white rounded-xl border border-[#e5e5e5] p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-[#7c3aed]/10 flex items-center justify-center">
              <Send size={20} className="text-[#7c3aed]" />
            </div>
            <div>
              <p className="text-sm font-semibold text-[#0a0a0a]">Suggest an Account</p>
              <p className="text-xs text-[#999]">Recommend X/Twitter accounts for our curated groups</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#0a0a0a] mb-1.5">
                X/Twitter Handle
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#999] text-sm">@</span>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  placeholder="username"
                  className="w-full pl-8 pr-4 py-2.5 rounded-lg border border-[#e5e5e5] text-sm focus:outline-none focus:border-[#7c3aed] focus:ring-1 focus:ring-[#7c3aed]/20"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#0a0a0a] mb-1.5">
                Group
              </label>
              <div className="grid grid-cols-2 gap-2">
                {GROUP_OPTIONS.map((g) => (
                  <button
                    key={g.slug}
                    type="button"
                    onClick={() => setGroup(g.slug)}
                    className={`px-3 py-2 rounded-lg text-xs font-medium border transition ${
                      group === g.slug
                        ? "bg-[#7c3aed] text-white border-[#7c3aed]"
                        : "bg-white text-[#666] border-[#e5e5e5] hover:border-[#7c3aed]/30"
                    }`}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#0a0a0a] mb-1.5">
                Why should we add this account? <span className="text-[#999] font-normal">(optional)</span>
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g., Great technical analysis, posts daily market updates..."
                rows={3}
                className="w-full px-4 py-2.5 rounded-lg border border-[#e5e5e5] text-sm focus:outline-none focus:border-[#7c3aed] focus:ring-1 focus:ring-[#7c3aed]/20 resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting || !handle.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#7c3aed] text-white text-sm font-medium hover:bg-[#6d28d9] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={14} />
              {submitting ? "Submitting..." : "Submit Suggestion"}
            </button>
          </form>

          {result && result.status === "received" && (
            <div className="mt-4 p-4 rounded-lg bg-emerald-50 border border-emerald-200">
              <div className="flex items-start gap-2">
                <CheckCircle size={16} className="text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-emerald-700">Suggestion received!</p>
                  <p className="text-xs text-emerald-600 mt-1">Thank you for your contribution. We&apos;ll review it shortly.</p>
                  {result.filecoin_cid && (
                    <div className="mt-2 space-y-1">
                      <a
                        href={`https://gateway.lighthouse.storage/ipfs/${result.filecoin_cid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-[#7c3aed] hover:underline"
                      >
                        <ExternalLink size={10} /> Stored on Filecoin
                      </a>
                      <p className="text-[10px] text-amber-600">
                        🔒 This CID links to encrypted data. Do not share outside the Traipp app.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {result && result.status === "error" && (
            <div className="mt-4 p-4 rounded-lg bg-red-50 border border-red-200">
              <p className="text-sm text-red-700">Failed to submit. Please try again.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
