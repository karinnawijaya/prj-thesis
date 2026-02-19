"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dagre from "dagre";
import ReactFlow, {
  Background,
  type Edge,
  Handle,
  MarkerType,
  type Node,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Button } from "@/components/ui/Button";
import type { PaintingMeta } from "@/lib/metadata";
import type {
  CompareJobResponse,
  DiagramEdge,
  DiagramNode,
  DiagramNodeType,
  DiagramPayload,
} from "@/lib/types";

interface CompareClientProps {
  leftId: string;
  rightId: string;
  setId: string;
  leftPainting: PaintingMeta | null;
  rightPainting: PaintingMeta | null;
}

interface ArtworkInfo {
  id: string;
  title: string;
  artist: string;
  year: string | null;
  imageUrl: string;
}

const ARTWORK_NODE_WIDTH = 220;
const ARTWORK_NODE_HEIGHT = 230;
const CATEGORY_NODE_WIDTH = 200;
const CATEGORY_NODE_HEIGHT = 70;
const TOP_ROW_Y = 20;
const ROW_SPACING = 260;
const NODESEP = 140;
const RANKSEP = 200;

const categoryPalette = {
  niche_connection: { bg: "#cfe6ff", border: "#2f7bdc", text: "#1b3f70" },
  artist: { bg: "#ffd9bf", border: "#f08c3a", text: "#7c3e10" },
  teacher: { bg: "#ffe8d6", border: "#d9a06a", text: "#6f3f18" },
  movement: { bg: "#bfeee7", border: "#20b39c", text: "#0f5b51" },
  theme: { bg: "#efe3ff", border: "#b294f4", text: "#4b2c7a" },
  context: { bg: "#ffe8d6", border: "#d9a06a", text: "#6f3f18" },
  other: { bg: "#ececec", border: "#b7b7b7", text: "#4b4b4b" },
};

function formatArtworkLine(artwork: ArtworkInfo) {
  const parts = [artwork.title, artwork.artist, artwork.year].filter(Boolean);
  return parts.join(", ");
}

function inferCategory(node: DiagramNode): keyof typeof categoryPalette {
  const type = node.type?.toLowerCase() as DiagramNodeType | undefined;
  if (type === "niche_connection" || node.level === 1) return "niche_connection";
  if (type === "artist") return "artist";
  if (type === "teacher") return "teacher";
  if (type === "movement") return "movement";
  if (type === "theme") return "theme";
  if (type === "context") return "context";
  return "other";
}

function truncateLabel(label: string) {
  const trimmed = label.trim();
  if (trimmed.length <= 42) {
    return insertLineBreak(trimmed);
  }
  return insertLineBreak(`${trimmed.slice(0, 39)}...`);
}

function insertLineBreak(label: string) {
  if (label.length <= 24) return label;
  const mid = Math.min(24, label.length - 1);
  const splitAt = label.lastIndexOf(" ", mid);
  if (splitAt <= 0) return label;
  return `${label.slice(0, splitAt)}\n${label.slice(splitAt + 1)}`;
}

function extractComparisonSummary(text: string) {
  const marker = "**Comparison Summary**";
  const idx = text.indexOf(marker);
  if (idx === -1) return text.trim();
  const after = text.slice(idx + marker.length).trim();
  return after.replace(/^\s*[:\-]\s*/, "").trim();
}

function replaceArtworkLabels(
  summary: string,
  artworkA: ArtworkInfo,
  artworkB: ArtworkInfo
) {
  return summary
    .replace(/\bArtwork\s*A\b/gi, artworkA.title)
    .replace(/\bArtwork\s*B\b/gi, artworkB.title);
}

function normalizeDiagramPayload(payload: any): DiagramPayload | null {
  if (!payload) return null;
  if (Array.isArray(payload.nodes) && Array.isArray(payload.edges)) {
    return payload as DiagramPayload;
  }
  const elements = payload.elements;
  if (!elements || !Array.isArray(elements.nodes) || !Array.isArray(elements.edges)) {
    return null;
  }

    const nodes: DiagramNode[] = elements.nodes.map((node: any, index: number) => {
      const data = node.data ?? {};
      const id = data.id ?? `node-${index}`;
      const label = data.label ?? data.name ?? id;
      const level = 1;
      return {
        id,
        type: "niche_connection",
        label: String(label),
        level,
      };
    });

  const edges: DiagramEdge[] = elements.edges.map((edge: any, index: number) => {
    const data = edge.data ?? {};
    const id = data.id ?? `edge-${index}`;
    return {
      id,
      source: String(data.source ?? ""),
      target: String(data.target ?? ""),
      kind: "contextual",
      label: data.label ? String(data.label) : null,
    };
  });

  return { nodes, edges, layout: { direction: "TB" } };
}

