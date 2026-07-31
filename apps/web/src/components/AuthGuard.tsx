"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchAuthConfig, isLoggedIn } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      if (isLoggedIn()) {
        if (!cancelled) setReady(true);
        return;
      }

      try {
        const config = await fetchAuthConfig();
        if (config.header_fallback) {
          if (!cancelled) setReady(true);
          return;
        }
      } catch {
        /* fall through to login */
      }

      if (!cancelled) router.replace("/login");
    }

    check();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (!ready) {
    return <div className="text-[var(--muted)]">验证登录状态…</div>;
  }

  return <>{children}</>;
}
