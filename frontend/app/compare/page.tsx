import { Icons } from "@/components/gallery/Icons";
import { getPaintingMetadata } from "@/lib/metadata";
import { CompareClient } from "./summary-client";
import "../styles/result.css";

interface ComparePageProps {
  searchParams: { left?: string; right?: string; set?: string };
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const paintings = await getPaintingMetadata();
  const leftId = searchParams.left ?? "";
  const rightId = searchParams.right ?? "";
  const setId = searchParams.set ?? "";

  const leftPainting = paintings.find((painting) => painting.id === leftId) ?? null;
  const rightPainting = paintings.find((painting) => painting.id === rightId) ?? null;

  return (
    <main className="page-shell">
      <CompareClient
        leftId={leftId}
        rightId={rightId}
        setId={setId}
        leftPainting={leftPainting}
        rightPainting={rightPainting}
      />
      <Icons nav={setId ? `/sets/${setId}` : "/sets"} />
    </main>
  );
}