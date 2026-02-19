import { NextResponse } from "next/server";
import { getPaintingMetadata } from "@/lib/metadata";

export async function GET() {
  const paintings = await getPaintingMetadata();
  return NextResponse.json({ paintings });
}