import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const paintingsDir = path.join(process.cwd(), "assets", "paintings");

export async function GET(
  _request: Request,
  { params }: { params: { filename: string } }
) {
  const filename = params.filename;
  if (!filename || filename.includes("..") || filename.includes("/")) {
    return new NextResponse("Not found", { status: 404 });
  }

  const filePath = path.join(paintingsDir, filename);

  try {
    const data = await fs.readFile(filePath);
    return new NextResponse(data, {
      status: 200,
      headers: {
        "Content-Type": "image/jpeg",
        "Cache-Control": "public, max-age=31536000, immutable",
      },
    });
  } catch (error) {
    return new NextResponse("Not found", { status: 404 });
  }
}