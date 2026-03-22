"use client";

import { BookOpen, Brain, Shield, Database, BarChart3, Cpu } from "lucide-react";

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-[#e5e5e5] p-6 mb-4">
      <h2 className="text-base font-semibold text-[#0a0a0a] mb-4 flex items-center gap-2">
        <Icon size={18} className="text-[#7c3aed]" /> {title}
      </h2>
      {children}
    </div>
  );
}

export default function InfoPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0a0a0a] tracking-tight">Methodology</h1>
        <p className="text-[#666] mt-1">Technical explanation of how we analyze and score tweet data</p>
      </div>

      <Section title="Data Collection" icon={Database}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>
            We collect tweets from <strong>curated account groups</strong> using the X/Twitter API v2 
            User Timeline endpoint (<code className="bg-[#f5f5f5] px-1.5 py-0.5 rounded text-xs">GET /2/users/:id/tweets</code>).
          </p>
          <p>
            Each account was selected based on: <strong>quality of information</strong>, posting frequency, 
            engagement metrics (likes, reposts, comments), and topic consistency.
          </p>
          <p>
            We collect up to <strong>60 tweets per day</strong> across all groups (15 per group), 
            leveraging X&apos;s new pay-per-use pricing at <strong>$0.005/tweet + $0.010/user lookup</strong> — approximately 
            <strong>$0.41 per full collection cycle</strong> (11 lookups + ~60 tweets), significantly cheaper than the previous subscription model ($100-$5,000/mo).
          </p>
          <div className="bg-[#fafafa] rounded-lg p-4 border border-[#f0f0f0]">
            <p className="text-xs font-semibold text-[#0a0a0a] mb-2">Per Tweet, we collect:</p>
            <ul className="text-xs text-[#666] space-y-1">
              <li>• Tweet ID, full text content, timestamp</li>
              <li>• Author handle, display name, follower count</li>
              <li>• Engagement: likes, comments (replies), reposts</li>
              <li>• Author account creation date</li>
            </ul>
          </div>
        </div>
      </Section>

      <Section title="NLP Sentiment Analysis" icon={Brain}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>
            Our NLP engine uses a <strong>keyword-based lexicon approach</strong> for real-time sentiment scoring. 
            Each tweet is analyzed against curated word lists:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
              <p className="text-xs font-semibold text-emerald-700 mb-1">Bullish Signals (27 keywords)</p>
              <p className="text-xs text-emerald-600">breakout, rally, pump, bullish, buy, accumulate, golden cross, adoption, institutional, etf...</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
              <p className="text-xs font-semibold text-red-700 mb-1">Bearish Signals (24 keywords)</p>
              <p className="text-xs text-red-600">dump, crash, bearish, sell, short, liquidation, fear, panic, hack, exploit, regulation...</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <p className="text-xs font-semibold text-blue-700 mb-1">Technical Patterns (21 keywords)</p>
              <p className="text-xs text-blue-600">RSI, MACD, EMA, fibonacci, bollinger, support, resistance, divergence, breakout...</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
              <p className="text-xs font-semibold text-purple-700 mb-1">Fundamental Catalysts (26 keywords)</p>
              <p className="text-xs text-purple-600">TVL, DeFi, governance, staking, yield, airdrop, halving, whale, RWA, ETF...</p>
            </div>
          </div>
          <p>
            <strong>Scoring formula:</strong> For each tweet, <code className="bg-[#f5f5f5] px-1.5 py-0.5 rounded text-xs">score = (positive_matches - negative_matches) / total_matches</code>.
            Output range: -1.0 (fully bearish) to +1.0 (fully bullish).
          </p>
        </div>
      </Section>

      <Section title="Overview Score (1-10)" icon={BarChart3}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>The overview score combines four weighted components:</p>
          <div className="bg-[#fafafa] rounded-lg p-4 border border-[#f0f0f0]">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-[#999]">
                  <th className="pb-2">Component</th>
                  <th className="pb-2">Range</th>
                  <th className="pb-2">Description</th>
                </tr>
              </thead>
              <tbody className="text-[#444]">
                <tr className="border-t border-[#f0f0f0]">
                  <td className="py-2 font-medium">Sentiment Polarity</td>
                  <td className="py-2">0-4 pts</td>
                  <td className="py-2">Maps -1..+1 sentiment to 0-4 scale</td>
                </tr>
                <tr className="border-t border-[#f0f0f0]">
                  <td className="py-2 font-medium">Signal Clarity</td>
                  <td className="py-2">0-2 pts</td>
                  <td className="py-2">How clearly bullish or bearish (|bull - bear| / total)</td>
                </tr>
                <tr className="border-t border-[#f0f0f0]">
                  <td className="py-2 font-medium">Engagement Quality</td>
                  <td className="py-2">0-2 pts</td>
                  <td className="py-2">Avg likes+comments+reposts per tweet, capped at 500</td>
                </tr>
                <tr className="border-t border-[#f0f0f0]">
                  <td className="py-2 font-medium">Information Density</td>
                  <td className="py-2">0-2 pts</td>
                  <td className="py-2">Tweet count normalized (10 tweets = max)</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[#999]">
            Final score = max(1.0, min(10.0, sum of components)). A score of 7+ indicates strong actionable signal.
          </p>
        </div>
      </Section>

      <Section title="Crypto Card Percentage" icon={BarChart3}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>
            The <strong>percentage shown on each crypto card</strong> (e.g., &quot;72% positive&quot;) represents the 
            <strong>sentiment ratio</strong> derived from all tweets mentioning that asset:
          </p>
          <div className="bg-[#fafafa] rounded-lg p-4 border border-[#f0f0f0]">
            <p className="text-xs font-semibold text-[#0a0a0a] mb-3">How it&apos;s calculated:</p>
            <ol className="text-xs text-[#444] space-y-2 list-decimal list-inside">
              <li>All tweets from curated groups are scanned for asset mentions (e.g., &quot;Bitcoin&quot;, &quot;BTC&quot;, &quot;$BTC&quot;)</li>
              <li>Each tweet is scored using our keyword lexicon: bullish words (+) vs bearish words (-)</li>
              <li>The raw score ranges from <strong>-1.0</strong> (fully bearish) to <strong>+1.0</strong> (fully bullish)</li>
              <li>This is converted to a percentage: <code className="bg-white px-1.5 py-0.5 rounded border border-[#e5e5e5]">percentage = score × 100</code></li>
            </ol>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-2">
            <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
              <p className="text-lg font-bold text-red-600">0-30%</p>
              <p className="text-xs text-red-500">Bearish</p>
              <p className="text-[10px] text-[#999] mt-1">Mostly negative signals</p>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg border border-amber-200">
              <p className="text-lg font-bold text-amber-600">30-60%</p>
              <p className="text-xs text-amber-500">Neutral / Mixed</p>
              <p className="text-[10px] text-[#999] mt-1">Balanced bull/bear signals</p>
            </div>
            <div className="text-center p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <p className="text-lg font-bold text-emerald-600">60-100%</p>
              <p className="text-xs text-emerald-500">Bullish</p>
              <p className="text-[10px] text-[#999] mt-1">Strong positive sentiment</p>
            </div>
          </div>
          <p className="text-xs text-[#999]">
            The percentage updates each collection cycle based on the latest tweets. More tweets = more reliable scores — 
            we collect up to 15 tweets per group per cycle, balancing accuracy with API cost efficiency ($0.005/tweet).
          </p>
        </div>
      </Section>

      <Section title="Virality Score (0-100)" icon={Cpu}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>Each coin&apos;s virality score measures how much buzz it generates across all groups:</p>
          <div className="bg-[#fafafa] rounded-lg p-4 border border-[#f0f0f0] font-mono text-xs">
            <p>mention_score = min(mentions × 4, 40)</p>
            <p className="mt-1">sentiment_mult = 1.2 if bullish, 1.1 if bearish, 1.0 if neutral</p>
            <p className="mt-1">engagement_score = min(avg_engagement / 50, 20)</p>
            <p className="mt-2 font-bold">virality = min((mention_score + engagement_score) × sentiment_mult, 100)</p>
          </div>
          <p>
            Coins are tracked using aliases (e.g., &quot;Bitcoin&quot;, &quot;BTC&quot;, &quot;$BTC&quot;). 
            We exclude stablecoins (USDT, USDC) and show the top 10 by mention count.
          </p>
        </div>
      </Section>

      <Section title="Data Storage & Privacy" icon={Shield}>
        <div className="space-y-3 text-sm text-[#444] leading-relaxed">
          <p>
            All collected tweet data is <strong>encrypted using Lighthouse SDK (Kavach encryption)</strong> 
            before being uploaded to Filecoin/IPFS. This ensures:
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-[#7c3aed] mt-1">•</span>
              <span><strong>Privacy:</strong> Raw tweet content is encrypted at rest on Filecoin. Only authorized API key holders can decrypt.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#7c3aed] mt-1">•</span>
              <span><strong>Immutability:</strong> Each collection has a unique CID (Content Identifier) on IPFS, making it tamper-proof.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#7c3aed] mt-1">•</span>
              <span><strong>Traceability:</strong> CIDs are indexed in SQLite and displayed in the UI for full audit trail.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#7c3aed] mt-1">•</span>
              <span><strong>User data:</strong> User profiles from Clerk are stored encrypted on Filecoin with sensitive fields (email, wallet) protected.</span>
            </li>
          </ul>
          <div className="bg-[#7c3aed]/5 rounded-lg p-3 border border-[#7c3aed]/20 mt-3">
            <p className="text-xs text-[#7c3aed]">
              <strong>ERC-8004 Compliance:</strong> All agent actions are signed and receipted, 
              creating a verifiable chain of evidence from data collection to analysis.
            </p>
          </div>
        </div>
      </Section>
    </div>
  );
}
