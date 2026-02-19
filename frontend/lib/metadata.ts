import { cache } from "react";
import { promises as fs } from "fs";
import path from "path";
export interface PaintingMeta {
  id: string;
  set: string;
  title: string;
  artist: string;
  year: string | null;
  filename: string;
}

const csvPathCandidates = [
  path.join(process.cwd(), "Painting_Metadata_260127.csv"),
  path.join(process.cwd(), "..", "Painting_Metadata_260127.csv"),
];

async function resolveCsvPath(): Promise<string> {
  for (const candidate of csvPathCandidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      continue;
    }
  }
  return csvPathCandidates[0];
}

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") {
        i += 1;
      }
      row.push(field);
      if (row.some((value) => value.length > 0)) {
        rows.push(row);
      }
      row = [];
      field = "";
      continue;
    }

    field += char;
  }

  row.push(field);
  if (row.some((value) => value.length > 0)) {
    rows.push(row);
  }

  return rows;
}

function normalizeText(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

export const getPaintingMetadata = cache(async (): Promise<PaintingMeta[]> => {
  const csvPath = await resolveCsvPath();
  const csvContent = await fs.readFile(csvPath, "utf8");

  const rows = parseCsv(csvContent);
  if (!rows.length) return [];

  const headers = rows[0].map((header) => header.trim().toLowerCase());
  const records = rows.slice(1).map((row) => {
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = row[index]?.trim() ?? "";
    });
    return record;
  });

  return records
    .map((record) => {
      const setValue = normalizeText(record["set"] ?? "").toUpperCase();
      const title = normalizeText(record["title"] ?? record["title "] ?? "");
      const artist = normalizeText(record["artist"] ?? "");
      const year = normalizeText(record["year"] ?? "") || null;
      const id = normalizeText(record["id"] ?? "");

      if (!id || !title || !setValue) {
        return null;
      }

      const filename = `${id}.jpg`;

      return {
        id,
        set: setValue,
        title,
        artist,
        year,
        filename,
      } satisfies PaintingMeta;
    })
    .filter((record): record is PaintingMeta => Boolean(record));
});
