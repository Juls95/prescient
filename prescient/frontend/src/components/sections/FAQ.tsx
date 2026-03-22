"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const faqs = [
  {
    q: "What data does Traipp collect?",
    a: "We fetch tweets from 11 curated influencers across 4 groups (Crypto, Stocks, Tech, Geopolitics) using the X/Twitter API v2. Each tweet includes full text, engagement metrics (likes, replies, retweets), and author metadata.",
  },
  {
    q: "How is the sentiment score calculated?",
    a: "Our NLP engine uses a keyword-based lexicon approach. Each tweet is scanned against 27 bullish and 24 bearish keywords. The score ranges from -1.0 (fully bearish) to +1.0 (fully bullish), displayed as 0-100% on the dashboard.",
  },
  {
    q: "Where is the data stored?",
    a: "All tweet collections are uploaded to IPFS/Filecoin via Lighthouse SDK. Each collection gets a unique CID (Content Identifier), creating an immutable, verifiable archive. CIDs are displayed in the Intelligence page.",
  },
  {
    q: "How much does it cost to run?",
    a: "X API uses pay-per-use pricing: $0.005 per tweet read, $0.010 per user lookup. A full collection cycle (60 tweets across 4 groups) costs approximately $0.41. CoinGecko and Filecoin storage are free tier.",
  },
  {
    q: "Can I suggest new accounts to track?",
    a: "Yes! Use the Suggest & Contact page to recommend X/Twitter accounts for any of our 4 groups. You can also reach out directly to @juls95 on X with feedback or partnership ideas.",
  },
  {
    q: "Is my data private?",
    a: "User profiles are managed by Clerk with enterprise-grade security. Tweet data on Filecoin uses Lighthouse encryption. Filecoin CIDs are marked as internal — do not share outside the Traipp app.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="py-24 px-6 border-t border-[#e4e4e7]">
      <div className="max-w-4xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-[38px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] mb-10"
        >
          Frequently asked questions.
        </motion.h2>

        <div className="space-y-3">
          {faqs.map((item, i) => (
            <motion.div
              key={item.q}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className="jet-card overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full px-6 py-4 text-left flex items-center justify-between gap-3"
              >
                <span className="text-[16px] font-semibold text-[#0a0a0a]">{item.q}</span>
                <span className="text-[#71717a] text-[14px]">{open === i ? "−" : "+"}</span>
              </button>
              <AnimatePresence>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <p className="px-6 pb-5 text-[14px] text-[#71717a] leading-relaxed">{item.a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
