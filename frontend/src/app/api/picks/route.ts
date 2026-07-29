import { NextRequest, NextResponse } from "next/server";

import { listOperationalPicks } from "@/lib/picks";

export async function GET(req: NextRequest) {
  const season = Number(req.nextUrl.searchParams.get("season"));
  const week = Number(req.nextUrl.searchParams.get("week"));

  if (!Number.isFinite(season) || !Number.isFinite(week)) {
    return NextResponse.json({ error: "Invalid season or week" }, { status: 400 });
  }

  return NextResponse.json({ picks: listOperationalPicks(season, week) });
}
