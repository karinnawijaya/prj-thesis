import type { DiagramPayload } from "./types";

export const mockDiagram: DiagramPayload = {
  nodes: [
    {
      id: "artworkA",
      type: "artwork",
      label: "Artwork A — Sample A, Artist A, 1874",
      level: 0,
    },
    {
      id: "artworkB",
      type: "artwork",
      label: "Artwork B — Sample B, Artist B, 1872",
      level: 0,
    },
    {
      id: "L1",
      type: "niche_connection",
      label: "Shared river setting",
      level: 1,
    },
    {
      id: "L2",
      type: "movement",
      label: "Impressionist movement",
      level: 2,
    },
    {
      id: "L3",
      type: "artist",
      label: "Édouard Manet",
      level: 3,
    },
    {
      id: "L4",
      type: "movement",
      label: "Impressionism",
      level: 4,
    },
  ],
  edges: [
    {
      id: "edge-1",
      source: "artworkA",
      target: "L1",
      kind: "direct",
    },
    {
      id: "edge-2",
      source: "artworkB",
      target: "L1",
      kind: "direct",
    },
    {
      id: "edge-3",
      source: "L1",
      target: "L2",
      kind: "contextual",
    },
    {
      id: "edge-4",
      source: "artworkA",
      target: "L3",
      kind: "contextual",
    },
    {
      id: "edge-5",
      source: "artworkB",
      target: "L3",
      kind: "contextual",
    },
    {
      id: "edge-6",
      source: "artworkA",
      target: "L4",
      kind: "contextual",
    },
    {
      id: "edge-7",
      source: "artworkB",
      target: "L4",
      kind: "contextual",
    },
  ],
  layout: { direction: "TB", hint_text: "artworks top, L1 center, L2 below" },
};
