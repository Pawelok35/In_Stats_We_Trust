import "server-only";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Core12Row = {
  TEAM: string;
  season: number;
  week: number;
  core_epa_offense?: number;
  core_epa_defense?: number;
  success_rate_offense?: number;
  success_rate_defense?: number;
  explosive_play_rate_offense?: number;
  third_down_conversion_offense?: number;
  points_per_drive_diff?: number;
  yards_per_play_diff?: number;
  turnover_margin?: number;
  redzone_td_rate_offense?: number;
  pressure_rate_defense?: number;
  tempo?: number;
  [key: string]: unknown;
};

export async function fetchCore12Preview(params: {
  season: number;
  week: number;
  n?: number;
}): Promise<Core12Row[]> {
  const url = new URL("/metrics/core12/preview", API_BASE_URL);
  url.searchParams.set("season", String(params.season));
  url.searchParams.set("week", String(params.week));
  if (params.n) {
    url.searchParams.set("n", String(params.n));
  }

  const response = await fetch(url.toString(), {
    next: { revalidate: 60 },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `Core12 preview request failed (${response.status}): ${errorText}`,
    );
  }

  const data = (await response.json()) as Core12Row[];
  return data;
}
