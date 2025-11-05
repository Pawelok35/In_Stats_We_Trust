import { NextRequest, NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";

const repoRoot = path.resolve(process.cwd(), "..");
const comparisonsDir = path.join(repoRoot, "data", "reports", "comparisons");

type AssetParams = {
  season: string;
  week: string;
  slug: string;
  filename: string[];
};

export async function GET(
  _request: NextRequest,
  context: { params: Promise<AssetParams> },
) {
  const {
    season: seasonParam,
    week: weekParam,
    slug,
    filename: filenameParts,
  } = await context.params;

  const season = Number(seasonParam);
  const week = Number(weekParam);

  if (!Number.isFinite(season) || !Number.isFinite(week) || !slug) {
    return NextResponse.json({ detail: "Invalid path parameters" }, { status: 400 });
  }

  const filename = (filenameParts ?? []).join("/");
  const folderName = `${season}_w${week}`;
  const assetPath = path.join(
    comparisonsDir,
    folderName,
    "assets",
    slug,
    filename,
  );

  if (!fs.existsSync(assetPath) || !fs.statSync(assetPath).isFile()) {
    return NextResponse.json({ detail: "Asset not found" }, { status: 404 });
  }

  const file = fs.readFileSync(assetPath);
  const extension = path.extname(filename).toLowerCase();
  const mimeType = mimeFromExtension(extension) ?? "application/octet-stream";

  return new NextResponse(file, {
    headers: {
      "Content-Type": mimeType,
      "Cache-Control": "public, max-age=60",
    },
  });
}

function mimeFromExtension(ext: string): string | undefined {
  switch (ext) {
    case ".png":
      return "image/png";
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".webp":
      return "image/webp";
    case ".svg":
      return "image/svg+xml";
    case ".json":
      return "application/json";
    default:
      return undefined;
  }
}
