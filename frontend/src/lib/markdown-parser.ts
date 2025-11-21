export type ParsedTable = {
  heading: string;
  headers: string[];
  rows: string[][];
};

export type ParsedReport = {
  slug: string;
  raw: string;
  teams: { home: string; away: string };
  tables: Record<string, ParsedTable>;
  sections: ParsedTable[];
  modelOutlook: {
    favorite?: string;
    spread?: number;
    homeWin?: number;
    awayWin?: number;
  };
};

const HEADING_PREFIX = /^#{2,3}\s+/;

export function parseMatchupReport(slug: string, markdown: string): ParsedReport {
  const { tables, ordered } = extractTables(markdown);
  const teams = parseTeams(slug, tables["PowerScore Breakdown (Model)"]);
  const modelOutlook = deriveModelOutlook(tables["Model Outlook"]);

  return {
    slug,
    raw: markdown,
    teams,
    tables,
    sections: ordered,
    modelOutlook,
  };
}

function parseTeams(slug: string, table?: ParsedTable) {
  if (table && table.headers.length >= 3) {
    return { home: table.headers[1], away: table.headers[2] };
  }
  const [home, away] = slug.split("_vs_");
  return {
    home: humanizeTeam(home ?? "HOME"),
    away: humanizeTeam(away ?? "AWAY"),
  };
}

function humanizeTeam(raw: string) {
  return raw.replace(/_/g, " ").toUpperCase();
}

function extractTables(markdown: string) {
  const lines = markdown.split(/\r?\n/);
  const tables: Record<string, ParsedTable> = {};
  const ordered: ParsedTable[] = [];
  let currentHeading = "";
  let buffer: string[] = [];

  const flushTable = () => {
    if (!currentHeading || buffer.length === 0) {
      buffer = [];
      return;
    }
    const parsed = parseTableLines(currentHeading, buffer);
    if (parsed) {
      tables[currentHeading] = parsed;
      ordered.push(parsed);
    }
    buffer = [];
  };

  for (const line of lines) {
    if (HEADING_PREFIX.test(line.trim())) {
      flushTable();
      currentHeading = line.replace(HEADING_PREFIX, "").trim();
      continue;
    }

    if (line.startsWith("|")) {
      buffer.push(line);
      continue;
    }

    if (buffer.length > 0 && line.trim() === "") {
      flushTable();
    }
  }
  flushTable();

  return { tables, ordered };
}

function parseTableLines(heading: string, lines: string[]): ParsedTable | null {
  const clean = lines.filter((line) => line.trim().length > 0);
  if (clean.length < 2) return null;
  const headerLine = clean[0];
  const headers = headerLine
    .split("|")
    .map((cell) => cell.trim())
    .filter(Boolean);
  const rows: string[][] = [];

  for (let i = 2; i < clean.length; i++) {
    const cells = clean[i]
      .split("|")
      .map((cell) => cell.trim())
      .filter(Boolean);
    if (cells.length) rows.push(cells);
  }

  return {
    heading,
    headers,
    rows,
  };
}

function deriveModelOutlook(table?: ParsedTable) {
  if (!table) return {};
  const record: Record<string, string> = {};
  for (const row of table.rows) {
    if (row.length >= 2) {
      record[row[0]] = row[1];
    }
  }

  const spreadRaw = record["Model Spread"] ?? record["Spread"];
  const favorite = spreadRaw?.includes("→")
    ? spreadRaw.split("→")[1].trim()
    : undefined;
  const numericSpread = spreadRaw ? parseFloat(spreadRaw.replace(/[^\d.-]/g, "")) : undefined;

  const homeWin = toPercent(record["Home Win %"] ?? record["Team A %"]);
  const awayWin = toPercent(record["Away Win %"] ?? record["Team B %"]);

  return {
    favorite,
    spread: Number.isFinite(numericSpread) ? numericSpread : undefined,
    homeWin,
    awayWin,
  };
}

function toPercent(value?: string) {
  if (!value) return undefined;
  const parsed = parseFloat(value.replace(/[^\d.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : undefined;
}
