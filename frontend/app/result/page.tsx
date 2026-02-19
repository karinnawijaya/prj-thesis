"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Icons } from "@/components/gallery/Icons";
import { apiFetch } from "@/lib/api";
import type { CompareResponse } from "@/lib/types";
import "../styles/result.css";

export default function ResultPage() {
  const router = useRouter();
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedIds = useMemo(() => {
    if (typeof window === "undefined") return [] as string[];
    const stored = sessionStorage.getItem("artweave_selected_paintings");
    return stored ? (JSON.parse(stored) as string[]) : [];
  }, []);

  const runCompare = useCallback(async () => {
    if (selectedIds.length !== 2) {
      router.replace("/option");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch<CompareResponse>("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          painting_a_id: selectedIds[0],
          painting_b_id: selectedIds[1],
        }),
      });
      setData(response);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [router, selectedIds]);

  useEffect(() => {
    runCompare();
  }, [runCompare]);

  return (
    <main className="page-shell">
      <div className="container result-page">
        <div>
          <span className="eyebrow">Summary</span>
          <h1 className="title">Comparison overview</h1>
          <p className="subtitle">A concise narrative crafted from your selected artworks.</p>
        </div>

        {loading ? (
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">Generating summary...</p>
          </div>
        ) : error ? (
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">{error}</p>
            <div style={{ marginTop: "16px" }}>
              <Button text="Try again" classname="white-btn" onClick={runCompare} />
            </div>
          </div>
        ) : data ? (
          <section className="card result-summary">
            <h2>Summary</h2>
            <p>{data.summary}</p>
          </section>
        ) : null}
      </div>
      <Icons nav="/option" />
    </main>
  );
}