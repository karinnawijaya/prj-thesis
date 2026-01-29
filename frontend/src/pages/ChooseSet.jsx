import { useNavigate } from "react-router-dom";
import { useAppState } from "../AppContext";

export default function ChooseSet() {
  const navigate = useNavigate();
  const { selectedSet, setSelectedSet } = useAppState();

  return (
    <section>
      <h2>Choose a Set</h2>
      <div style={{ display: "flex", gap: 12 }}>
        <button
          type="button"
          onClick={() => setSelectedSet("A")}
          aria-pressed={selectedSet === "A"}
        >
          Set A
        </button>
        <button
          type="button"
          onClick={() => setSelectedSet("B")}
          aria-pressed={selectedSet === "B"}
        >
          Set B
        </button>
      </div>
      <div style={{ marginTop: 16 }}>
        <button
          type="button"
          onClick={() => navigate("/choose-paintings")}
          disabled={!selectedSet}
        >
          Next
        </button>
      </div>
    </section>
  );
}