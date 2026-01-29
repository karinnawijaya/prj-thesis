import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

export default function CytoscapeDiagram({ diagramJson }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!diagramJson || !containerRef.current) return undefined;

    const cy = cytoscape({
      container: containerRef.current,
      elements: diagramJson.elements,
      layout: diagramJson.layout,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-wrap": "wrap",
            "text-max-width": 140,
            "font-size": 12,
          },
        },
        {
          selector: "edge",
          style: {
            label: "data(label)",
            "font-size": 10,
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
          },
        },
      ],
    });

    return () => {
      cy.destroy();
    };
  }, [diagramJson]);

  return <div ref={containerRef} style={{ width: "100%", height: 480 }} />;
}