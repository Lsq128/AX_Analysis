"use client";

import { useEffect, useState } from "react";
import { fetchAuthConfig } from "@/lib/api";

/** null while loading; defaults to false on error (personal mode). */
export function useBillingEnabled(): boolean | null {
  const [enabled, setEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    fetchAuthConfig()
      .then((c) => setEnabled(Boolean(c.billing_enabled)))
      .catch(() => setEnabled(false));
  }, []);

  return enabled;
}