function PaintingCardNode({ data }: { data: ArtworkInfo & { tag: string } }) {
  return (
    <div className="diagram-painting-card">
      <Handle type="target" position={Position.Top} className="diagram-handle" />
      <span className="diagram-card-tag">{data.tag}</span>
      <img src={data.imageUrl} alt={data.title} className="diagram-card-image" />
      <div className="diagram-card-title">{data.title}</div>
      <div className="diagram-card-meta">{data.year ?? ""}</div>
      <Handle type="source" position={Position.Bottom} className="diagram-handle" />
    </div>
  );
}

function CategoryNode({ data }: { data: DiagramNode }) {
  const palette = categoryPalette[inferCategory(data)];
  return (
    <div
      className="diagram-category-node"
      style={{
        background: palette.bg,
        borderColor: palette.border,
        color: palette.text,
      }}
    >
      <Handle type="target" position={Position.Top} className="diagram-handle" />
      {truncateLabel(String(data.label))}
      <Handle type="source" position={Position.Bottom} className="diagram-handle" />
    </div>
  );
}

function layoutWithDagre(nodes: DiagramNode[], edges: DiagramEdge[]): DiagramNode[] {
  const canvasWidth = 920;
  const padding = 80;
  const leftX = padding;
  const rightX = canvasWidth - ARTWORK_NODE_WIDTH - padding;
  const centerX =
    (leftX + ARTWORK_NODE_WIDTH + rightX) / 2 - CATEGORY_NODE_WIDTH / 2;

  const graph = new dagre.graphlib.Graph();
  graph.setGraph({
    rankdir: "TB",
    nodesep: NODESEP,
    ranksep: RANKSEP,
    marginx: 40,
    marginy: 20,
  });
  graph.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((node) => {
    const isArtwork = node.id === "artworkA" || node.id === "artworkB";
    graph.setNode(node.id, {
      width: isArtwork ? ARTWORK_NODE_WIDTH : CATEGORY_NODE_WIDTH,
      height: isArtwork ? ARTWORK_NODE_HEIGHT : CATEGORY_NODE_HEIGHT,
    });
  });

  edges.forEach((edge) => {
    if (nodes.find((n) => n.id === edge.source) && nodes.find((n) => n.id === edge.target)) {
      graph.setEdge(edge.source, edge.target);
    }
  });

  dagre.layout(graph);

  const mapped = nodes.map((node) => {
    const isArtwork = node.id === "artworkA" || node.id === "artworkB";
    const width = isArtwork ? ARTWORK_NODE_WIDTH : CATEGORY_NODE_WIDTH;
    const point = graph.node(node.id);
    const rowIndex =
      node.id === "artworkA" ||
      node.id === "artworkB" ||
      node.type === "niche_connection" ||
      node.level === 1
        ? 0
        : Math.max(1, node.level - 1);

    return {
      ...node,
      x: typeof point?.x === "number" ? point.x - width / 2 : node.x ?? 0,
      y: TOP_ROW_Y + ROW_SPACING * rowIndex,
    };
  });

  const artworkA = mapped.find((node) => node.id === "artworkA");
  const artworkB = mapped.find((node) => node.id === "artworkB");
  const l1 = mapped.find(
    (node) => node.type === "niche_connection" || node.level === 1
  );

  if (artworkA) {
    artworkA.x = leftX;
    artworkA.y = TOP_ROW_Y;
  }
  if (artworkB) {
    artworkB.x = rightX;
    artworkB.y = TOP_ROW_Y;
  }
  if (l1) {
    l1.x = centerX;
    l1.y = TOP_ROW_Y;
  }

  return mapped;
}

