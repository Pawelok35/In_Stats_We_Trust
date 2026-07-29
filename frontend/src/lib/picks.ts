import "server-only";

import fs from "node:fs";
import path from "node:path";

import type { OperationalPick, PickDecision } from "@/lib/pick-types";

const repoRoot = path.resolve(process.cwd(), "..");
const variantsConfigPath = path.join(repoRoot, "config", "tag_variants.yaml");

type VariantConfig = {
  name: string;
  status: string;
  picksDir: string;
};

type RawPick = Record<string, unknown>;

export function listOperationalPicks(season: number, week: number): OperationalPick[] {
  const variants = listVariantConfigs();
  const picks: OperationalPick[] = [];

  for (const variant of variants) {
    const filePath = path.join(repoRoot, variant.picksDir, String(season), `week_${padWeek(week)}.jsonl`);
    if (!fs.existsSync(filePath)) continue;

    const lines = fs.readFileSync(filePath, "utf-8").split(/\r?\n/).filter(Boolean);
    for (const [index, line] of lines.entries()) {
      const raw = JSON.parse(line) as RawPick;
      picks.push(toOperationalPick(raw, variant, index));
    }
  }

  return picks.sort((a, b) => {
    const statusRank = statusOrder(a.variantStatus) - statusOrder(b.variantStatus);
    if (statusRank !== 0) return statusRank;
    return Math.abs(b.edgeVsLine ?? 0) - Math.abs(a.edgeVsLine ?? 0);
  });
}

function listVariantConfigs(): VariantConfig[] {
  if (!fs.existsSync(variantsConfigPath)) {
    return [{ name: "baseline", status: "champion", picksDir: "data/picks" }];
  }

  const lines = fs.readFileSync(variantsConfigPath, "utf-8").split(/\r?\n/);
  const variants: VariantConfig[] = [];
  let current: Partial<VariantConfig> | null = null;

  for (const line of lines) {
    const nameMatch = line.match(/^\s*-\s+name:\s*(.+)\s*$/);
    if (nameMatch) {
      if (current?.name && current?.picksDir) {
        variants.push({
          name: current.name,
          status: current.status ?? "experimental",
          picksDir: current.picksDir,
        });
      }
      current = { name: cleanYamlValue(nameMatch[1]) };
      continue;
    }

    if (!current) continue;
    const statusMatch = line.match(/^\s*status:\s*(.+)\s*$/);
    if (statusMatch) {
      current.status = cleanYamlValue(statusMatch[1]);
      continue;
    }

    const picksDirMatch = line.match(/^\s*picks_dir:\s*(.+)\s*$/);
    if (picksDirMatch) {
      current.picksDir = cleanYamlValue(picksDirMatch[1]);
    }
  }

  if (current?.name && current?.picksDir) {
    variants.push({
      name: current.name,
      status: current.status ?? "experimental",
      picksDir: current.picksDir,
    });
  }

  return variants;
}

function toOperationalPick(raw: RawPick, variant: VariantConfig, index: number): OperationalPick {
  const season = Number(raw.season);
  const week = Number(raw.week);
  const home = String(raw.home ?? "").toUpperCase();
  const away = String(raw.away ?? "").toUpperCase();
  const tag = String(raw.tag ?? "UNKNOWN").toUpperCase();
  const edgeVsLine = toNumber(raw.edge_vs_line);
  const confidence = toNumber(raw.confidence);
  const slug = `${home}_vs_${away}`;

  return {
    id: `${variant.name}-${season}-${week}-${home}-${away}-${index}`,
    season,
    week,
    variant: variant.name,
    variantStatus: variant.status,
    home,
    away,
    matchup: `${home} vs ${away}`,
    tag,
    modelWinner: String(raw.model_winner ?? "").toUpperCase(),
    marketWinner: raw.market_winner ? String(raw.market_winner).toUpperCase() : undefined,
    confidence,
    edgeVsLine,
    handicap: toNumber(raw.handicap),
    spread: toNumber(raw.spread),
    total: toNumber(raw.total),
    window: raw.window ? String(raw.window) : undefined,
    report: raw.report ? String(raw.report) : undefined,
    slug,
    decision: decisionFor(tag, confidence, edgeVsLine),
    modelVersion: raw.model_version ? String(raw.model_version) : undefined,
    dataCutoff: raw.data_cutoff ? String(raw.data_cutoff) : undefined,
    commitSha: raw.commit_sha ? String(raw.commit_sha) : undefined,
    configSha256: raw.config_sha256 ? String(raw.config_sha256) : undefined,
    generatedAt: raw.generated_at ? String(raw.generated_at) : undefined,
  };
}

function decisionFor(tag: string, confidence: number | null, edge: number | null): PickDecision {
  const edgeAbs = Math.abs(edge ?? 0);
  if (tag === "GOY" || tag === "GOM") return "bet";
  if (tag === "GOW" || tag === "VALUE PLAY") return "lean";
  if ((confidence ?? 0) >= 90 && edgeAbs >= 10) return "lean";
  if (tag === "NEUTRAL") return "avoid";
  return "no bet";
}

function statusOrder(status: string) {
  if (status === "champion") return 0;
  if (status === "challenger") return 1;
  if (status === "experimental") return 2;
  return 3;
}

function toNumber(value: unknown): number | null {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function cleanYamlValue(value: string) {
  return value.trim().replace(/^["']|["']$/g, "");
}

function padWeek(week: number) {
  return String(week).padStart(2, "0");
}
