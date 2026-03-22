"use client";

import { motion } from "framer-motion";

const groups = [
  {
    title: "CryptoTweets",
    meta: "4 accounts · 15 tweets/cycle",
    desc: "Market analysis from @Zeneca, @intocryptoverse, @IncomeSharks, and @Nebraskangooner. Bitcoin, Ethereum, DeFi, and altcoin insights.",
  },
  {
    title: "StockTweets",
    meta: "2 accounts · 14 tweets/cycle",
    desc: "Stock market intelligence from @arny_trezzi and @amitisinvesting. Technical analysis, earnings, and investment strategies.",
  },
  {
    title: "TechTweets",
    meta: "3 accounts · 15 tweets/cycle",
    desc: "VC and startup ecosystem insights from @andrewchen, @skominers, and @jason. AI, SaaS, and emerging tech trends.",
  },
  {
    title: "GeopoliticsTweets",
    meta: "2 accounts · 14 tweets/cycle",
    desc: "Global affairs analysis from @TuckerCarlson and @DonMiami3. Politics, policy, sanctions, and economic impact.",
  },
];

export function Tracks() {
  return (
    <section id="groups" className="py-24 px-6 bg-[#fafafa]">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-[38px] md:text-[52px] font-bold tracking-tighter text-[#0a0a0a] mb-12 max-w-3xl"
        >
          4 curated intelligence groups.
        </motion.h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {groups.map((t, i) => (
            <motion.div
              key={t.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="jet-card p-6"
            >
              <div className="text-[12px] font-semibold tracking-wide text-[#7c3aed] mb-2">{t.meta}</div>
              <h3 className="text-[20px] font-semibold tracking-tight text-[#0a0a0a] mb-2">{t.title}</h3>
              <p className="text-[14px] text-[#71717a] leading-relaxed">{t.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
