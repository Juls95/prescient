"use client";

import { useEffect, useState } from "react";
import { useSync } from "@/lib/useSync";
import { api } from "@/lib/api";
import { Save, Plus, X, Bell, Shield, Eye, Wallet } from "lucide-react";

const ALL_COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK", "UNI", "ATOM", "LTC", "NEAR", "APT", "ARB", "OP", "FIL", "INJ"];

export default function SettingsPage() {
  const { user } = useSync();
  const [riskTolerance, setRiskTolerance] = useState<"low" | "medium" | "high">("medium");
  const [notifications, setNotifications] = useState(true);
  const [watchlist, setWatchlist] = useState<string[]>(["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC"]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [addingCoin, setAddingCoin] = useState(false);
  const [walletAddress, setWalletAddress] = useState("");
  const [walletSaving, setWalletSaving] = useState(false);
  const [walletSaved, setWalletSaved] = useState(false);
  const [walletError, setWalletError] = useState("");

  const availableCoins = ALL_COINS.filter((c) => !watchlist.includes(c));

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updatePreferences({
        risk_tolerance: riskTolerance,
        notification_enabled: notifications,
        favorite_coins: watchlist,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* noop */ }
    setSaving(false);
  };

  const removeCoin = (coin: string) => setWatchlist((prev) => prev.filter((c) => c !== coin));
  const addCoin = (coin: string) => {
    setWatchlist((prev) => [...prev, coin]);
    setAddingCoin(false);
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Settings</h1>
        <p className="text-[#666] mt-1">Manage your preferences and watchlist</p>
      </div>

      {/* Profile */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Shield size={18} className="text-[#999]" /> Profile
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-[#666]">Username</span>
            <span className="text-sm font-medium text-[#0a0a0a]">{user?.firstName || user?.username || "User"}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-[#f0f0f0]">
            <span className="text-sm text-[#666]">Email</span>
            <span className="text-sm font-medium text-[#0a0a0a]">{user?.primaryEmailAddress?.emailAddress || "—"}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-[#f0f0f0]">
            <span className="text-sm text-[#666]">Member since</span>
            <span className="text-sm font-medium text-[#0a0a0a]">
              {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : "—"}
            </span>
          </div>
        </div>
      </section>

      {/* Wallet */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
          <Wallet size={18} className="text-[#999]" /> Wallet
        </h2>
        <p className="text-xs text-[#999] mb-4">Connect your wallet to participate in prediction markets and receive payouts.</p>

        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={walletAddress}
              onChange={(e) => { setWalletAddress(e.target.value); setWalletError(""); }}
              placeholder="0x... (Ethereum address)"
              className="flex-1 px-3 py-2.5 rounded-lg border border-[#e5e5e5] bg-white text-sm text-[#0a0a0a] placeholder-[#999] focus:outline-none focus:ring-2 focus:ring-[#7c3aed]/20 focus:border-[#7c3aed] transition"
            />
            <button
              onClick={async () => {
                if (!walletAddress.startsWith("0x") || walletAddress.length !== 42) {
                  setWalletError("Invalid Ethereum address (must be 0x + 40 hex chars)");
                  return;
                }
                setWalletSaving(true);
                try {
                  await api.attachWallet(walletAddress);
                  setWalletSaved(true);
                  setTimeout(() => setWalletSaved(false), 2000);
                } catch (e: unknown) {
                  setWalletError(e instanceof Error ? e.message : "Failed to attach wallet");
                }
                setWalletSaving(false);
              }}
              disabled={walletSaving || !walletAddress}
              className="px-4 py-2.5 rounded-lg bg-[#0a0a0a] text-white text-sm font-medium hover:opacity-85 transition disabled:opacity-50"
            >
              {walletSaving ? "Saving..." : walletSaved ? "Saved ✓" : "Attach"}
            </button>
          </div>

          <button
            onClick={async () => {
              if (typeof window !== "undefined" && (window as unknown as { ethereum?: { request: (args: { method: string }) => Promise<string[]> } }).ethereum) {
                try {
                  const eth = (window as unknown as { ethereum: { request: (args: { method: string }) => Promise<string[]> } }).ethereum;
                  const accounts = await eth.request({ method: "eth_requestAccounts" });
                  if (accounts[0]) {
                    setWalletAddress(accounts[0]);
                    setWalletSaving(true);
                    await api.attachWallet(accounts[0]);
                    setWalletSaved(true);
                    setTimeout(() => setWalletSaved(false), 2000);
                    setWalletSaving(false);
                  }
                } catch {
                  setWalletError("MetaMask connection failed");
                }
              } else {
                setWalletError("No wallet detected. Install MetaMask or paste your address above.");
              }
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border border-[#e5e5e5] text-sm font-medium text-[#666] hover:bg-[#f5f5f5] transition"
          >
            <Wallet size={16} />
            Connect MetaMask
          </button>

          {walletError && <p className="text-xs text-red-500">{walletError}</p>}
          {walletSaved && <p className="text-xs text-emerald-600">Wallet attached successfully!</p>}
        </div>
      </section>

      {/* Risk */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#0a0a0a] mb-4">Risk Tolerance</h2>
        <div className="flex gap-3">
          {(["low", "medium", "high"] as const).map((level) => (
            <button
              key={level}
              onClick={() => setRiskTolerance(level)}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition ${
                riskTolerance === level
                  ? level === "low" ? "bg-blue-50 border-blue-300 text-blue-700"
                    : level === "medium" ? "bg-yellow-50 border-yellow-300 text-yellow-700"
                    : "bg-red-50 border-red-300 text-red-700"
                  : "bg-white border-[#e5e5e5] text-[#666] hover:bg-[#f5f5f5]"
              }`}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
      </section>

      {/* Notifications */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell size={18} className="text-[#999]" />
            <div>
              <h2 className="text-sm font-semibold text-[#0a0a0a]">Notifications</h2>
              <p className="text-xs text-[#999]">Get alerts for new markets and price movements</p>
            </div>
          </div>
          <button
            onClick={() => setNotifications(!notifications)}
            className={`relative w-11 h-6 rounded-full transition ${notifications ? "bg-[#7c3aed]" : "bg-[#e5e5e5]"}`}
          >
            <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${notifications ? "translate-x-5.5 left-0.5" : "left-0.5"}`}
              style={{ transform: notifications ? "translateX(22px)" : "translateX(0)" }}
            />
          </button>
        </div>
      </section>

      {/* Watchlist */}
      <section className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#0a0a0a] flex items-center gap-2">
            <Eye size={18} className="text-[#999]" /> Watchlist
          </h2>
          <button
            onClick={() => setAddingCoin(true)}
            className="text-xs text-[#7c3aed] hover:underline flex items-center gap-1"
          >
            <Plus size={14} /> Add coin
          </button>
        </div>

        {addingCoin && (
          <div className="mb-4 flex flex-wrap gap-2 p-3 bg-[#fafafa] rounded-lg border border-[#e5e5e5]">
            {availableCoins.slice(0, 12).map((coin) => (
              <button key={coin} onClick={() => addCoin(coin)}
                className="px-3 py-1 text-xs font-medium rounded-full bg-white border border-[#e5e5e5] text-[#666] hover:border-[#7c3aed] hover:text-[#7c3aed] transition">
                {coin}
              </button>
            ))}
            <button onClick={() => setAddingCoin(false)} className="px-3 py-1 text-xs text-[#999] hover:text-[#666]">Cancel</button>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {watchlist.length === 0 ? (
            <p className="text-sm text-[#999]">No coins in your watchlist. Add some to get started.</p>
          ) : (
            watchlist.map((coin) => (
              <span key={coin} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#f5f5f5] text-sm font-medium text-[#0a0a0a]">
                {coin}
                <button onClick={() => removeCoin(coin)} className="text-[#999] hover:text-red-500 transition">
                  <X size={14} />
                </button>
              </span>
            ))
          )}
        </div>
      </section>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-[#0a0a0a] text-white text-sm font-medium hover:opacity-85 transition disabled:opacity-50"
      >
        <Save size={16} />
        {saving ? "Saving..." : saved ? "Saved ✓" : "Save Changes"}
      </button>
    </div>
  );
}
