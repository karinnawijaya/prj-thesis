"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { GalleryImage } from "@/components/gallery/GalleryImage";
import { paintingAssets } from "@/lib/paintingAssets";
import "./styles/home.css";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="page-shell">
      <div className="container home-page">
        <div className="home-content">
          <h1 className="title">ArtWeave</h1>
          <p className="subtitle">
            Step into a curated gallery of masterpieces. Compare two paintings side by side and
            discover concise insights in a warm, guided flow.
          </p>
          <Button
            text="Let’s Begin"
            classname="main-btn"
            onClick={() => router.push("/intro")}
          />
        </div>
        <div className="home-images">
          <GalleryImage src={paintingAssets.tuileries.src} className="top" alt="The Tuileries" />
          <GalleryImage src={paintingAssets.seashore.src} className="left" alt="By the Seashore" />
          <GalleryImage src={paintingAssets.bridge.src} className="right" alt="The Bridge" />
        </div>
      </div>
    </main>
  );
}