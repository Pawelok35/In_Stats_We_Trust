import { NextRequest, NextResponse } from "next/server";

import { listMatchupsForWeek } from "@/lib/reports";

export async function GET(req: NextRequest) {
  const seasonParam = req.nextUrl.searchParams.get("season");
  const weekParam = req.nextUrl.searchParams.get("week");

  const season = Number(seasonParam);
  const week = Number(weekParam);

  if (!Number.isFinite(season) || !Number.isFinite(week)) {
    return NextResponse.json({ error: "Invalid season or week" }, { status: 400 });
  }

  const matchups = listMatchupsForWeek(season, week);
  return NextResponse.json({ matchups });
}
