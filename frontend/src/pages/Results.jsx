import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CytoscapeDiagram from "../components/CytoscapeDiagram";
import { useAppState } from "../AppContext";

const API_BASE = "http://localhost:8000";

export default function Results() {
  const navigate = useNavigate();
  const { compareId, setCompareId } = useAppState();
  const [status, setStatus] = useState({ status: "processing" });

  useEffect(() => {
    if (!compareId) {
      navigate("/choose-set");
      return;
    }

    let intervalId;
    let active = true;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/compare/${compareId}`);
        const data = await res.json();
        if (!active) return;
        setStatus(data);
        if (data.status === "done" || data.status === "error") {
          window.clearInterval(intervalId);
        }
      } catch (error) {
        if (active) {
          setStatus({ status: "error", error_message: "Failed to fetch results." });
          window.clearInterval(intervalId);
        }
      }
    };

    poll();
    intervalId = window.setInterval(poll, 1000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [compareId, navigate]);

  const resetFlow = () => {
    setCompareId("");
    navigate("/choose-set");
  };

  return (
    <section>
      <h2>Results</h2>
      {status.status === "error" && (
        <div>
          <p style={{ color: "crimson" }}>{status.error_message || "Error."}</p>
          <button type="button" onClick={resetFlow}>
            Start over
          </button>
        </div>
      )}
      {status.status !== "error" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          <div>
            <h3>Summary</h3>
            {status.status === "processing" && <p>Generating summary...</p>}
            {status.status !== "processing" && (
              <div style={{ whiteSpace: "pre-wrap" }}>
                {status.summary_markdown}
              </div>
            )}
          </div>
          <div>
            <h3>Diagram</h3>
            {status.status !== "done" && <p>Currently rendering your visual...</p>}
            {status.status === "done" && status.diagram && (
              <CytoscapeDiagram diagramJson={status.diagram} />
            )}
          </div>
        </div>
      )}
    </section>
  );
}