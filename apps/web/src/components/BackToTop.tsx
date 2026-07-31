"use client";

import { useEffect, useState } from "react";

export function BackToTop({ threshold = 480 }: { threshold?: number }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function onScroll() {
      setVisible(window.scrollY > threshold);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [threshold]);

  if (!visible) return null;

  return (
    <button
      type="button"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      className="fixed bottom-6 right-5 z-40 rounded-full border border-[var(--border)] bg-[var(--surface)] px-3.5 py-2.5 text-sm text-[var(--muted)] shadow-lg shadow-black/30 hover:border-[var(--accent)] hover:text-[var(--text)] active:scale-[0.98]"
      aria-label="回到顶部"
    >
      回到顶部
    </button>
  );
}
