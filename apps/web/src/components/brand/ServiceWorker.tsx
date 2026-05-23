"use client";

import { useEffect } from "react";

/**
 * Registers /sw.js on mount. Silent failure in dev / unsupported browsers.
 */
export function ServiceWorkerRegistrar() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;
    // Only register in production-like contexts; in dev SW caching breaks HMR.
    if (process.env.NODE_ENV !== "production") return;
    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .catch(() => {
        /* swallow — non-fatal */
      });
  }, []);
  return null;
}