function OverviewPanel({
  artworkA,
  artworkB,
  summaryText,
  loading,
  error,
  onRetry,
}: {
  artworkA: ArtworkInfo;
  artworkB: ArtworkInfo;
  summaryText: string | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  return (
    <section className="card result-overview-card">
      <h2>Overview</h2>
      <div className="overview-lines">
        <div>
          <div className="overview-line-label">Artwork A</div>
          <div className="overview-line-text">{formatArtworkLine(artworkA)}</div>
        </div>
        <div>
          <div className="overview-line-label">Artwork B</div>
          <div className="overview-line-text">{formatArtworkLine(artworkB)}</div>
        </div>
      </div>
      <h2 className="summary-title">Summary</h2>
      {loading ? (
        <p>Generating summary...</p>
      ) : error ? (
        <div>
          <p className="option-hint">{error}</p>
          <div style={{ marginTop: "16px" }}>
            <Button text="Try again" classname="white-btn" onClick={onRetry} />
          </div>
        </div>
      ) : (
        <p>{summaryText ?? ""}</p>
      )}
      <span className="summary-footnote">AI generated</span>
    </section>
  );
}

function DiagramCanvas({
  diagram,
  artworkA,
  artworkB,
  loading,
}: {
  diagram: DiagramPayload | null;
  artworkA: ArtworkInfo;
  artworkB: ArtworkInfo;
  loading: boolean;
}) {
  const { nodes, edges } = useMemo(() => {
    if (!diagram || !Array.isArray(diagram.nodes) || !Array.isArray(diagram.edges)) {
      const fallbackNodes: Node[] = [
        {
          id: "artworkA",
          type: "paintingCard",
          data: { ...artworkA, tag: "Artwork A" },
          position: { x: 80, y: 20 },
          width: ARTWORK_NODE_WIDTH,
          height: ARTWORK_NODE_HEIGHT,
        },
        {
          id: "artworkB",
          type: "paintingCard",
          data: { ...artworkB, tag: "Artwork B" },
          position: { x: 620, y: 20 },
          width: ARTWORK_NODE_WIDTH,
          height: ARTWORK_NODE_HEIGHT,
        },
        {
          id: "L1",
          type: "category",
          data: {
            id: "L1",
            type: "niche_connection",
            label: "Connection could not be structured",
            level: 1,
          },
          position: { x: 360, y: 20 },
          width: CATEGORY_NODE_WIDTH,
          height: CATEGORY_NODE_HEIGHT,
        },
      ];
      const fallbackEdges: Edge[] = [
        {
          id: "edge-artworkA-L1",
          source: "artworkA",
          target: "L1",
          type: "step",
          markerEnd: { type: MarkerType.ArrowClosed, color: "#9e9e9e" },
          style: { stroke: "#9e9e9e", strokeWidth: 1.4 },
        },
        {
          id: "edge-artworkB-L1",
          source: "artworkB",
          target: "L1",
          type: "step",
          markerEnd: { type: MarkerType.ArrowClosed, color: "#9e9e9e" },
          style: { stroke: "#9e9e9e", strokeWidth: 1.4 },
        },
      ];
      return { nodes: fallbackNodes, edges: fallbackEdges };
    }

    const normalizedNodes = layoutWithDagre(diagram.nodes, diagram.edges);
    const nodeMap = new Map(normalizedNodes.map((node) => [node.id, node]));

    const flowNodes: Node[] = normalizedNodes.map((node) => {
      if (node.id === "artworkA") {
        return {
          id: node.id,
          type: "paintingCard",
          data: { ...artworkA, tag: "Artwork A" },
          position: {
            x: node.x ?? 0,
            y: node.y ?? 0,
          },
          width: ARTWORK_NODE_WIDTH,
          height: ARTWORK_NODE_HEIGHT,
        };
      }
      if (node.id === "artworkB") {
        return {
          id: node.id,
          type: "paintingCard",
          data: { ...artworkB, tag: "Artwork B" },
          position: {
            x: node.x ?? 0,
            y: node.y ?? 0,
          },
          width: ARTWORK_NODE_WIDTH,
          height: ARTWORK_NODE_HEIGHT,
        };
      }
      return {
        id: node.id,
        type: "category",
        data: node,
        position: {
          x: node.x ?? 0,
          y: node.y ?? 0,
        },
        width: CATEGORY_NODE_WIDTH,
        height: CATEGORY_NODE_HEIGHT,
      };
    });

    const flowEdges: Edge[] = diagram.edges
      .filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target))
      .map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "step",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#9e9e9e" },
        style: { stroke: "#9e9e9e", strokeWidth: 1.4 },
        label: edge.label ? truncateLabel(edge.label) : undefined,
        labelStyle: { fill: "#6b5f55", fontSize: 12, fontWeight: 500 },
        labelBgStyle: { fill: "#f7f2eb", fillOpacity: 0.9 },
        labelBgPadding: [4, 2],
        labelBgBorderRadius: 6,
      }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [diagram, artworkA, artworkB]);

  if (loading) {
    return (
      <div className="diagram-empty">
        <p>Generating diagram...</p>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="diagram-empty">
        <p>Diagram unavailable. Showing a fallback connection.</p>
      </div>
    );
  }

  return (
    <div className="diagram-scroll">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ paintingCard: PaintingCardNode, category: CategoryNode }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        panOnScroll={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background gap={24} size={1} color="#e6e0d9" />
      </ReactFlow>
    </div>
  );
}

