"use client";

import { motion } from "framer-motion";

const pillars = [
  {
    title: "Data Collection",
    subtitle: "Curated influencer timelines via X API v2.",
    bullets: [
      "11 hand-picked accounts across 4 groups",
      "Pay-per-use: $0.005/tweet, $0.010/user lookup",
      "~$0.41 per full collection cycle",
      "Excludes retweets & replies for signal quality",
    ],
  },
  {
    title: "NLP Sentiment Engine",
    subtitle: "Keyword-based lexicon scoring with signal classification.",
    bullets: [
      "27 bullish + 24 bearish keyword patterns",
      "Technical & fundamental signal detection",
      "Sentiment score: -1.0 to +1.0 → 0-100%",
      "Engagement-weighted confidence metrics",
    ],
  },
  {
    title: "Filecoin/IPFS Storage",
    subtitle: "Permanent, verifiable data archival via Lighthouse.",
    bullets: [
      "Every collection gets a unique IPFS CID",
      "Encrypted at rest via Lighthouse Kavach",
      "Immutable audit trail for all tweet data",
      "ERC-8004 agent action receipts",
    ],
  },
  {
    title: "Frontend & Auth",
    subtitle: "Modern stack with real-time data visualization.",
    bullets: [
      "Next.js 15 + Tailwind CSS + Framer Motion",
      "Clerk authentication (social + email)",
      "Real-time dashboard with live scores",
      "Intelligence deep-dive per asset",
    ],
  },
];

export function TechStack() {
  return (
    <section className="py-24 px-6 border-t border-[#e4e4e7]">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-[38px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] mb-12 max-w-3xl"
        >
          The tech behind Prescient.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pillars.map((p, i) => (
            <motion.article
              key={p.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="jet-card p-7"
            >
              <h3 className="text-[24px] font-semibold tracking-tight text-[#0a0a0a] mb-2">{p.title}</h3>
              <p className="text-[14px] text-[#71717a] mb-4">{p.subtitle}</p>
              <ul className="space-y-2">
                {p.bullets.map((b, bulletIndex) => (
                  <li key={`${i}-${bulletIndex}-${b}`} className="text-[14px] text-[#3f3f46] leading-relaxed">• {b}</li>
                ))}
              </ul>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
