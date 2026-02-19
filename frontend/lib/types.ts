export interface SetSummary {
  set_id: string;
  label: string;
  count: number;
}

export interface Painting {
  id: string;
  title: string;
  artist: string;
  year: string | null;
  image_url: string | null;
  alt: string;
  metadata: Record<string, unknown> | null;
}

export interface CompareOverview {
  artworkA: Painting;
  artworkB: Painting;
}

export interface CompareResponse {
  overview: CompareOverview;
  summary: string;
}

export type DiagramEdgeKind = "direct" | "contextual" | "interpretive";

export type DiagramNodeType =
  | "artwork"
  | "niche_connection"
  | "artist"
  | "teacher"
  | "movement"
  | "theme"
  | "context"
  | "other";

export interface DiagramNode {
  id: string;
  type: DiagramNodeType;
  label: string;
  level: number;
  x?: number;
  y?: number;
}

export interface DiagramEdge {
  id: string;
  source: string;
  target: string;
  kind: DiagramEdgeKind;
  label?: string | null;
}

export interface DiagramLayout {
  direction: "TB";
  hint_text?: string | null;
}

export interface DiagramPayload {
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  layout?: DiagramLayout | null;
}

export interface CompareJobResponse {
  status: string;
  summary_markdown?: string | null;
  diagram?: DiagramPayload | null;
}
