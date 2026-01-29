import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppState } from "../AppContext";

const API_BASE = "http://localhost:8000";

export default function ChoosePaintings() {
  const navigate = useNavigate();
  const { selectedSet, setCompareId } = useAppState();
  const [paintings, setPaintings] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedSet) {
      navigate("/choose-set");
      return;
    }

    let active = true;
    setLoading(true);
    setMessage("");
    setSelectedIds([]);

    fetch(`${API_BASE}/api/paintings?set=${selectedSet}`)
      .then((res) => res.json())
      .then((data) => {
        if (active) {
          setPaintings(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setMessage("Failed to load paintings.");
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedSet, navigate]);

  const selectedSetLabel = useMemo(
    () => (selectedSet ? `Set ${selectedSet}` : ""),
    [selectedSet]
  );

  const toggleSelection = (id) => {
    setMessage("");
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((pid) => pid !== id));
      return;
    }
    if (selectedIds.length >= 2) {
      setMessage("You can only select 2 paintings. Unselect one first.");
      return;
    }
    setSelectedIds([...selectedIds, id]);
  };

  const handleNext = async () => {
    const [left_id, right_id] = selectedIds;
    const res = await fetch(`${API_BASE}/api/compare/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ set: selectedSet, left_id, right_id }),
    });
    const data = await res.json();
    if (data.compare_id) {
      setCompareId(data.compare_id);
      navigate("/results");
      return;
    }
    setMessage("Unable to start comparison.");
  };

  return (
    <section>
      <h2>Choose 2 paintings ({selectedSetLabel})</h2>
      {message && <p style={{ color: "crimson" }}>{message}</p>}
      {loading && <p>Loading paintings...</p>}
      {!loading && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 16,
          }}
        >
          {paintings.map((painting) => {
            const isSelected = selectedIds.includes(painting.id);
            return (
              <button
                key={painting.id}
                type="button"
                onClick={() => toggleSelection(painting.id)}
                style={{
                  border: isSelected ? "2px solid #1f6feb" : "1px solid #ddd",
                  padding: 8,
                  textAlign: "left",
                  background: isSelected ? "#eef4ff" : "white",
                }}
              >
                <img
                  src={painting.image_url}
                  alt={painting.title}
                  style={{ width: "100%", height: 120, objectFit: "cover" }}
                />
                <div style={{ marginTop: 6 }}>
                  <strong>{painting.title}</strong>
                  <div>{painting.artist}</div>
                  <div>{painting.year}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
      <div style={{ marginTop: 16 }}>
        <button type="button" onClick={handleNext} disabled={selectedIds.length !== 2}>
          Proceed
        </button>
      </div>
    </section>
  );
}