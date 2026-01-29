import { useNavigate } from "react-router-dom";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <section>
      <h1>ArtWeave</h1>
      <p>Explore connections between paintings through AI-assisted comparisons.</p>
      <button type="button" onClick={() => navigate("/tutorial")}>
        Next
      </button>
    </section>
  );
}