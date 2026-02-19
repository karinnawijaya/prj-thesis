"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Icons } from "@/components/gallery/Icons";
import type { PaintingMeta } from "@/lib/metadata";
import "../styles/sets.css";

interface MetadataResponse {
  paintings?: PaintingMeta[];
}

export default function SetsPage() {
  const [paintings, setPaintings] = useState<PaintingMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const response = await fetch("/api/metadata");
        if (!response.ok) {
          throw new Error("Unable to load painting sets.");
        }
        const data = (await response.json()) as MetadataResponse;
        const nextPaintings = Array.isArray(data.paintings) ? data.paintings : [];
        setPaintings(nextPaintings);
        console.log(nextPaintings.map((painting) => ({ id: painting.id, set: painting.set })));
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadMetadata();
  }, []);

  const sets = useMemo(() => {
    return Array.from(new Set(paintings.map((painting) => painting.set))).sort();
  }, [paintings]);

  return (
    <main className="page-shell">
      <div className="container sets-page">
        <div>
          <span className="eyebrow">Curated sets</span>
          <h1 className="title">Select your paintings</h1>
          <p className="subtitle">
            Choose a painting set to begin comparing two standout artworks in a guided flow.
          </p>
        </div>

        {loading ? (
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">Loading sets...</p>
          </div>
        ) : error ? (
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">{error}</p>
          </div>
        ) : sets.length === 0 ? (
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">No sets available.</p>
          </div>
        ) : (
          <div className="sets-grid">
            {sets.map((setId) => {
              const count = paintings.filter((painting) => painting.set === setId).length;
              return (
                <Link key={setId} href={`/sets/${setId}`} className="set-card">
                  <div className="set-preview">Set {setId}</div>
                  <div className="set-meta">
                    <h3>{setId}</h3>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
      <Icons nav="/intro" />
    </main>
  );
}