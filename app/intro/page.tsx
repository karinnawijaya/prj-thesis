"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Icons } from "@/components/gallery/Icons";
import { apiFetch } from "@/lib/api";
import { resolveImageUrl } from "@/lib/images";
import type { Painting, SetSummary } from "@/lib/types";
import { paintingAssets } from "@/lib/paintingAssets";
import "../styles/intro.css";

export default function IntroPage() {
  const router = useRouter();
  const [heroPainting, setHeroPainting] = useState<Painting | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHero = async () => {
      try {
        const sets = await apiFetch<SetSummary[]>("/api/sets");
        if (!sets.length) {
          setHeroPainting(null);
          return;
        }
        const paintings = await apiFetch<Painting[]>(`/api/paintings?set_id=${sets[0].set_id}`);
        setHeroPainting(paintings[0] ?? null);
      } catch (error) {
        setHeroPainting(null);
      } finally {
        setLoading(false);
      }
    };

    loadHero();
  }, []);

  const resolvedImage = resolveImageUrl(heroPainting?.image_url ?? null);

  return (
    <main className="page-shell">
      <div className="container intro-page">
        <div className="card intro-card">
          {loading ? (
            <div className="intro-image" style={{ background: "#efe6dc" }} />
          ) : (
            <img
              src={resolvedImage ?? paintingAssets.dancers.src}
              alt={heroPainting?.alt || heroPainting?.title || "Painting preview"}
              className="intro-image"
            />
          )}
        </div>
        <div className="intro-content">
          <div>
            <span className="eyebrow">How it works</span>
            <h1 className="title">A guided art comparison</h1>
            <p className="subtitle">
              Choose a curated set, select two paintings, and receive an elegant summary of how the
              artworks relate. The flow is designed to keep you focused on visual discovery.
            </p>
          </div>
          <div className="button-row">
            <Button
              text="Next"
              classname="main-btn"
              onClick={() => router.push("/option")}
            />
          </div>
        </div>
      </div>
      <Icons nav="/" />
    </main>
  );
}