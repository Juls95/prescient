"use client";

export function Footer() {
  return (
    <footer className="border-t border-[#e4e4e7] py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-[#7c3aed] flex items-center justify-center">
                <span className="text-white font-bold text-xs">P</span>
              </div>
              <span className="text-[15px] font-semibold tracking-tight text-[#0a0a0a]">Prescient</span>
            </div>
            <p className="text-[14px] text-[#71717a] max-w-md">
              Social intelligence hub — curated tweets, NLP sentiment scoring, and permanent Filecoin storage.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[14px]">
            <a href="#features" className="text-[#71717a] hover:text-[#0a0a0a] transition-colors">Features</a>
            <a href="#how-it-works" className="text-[#71717a] hover:text-[#0a0a0a] transition-colors">How it works</a>
            <a href="#groups" className="text-[#71717a] hover:text-[#0a0a0a] transition-colors">Groups</a>
            <a href="#faq" className="text-[#71717a] hover:text-[#0a0a0a] transition-colors">FAQ</a>
            <a
              href="https://github.com/Juls95/prescient"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#71717a] hover:text-[#0a0a0a] transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://x.com/juls95"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#71717a] hover:text-[#0a0a0a] transition-colors"
            >
              @juls95
            </a>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-[#e4e4e7] text-[13px] text-[#a1a1aa]">
          © 2026 Prescient · Built for Synthesis Hackathon
        </div>
      </div>
    </footer>
  );
}
