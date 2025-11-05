import "server-only";

import fs from "node:fs";
import path from "node:path";

export type WeekIdentifier = {
  season: number;
  week: number;
  folder: string;
};

export type MatchupSummary = {
  slug: string;
  title: string;
  filePath: string;
};

export type ManifestFileEntry = {
  path: string;
  sha256: string;
  size: number;
};

export type MatchupManifest = {
  markdown?: ManifestFileEntry;
  assets: ManifestFileEntry[];
};

const repoRoot = path.resolve(process.cwd(), "..");
const comparisonsDir = path.join(repoRoot, "data", "reports", "comparisons");

const WEEK_FOLDER_REGEX = /^(\d+)_w(\d+)$/i;

export function listAvailableWeeks(): WeekIdentifier[] {
  if (!fs.existsSync(comparisonsDir)) {
    return [];
  }

  const entries = fs.readdirSync(comparisonsDir, { withFileTypes: true });
  const weeks: WeekIdentifier[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const match = entry.name.match(WEEK_FOLDER_REGEX);
    if (!match) continue;

    const [, seasonStr, weekStr] = match;
    const season = Number(seasonStr);
    const week = Number(weekStr);
    if (!Number.isFinite(season) || !Number.isFinite(week)) continue;

    weeks.push({
      season,
      week,
      folder: entry.name,
    });
  }

  return weeks.sort((a, b) => {
    if (a.season === b.season) {
      return b.week - a.week;
    }
    return b.season - a.season;
  });
}

export function listMatchupsForWeek(season: number, week: number): MatchupSummary[] {
  const folderName = `${season}_w${week}`;
  const folderPath = path.join(comparisonsDir, folderName);

  if (!fs.existsSync(folderPath)) {
    return [];
  }

  const entries = fs.readdirSync(folderPath, { withFileTypes: true });
  const matchups: MatchupSummary[] = [];

  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (!entry.name.endsWith(".md")) continue;

    const slug = entry.name.replace(/\.md$/i, "");
    const title = slug.replace(/_/g, " ").replace(/\bvs\b/i, "vs");

    matchups.push({
      slug,
      title,
      filePath: path.join(folderPath, entry.name),
    });
  }

  return matchups.sort((a, b) => a.title.localeCompare(b.title));
}

export function loadMatchupMarkdown(season: number, week: number, slug: string): string {
  const folderName = `${season}_w${week}`;
  const filePath = path.join(comparisonsDir, folderName, `${slug}.md`);

  if (!fs.existsSync(filePath)) {
    throw new Error(`Report not found for ${season} week ${week} matchup ${slug}`);
  }

  return fs.readFileSync(filePath, "utf-8");
}

export function loadMatchupManifest(
  season: number,
  week: number,
  slug: string,
): MatchupManifest | null {
  const folderName = `${season}_w${week}`;
  const manifestPath = path.join(comparisonsDir, folderName, "manifest.json");

  if (!fs.existsSync(manifestPath)) {
    return null;
  }

  try {
    const payload = JSON.parse(
      fs.readFileSync(manifestPath, "utf-8"),
    ) as {
      files: ManifestFileEntry[];
    };

    const markdownEntry = payload.files.find((file) =>
      file.path.endsWith(`${slug}.md`),
    );

    const assetEntries = payload.files.filter((file) =>
      file.path.includes(path.join("assets", slug)),
    );

    return {
      markdown: markdownEntry,
      assets: assetEntries,
    };
  } catch (error) {
    console.error("Failed to parse manifest:", error);
    return null;
  }
}
