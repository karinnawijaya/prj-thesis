import { notFound } from "next/navigation";
import { Icons } from "@/components/gallery/Icons";
import { getPaintingMetadata } from "@/lib/metadata";
import { SetSelectionClient } from "../[setId]/selection-client";
import "../../styles/option.css";

interface SetDetailPageProps {
  params: { setId: string };
}

export default async function SetDetailPage({ params }: SetDetailPageProps) {
  const normalizedSetId = params.setId.toUpperCase();
  if (!normalizedSetId) {
    notFound();
  }

  const paintings = await getPaintingMetadata();
  const setPaintings = paintings.filter((painting) => painting.set === normalizedSetId);

  if (setPaintings.length === 0) {
    return (
      <main className="page-shell">
        <div className="container option-page">
          <div className="card" style={{ padding: "24px" }}>
            <p className="option-hint">Set {normalizedSetId} is not available.</p>
          </div>
        </div>
        <Icons nav="/sets" />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <SetSelectionClient setId={normalizedSetId} paintings={setPaintings} />
      <Icons nav="/sets" />
    </main>
  );
}