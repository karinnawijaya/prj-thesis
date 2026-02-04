"use client";

import type { Painting } from "@/lib/types";
import { resolveImageUrl } from "@/lib/images";

interface PaintingCardProps {
  painting: Painting;
  selected?: boolean;
  onClick?: () => void;
}

export function PaintingCard({ painting, selected = false, onClick }: PaintingCardProps) {
  const resolvedImage = resolveImageUrl(painting.image_url);
  const hasImage = Boolean(resolvedImage);
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative flex w-full flex-col overflow-hidden rounded-2xl border bg-white text-left shadow-soft transition hover:-translate-y-1 ${
        selected ? "border-indigo-500 ring-2 ring-indigo-200" : "border-transparent"
      }`}
    >
      <div className="relative h-40 w-full bg-slate-100">
        {hasImage ? (
          <img
            src={resolvedImage ?? ""}
            alt={painting.alt || painting.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-slate-400">
            Image coming soon
          </div>
        )}
        {selected ? (
          <div className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-white">
            <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 10l3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        ) : null}
      </div>
      <div className="flex flex-1 flex-col gap-1 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">{painting.title}</h3>
        <p className="text-xs text-slate-500">
          {painting.artist}
          {painting.year ? ` • ${painting.year}` : ""}
        </p>
      </div>
    </button>
  );
}