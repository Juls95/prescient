"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useUser, UserButton } from "@clerk/nextjs";

export function Navbar() {
  const { isSignedIn } = useUser();

  return (
    <motion.nav
      initial={{ y: -12, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-[#e4e4e7]"
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#7c3aed] flex items-center justify-center">
            <span className="text-white font-bold text-xs">P</span>
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-[#0a0a0a]">Prescient</span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-6">
          {["Features", "How it works", "Tracks", "FAQ"].map((link) => (
            <a
              key={link}
              href={`#${link.toLowerCase().replace(/ /g, "-")}`}
              className="text-[14px] text-[#71717a] hover:text-[#0a0a0a] transition-colors"
            >
              {link}
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/Juls95/prescient"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:block text-[14px] text-[#71717a] hover:text-[#0a0a0a] transition-colors"
          >
            GitHub
          </a>

          {isSignedIn ? (
            <>
              <Link
                href="/dashboard"
                className="px-4 py-2 text-[14px] text-[#71717a] hover:text-[#0a0a0a] transition-colors font-medium"
              >
                Dashboard
              </Link>
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "w-8 h-8",
                  },
                }}
              />
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="px-4 py-2 text-[14px] text-[#71717a] hover:text-[#0a0a0a] transition-colors font-medium"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="btn-primary px-4 py-2 text-[14px] text-white bg-[#0a0a0a] rounded-full font-semibold hover:opacity-80 transition-opacity"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
