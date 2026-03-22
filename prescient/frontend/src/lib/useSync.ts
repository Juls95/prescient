"use client";

import { useEffect, useRef } from "react";
import { useUser } from "@clerk/nextjs";
import { api } from "./api";

/**
 * Hook that syncs the Clerk user to the backend after sign-in.
 * Stores JWT token in localStorage for subsequent API calls.
 * Runs once per session (guarded by ref).
 */
export function useSync() {
  const { user, isSignedIn, isLoaded } = useUser();
  const synced = useRef(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user || synced.current) return;

    const doSync = async () => {
      try {
        const res = await api.request<{
          user: Record<string, unknown>;
          token: string;
          filecoin_cid: string | null;
          synced: boolean;
        }>("/api/users/sync", {
          method: "POST",
          body: {
            clerk_id: user.id,
            username: user.username || user.firstName || user.id.slice(0, 12),
            email: user.primaryEmailAddress?.emailAddress || "",
            display_name: user.fullName || user.firstName || undefined,
          },
        });
        if (res.token) {
          localStorage.setItem("traipp_token", res.token);
        }
        synced.current = true;
      } catch (err) {
        console.warn("[Traipp] Backend sync failed (non-blocking):", err);
        // Don't block the user - Clerk auth still works, backend sync is best-effort
      }
    };

    doSync();
  }, [isLoaded, isSignedIn, user]);

  return { isLoaded, isSignedIn, user };
}
