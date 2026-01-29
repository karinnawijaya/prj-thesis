import { useNavigate } from "react-router-dom";

export default function Tutorial() {
  const navigate = useNavigate();

  return (
    <section>
      <h2>Tutorial</h2>
      <ol>
        <li>Choose a painting set (A or B).</li>
        <li>Select exactly two paintings.</li>
        <li>Review the comparison summary and diagram.</li>
      </ol>
      <button type="button" onClick={() => navigate("/choose-set")}>
        Next
      </button>
    </section>
  );
}
