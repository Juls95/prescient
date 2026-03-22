"use client";

import { useEffect, useState } from "react";
import { api, StorageIndex, StorageResponse, ReceiptsResponse } from "@/lib/api";
import { Database, ExternalLink, Search, FileJson, RefreshCw, AlertTriangle, Shield } from "lucide-react";

export default function StoragePage() {
  const [index, setIndex] = useState<StorageIndex | null>(null);
  const [receipts, setReceipts] = useState<ReceiptsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cidLookup, setCidLookup] = useState("");
  const [cidResult, setCidResult] = useState<StorageResponse | null>(null);
  const [cidLoading, setCidLoading] = useState(false);
  const [cidError, setCidError] = useState<string | null>(null);
  const [userCid, setUserCid] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [idx, rcp] = await Promise.allSettled([
          api.getStorageIndex(),
          api.getReceipts(),
        ]);
        if (idx.status === "fulfilled") setIndex(idx.value);
        if (rcp.status === "fulfilled") setReceipts(rcp.value);

        // Try to get user's Filecoin CID from profile
        try {
          const profile = await api.getProfile();
          const cid = (profile.user as Record<string, unknown>)?.filecoin_cid as string | null;
          if (cid) setUserCid(cid);
        } catch { /* not logged in or backend down */ }
      } catch {
        setError("Failed to connect to backend");
      }
      setLoading(false);
    }
    load();
  }, []);

  const handleCidLookup = async () => {
    if (!cidLookup.trim()) return;
    setCidLoading(true);
    setCidError(null);
    setCidResult(null);
    try {
      const result = await api.getStorageRecord(cidLookup.trim());
      setCidResult(result);
    } catch (e: unknown) {
      setCidError(e instanceof Error ? e.message : "CID not found");
    }
    setCidLoading(false);
  };

  const allCids: { label: string; cid: string }[] = [];
  if (index) {
    if (index.latest_discovery_cid) allCids.push({ label: "Latest Discovery", cid: index.latest_discovery_cid });
    if (index.latest_index_cid) allCids.push({ label: "Master Index", cid: index.latest_index_cid });
    Object.entries(index.markets).forEach(([marketId, cids]) => {
      cids.forEach((cid, i) => allCids.push({ label: `Market ${marketId.slice(0, 8)}… #${i + 1}`, cid }));
    });
  }
  if (userCid) allCids.unshift({ label: "Your Profile", cid: userCid });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Filecoin Storage</h1>
        <p className="text-[#666] mt-1">Immutable evidence stored on IPFS/Filecoin via Lighthouse</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* CID Lookup */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Search size={18} className="text-[#999]" /> Lookup by CID
        </h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={cidLookup}
            onChange={(e) => setCidLookup(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCidLookup()}
            placeholder="Enter IPFS CID (e.g., QmXyz...)"
            className="flex-1 px-4 py-2.5 rounded-lg border border-[#e5e5e5] bg-[#fafafa] text-sm text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:ring-2 focus:ring-[#7c3aed]/20 focus:border-[#7c3aed] transition"
          />
          <button onClick={handleCidLookup} disabled={cidLoading}
            className="px-4 py-2.5 rounded-lg bg-[#0a0a0a] text-white text-sm font-medium hover:opacity-85 transition disabled:opacity-50">
            {cidLoading ? "Loading..." : "Retrieve"}
          </button>
        </div>
        {cidError && <p className="text-sm text-red-500 mt-2">{cidError}</p>}
        {cidResult && (
          <div className="mt-4 p-4 rounded-lg bg-[#fafafa] border border-[#e5e5e5]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#7c3aed]">{cidResult.cid}</span>
              <a href={`https://gateway.lighthouse.storage/ipfs/${cidResult.cid}`} target="_blank" rel="noopener noreferrer"
                className="text-xs text-[#7c3aed] hover:underline flex items-center gap-1">
                <ExternalLink size={12} /> View on IPFS
              </a>
            </div>
            <pre className="text-xs text-[#444] overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">
              {JSON.stringify(cidResult.data, null, 2)}
            </pre>
          </div>
        )}
      </section>

      {/* Your Profile on Filecoin */}
      {userCid && (
        <section className="bg-white rounded-xl border border-[#7c3aed]/20 p-6 mb-6">
          <h2 className="text-lg font-semibold text-[#0a0a0a] mb-2 flex items-center gap-2">
            <Shield size={18} className="text-[#7c3aed]" /> Your Profile on Filecoin
          </h2>
          <p className="text-sm text-[#666] mb-3">Your user data is permanently stored on the decentralized web</p>
          <div className="flex items-center gap-2">
            <code className="text-xs bg-[#fafafa] border border-[#e5e5e5] rounded px-2 py-1 text-[#7c3aed]">{userCid}</code>
            <a href={`https://gateway.lighthouse.storage/ipfs/${userCid}`} target="_blank" rel="noopener noreferrer"
              className="text-xs text-[#7c3aed] hover:underline flex items-center gap-1">
              <ExternalLink size={12} /> View
            </a>
          </div>
        </section>
      )}

      {/* Storage Index */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Database size={18} className="text-[#999]" /> Storage Index
        </h2>
        {loading ? (
          <p className="text-sm text-[#999]">Loading index...</p>
        ) : allCids.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-[#999] mb-2">No records stored on Filecoin yet</p>
            <p className="text-xs text-[#ccc]">Records are created when the agent runs discovery cycles or when users sign up</p>
          </div>
        ) : (
          <div className="space-y-2">
            {allCids.map(({ label, cid }) => (
              <div key={cid} className="flex items-center justify-between py-2 border-b border-[#f0f0f0] last:border-0">
                <div className="flex items-center gap-2">
                  <FileJson size={14} className="text-[#999]" />
                  <span className="text-sm font-medium text-[#0a0a0a]">{label}</span>
                </div>
                <div className="flex items-center gap-3">
                  <code className="text-xs text-[#666] hidden md:block">{cid.length > 20 ? cid.slice(0, 10) + "…" + cid.slice(-8) : cid}</code>
                  <button onClick={() => { setCidLookup(cid); handleCidLookup(); }}
                    className="text-xs text-[#7c3aed] hover:underline">View</button>
                  <a href={`https://gateway.lighthouse.storage/ipfs/${cid}`} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-[#999] hover:text-[#7c3aed]">
                    <ExternalLink size={12} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ERC-8004 Receipts */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Shield size={18} className="text-[#999]" /> ERC-8004 Agent Receipts
        </h2>
        {!receipts || receipts.count === 0 ? (
          <p className="text-sm text-[#999]">No receipts generated yet. Receipts are created when the agent performs verified actions.</p>
        ) : (
          <div className="space-y-2">
            {receipts.receipts.map((r, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-[#f0f0f0] last:border-0">
                <div>
                  <span className="text-sm font-medium text-[#0a0a0a] capitalize">{r.action}</span>
                  {r.timestamp && <span className="text-xs text-[#999] ml-2">{new Date(r.timestamp).toLocaleString()}</span>}
                </div>
                {r.signature && (
                  <code className="text-xs text-[#666]">{r.signature.slice(0, 16)}…</code>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
