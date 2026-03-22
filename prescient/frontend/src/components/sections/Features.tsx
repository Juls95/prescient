"use client";

import { motion } from "framer-motion";

const features = [
  {
    icon: "🧠",
    title: "AI Sentiment Scoring",
    description: "NLP engine analyzes tweets using bullish/bearish keyword lexicons. Scores range from 0-100% with confidence metrics.",
  },
  {
    icon: "🐦",
    title: "Curated Tweet Groups",
    description: "Tweets fetched from hand-picked influencers across 4 groups: Crypto, Stocks, Tech, and Geopolitics.",
  },
  {
    icon: "🔒",
    title: "Filecoin Permanent Storage",
    description: "Every tweet collection is uploaded to IPFS/Filecoin via Lighthouse, creating an immutable, verifiable archive.",
  },
  {
    icon: "📊",
    title: "Real-Time Dashboard",
    description: "Live sentiment scores, engagement metrics, signal classification, and per-asset deep-dive analysis.",
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 px-6 border-t border-[#e4e4e7]">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-14"
        >
          <h2 className="text-[40px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] leading-tight max-w-2xl">
            Social intelligence, automated and verifiable.
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="jet-card p-6"
            >
              <div className="feature-icon">{f.icon}</div>
              <h3 className="text-[15px] font-semibold text-[#0a0a0a] mb-2">{f.title}</h3>
              <p className="text-[14px] text-[#71717a] leading-relaxed">{f.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