export function CompareClient({
  leftId,
  rightId,
  setId,
  leftPainting,
  rightPainting,
}: CompareClientProps) {
  const [diagram, setDiagram] = useState<DiagramPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summaryText, setSummaryText] = useState<string | null>(null);

  useEffect(() => {
    if (process.env.NODE_ENV !== "production" && diagram) {
      console.assert(
        Array.isArray(diagram.nodes) && diagram.nodes.length > 0,
        "Diagram payload missing nodes.",
        diagram
      );
    }
  }, [diagram]);

  const runCompare = useCallback(async () => {
    if (!leftId || !rightId || !setId) {
      setError("Please select two paintings first.");
      setLoading(false);
      setSummaryText(null);
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);

    setLoading(true);
    setError(null);
    setSummaryText(null);
    setDiagram(null);

    try {
      const startResponse = await fetch("/api/compare/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          set: setId,
          left_id: leftId,
          right_id: rightId,
        }),
        signal: controller.signal,
      });

      if (!startResponse.ok) {
        const message = await startResponse.text();
        throw new Error(message || "Summary request failed.");
      }

      const startPayload = (await startResponse.json()) as { compare_id?: string };
      if (!startPayload.compare_id) {
        throw new Error("Unable to start comparison.");
      }

      let attempts = 0;
      let summaryFound = false;
      while (attempts < 20) {
        const statusResponse = await fetch(
          `/api/compare/${encodeURIComponent(startPayload.compare_id)}`,
          { signal: controller.signal }
        );
        if (!statusResponse.ok) {
          const message = await statusResponse.text();
          throw new Error(message || "Unable to fetch comparison.");
        }
        const payload = (await statusResponse.json()) as CompareJobResponse;
        if (process.env.NODE_ENV !== "production") {
          console.debug("Compare status payload:", payload);
        }
        if (payload.summary_markdown) {
          setSummaryText(extractComparisonSummary(payload.summary_markdown));
          summaryFound = true;
        }
        if (payload.diagram) {
          setDiagram(normalizeDiagramPayload(payload.diagram));
        }
        if (payload.status === "done") {
          setSummaryText(
            payload.summary_markdown
              ? extractComparisonSummary(payload.summary_markdown)
              : ""
          );
          setDiagram(normalizeDiagramPayload(payload.diagram));
          summaryFound = Boolean(payload.summary_markdown);
          break;
        }
        attempts += 1;
        await new Promise((resolve) => setTimeout(resolve, 900));
      }

      if (!summaryFound) {
        setSummaryText((prev) => prev ?? "Summary unavailable.");
      }
    } catch (err) {
      const message =
        (err as Error).name === "AbortError"
          ? "The summary request timed out."
          : (err as Error).message;
      setError(message);
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  }, [leftId, rightId, setId]);

  useEffect(() => {
    runCompare();
  }, [runCompare]);

  if (!leftPainting || !rightPainting) {
    return (
      <div className="container result-page">
        <div className="card result-overview-card">
          <h2>Overview</h2>
          <p className="option-hint">We could not locate the selected paintings.</p>
        </div>
      </div>
    );
  }

  const leftSrc = `/api/paintings/${encodeURIComponent(leftPainting.filename)}`;
  const rightSrc = `/api/paintings/${encodeURIComponent(rightPainting.filename)}`;

  const artworkA: ArtworkInfo = {
    id: leftPainting.id,
    title: leftPainting.title,
    artist: leftPainting.artist,
    year: leftPainting.year,
    imageUrl: leftSrc,
  };
  const artworkB: ArtworkInfo = {
    id: rightPainting.id,
    title: rightPainting.title,
    artist: rightPainting.artist,
    year: rightPainting.year,
    imageUrl: rightSrc,
  };

  const resolvedSummary = summaryText
    ? replaceArtworkLabels(summaryText, artworkA, artworkB)
    : summaryText;

  return (
    <div className="container result-page">
      <div className="result-layout">
        <OverviewPanel
          artworkA={artworkA}
          artworkB={artworkB}
          summaryText={resolvedSummary}
          loading={loading}
          error={error}
          onRetry={runCompare}
        />
        <section className="card diagram-card">
          <DiagramCanvas
            diagram={diagram}
            artworkA={artworkA}
            artworkB={artworkB}
            loading={loading}
          />
          {process.env.NODE_ENV !== "production" && diagram ? (
            <details className="diagram-debug">
              <summary>Diagram JSON (debug)</summary>
              <pre>{JSON.stringify(diagram, null, 2)}</pre>
            </details>
          ) : null}
        </section>
      </div>
    </div>
  );
}
