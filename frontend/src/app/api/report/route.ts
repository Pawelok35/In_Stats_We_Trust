import { NextRequest, NextResponse } from "next/server";

import { parseMatchupReport } from "@/lib/markdown-parser";
import { loadMatchupMarkdown } from "@/lib/reports";

export async function GET(req: NextRequest) {
  const seasonParam = req.nextUrl.searchParams.get("season");
  const weekParam = req.nextUrl.searchParams.get("week");
  const slug = req.nextUrl.searchParams.get("slug");

  const season = Number(seasonParam);
  const week = Number(weekParam);

  if (!Number.isFinite(season) || !Number.isFinite(week) || !slug) {
    return NextResponse.json({ error: "Missing season, week or slug" }, { status: 400 });
  }

  try {
    const markdown = loadMatchupMarkdown(season, week, slug);
    const parsed = parseMatchupReport(slug, markdown);
    return NextResponse.json({ report: parsed });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Report not found" }, { status: 404 });
  }
}
