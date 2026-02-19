import ELK from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "reactflow";

interface LayoutOptions {
  direction?: "DOWN";
  nodeSpacing?: number;
  layerSpacing?: number;
}

const elk = new ELK();

export async function layoutGraphWithElk(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
) {
  const direction = options.direction ?? "DOWN";
  const nodeSpacing = options.nodeSpacing ?? 140;
  const layerSpacing = options.layerSpacing ?? 180;

  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": direction,
      "elk.spacing.nodeNode": String(nodeSpacing),
      "elk.layered.spacing.nodeNodeBetweenLayers": String(layerSpacing),
      "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: node.width ?? 200,
      height: node.height ?? 80,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await elk.layout(graph);
  const positions = new Map<string, { x: number; y: number }>();

  layout.children?.forEach((child) => {
    if (child.x == null || child.y == null) return;
    positions.set(child.id, { x: child.x, y: child.y });
  });

  const layoutedNodes = nodes.map((node) => {
    const position = positions.get(node.id) ?? node.position ?? { x: 0, y: 0 };
    return {
      ...node,
      position,
    };
  });

  return layoutedNodes;
}
