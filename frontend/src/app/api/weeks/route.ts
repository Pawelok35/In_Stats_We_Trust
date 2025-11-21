import { NextResponse } from "next/server";

import { listAvailableWeeks } from "@/lib/reports";

export async function GET() {
  const weeks = listAvailableWeeks();
  return NextResponse.json({ weeks });
}
