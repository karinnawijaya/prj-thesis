"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import type { PaintingMeta } from "@/lib/metadata";

interface SetSelectionClientProps {
  setId: string;
  paintings: PaintingMeta[];
}

export function SetSelectionClient({ setId, paintings }: SetSelectionClientProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>([]);

  const displayedPaintings = useMemo(() => paintings.slice(0, 5), [paintings]);

  const toggleSelection = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      if (prev.length >= 2) {
        return prev;
      }
      return [...prev, id];
    });
  };

  const readyToCompare = selected.length === 2;

  const handleCompare = () => {
    if (!readyToCompare) return;
    const [left, right] = selected;
    router.push(`/compare?left=${left}&right=${right}&set=${setId}`);
  };

  return (
    <div className="container option-page">
      <div>
        <span className="eyebrow">Set {setId}</span>
        <h1 className="title">Choose two paintings</h1>
        <p className="subtitle">
          Find meaningful connections from these curated artworks
        </p>
      </div>

      <div className="gallery-grid five-grid">
        {displayedPaintings.map((painting) => {
          const isSelected = selected.includes(painting.id);
          return (
            <button
              key={painting.id}
              type="button"
              className={`option-card${isSelected ? " selected" : ""}`}
              onClick={() => toggleSelection(painting.id)}
            >
              <img
                src={`/api/paintings/${encodeURIComponent(painting.filename)}`}
                alt={painting.title}
                className="option-image"
              />
              <div className="option-meta">
                <h3>{painting.title}</h3>
                <p>
                  {painting.artist}
                  {painting.year ? ` • ${painting.year}` : ""}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="option-actions">
        <span className="option-hint">{selected.length}/2 selected</span>
        <Button
          text="Compare"
          classname="main-btn"
          onClick={handleCompare}
          disabled={!readyToCompare}
        />
      </div>
    </div>
  );
}