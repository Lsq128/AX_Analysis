"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isLoggedIn, searchTickers } from "@/lib/api";
import type { TickerSearchResult } from "@/lib/types";

export function HomeTickerInput() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [results, setResults] = useState<TickerSearchResult[]>([]);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    const q = ticker.trim();
    if (q.length < 2) {
      setResults([]);
      return;
    }
    const handle = setTimeout(() => {
      searchTickers(q, 6).then(setResults).catch(() => setResults([]));
    }, 220);
    return () => clearTimeout(handle);
  }, [ticker]);

  function go(value?: string) {
    const t = (value ?? ticker).trim().toUpperCase();
    if (!t) return;
    const dest = `/workspace/analyses/new?ticker=${encodeURIComponent(t)}`;
    if (isLoggedIn()) {
      router.push(dest);
    } else {
      router.push(`/login?next=${encodeURIComponent(dest)}`);
    }
  }

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <form
        className="ax-input-shell"
        onSubmit={(e) => {
          e.preventDefault();
          go();
        }}
      >
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          placeholder="输入股票代码，例如 600519 / 0700.HK / NVDA"
          aria-label="股票代码"
          autoComplete="off"
          spellCheck={false}
        />
        <button type="submit" className="ax-btn-primary" disabled={!ticker.trim()}>
          分析
        </button>
      </form>

      {focused && results.length > 0 && (
        <ul className="absolute z-20 left-0 right-0 mt-2 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-lg">
          {results.map((item) => (
            <li key={`${item.source}-${item.ticker}`}>
              <button
                type="button"
                className="w-full px-4 py-3 text-left text-sm hover:bg-[var(--surface-2)]"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  setTicker(item.ticker);
                  setResults([]);
                  go(item.ticker);
                }}
              >
                <span className="font-medium">{item.ticker}</span>
                {item.name && (
                  <span className="ml-2 text-[var(--muted)]">
                    {item.name}
                    {item.market ? ` · ${item.market}` : ""}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
