"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ParsedReport, ParsedTable } from "@/lib/markdown-parser";

const SECTION_CONFIG = [
  {
    heading: "Situational edges",
    charts: [
      { key: "3rd Down Conversion", description: "Success on money downs." },
      { key: "Red Zone TD Rate", description: "Inside the 20 production." },
      { key: "Pass Protection vs Pressure", description: "Pass pro delta vs pressure." },
      { key: "Explosive Plays", description: "Explosive rate vs opponent." },
    ],
  },
  {
    heading: "Matchup edges",
    charts: [
      { key: "Rush Success Edge", description: "Rushing success margin." },
      { key: "Pass Success Edge", description: "Passing success margin." },
      { key: "Explosive Rate Edge", description: "Explosive differential." },
      { key: "Pass Protection vs Pressure", description: "Protection differential." },
    ],
  },
  {
    heading: "Game script projection",
    charts: [
      { key: "Tempo", description: "Pace per drive." },
      { key: "Pass Rate", description: "Air vs ground share." },
      { key: "Run Rate", description: "Complimentary run share." },
      { key: "Passes per Drive", description: "Play-calling splits." },
    ],
  },
  {
    heading: "Drive context",
    tables: [
      { key: "Points per Drive (offense)", description: "PPD (offense)." },
      { key: "Points per Drive Allowed", description: "PPD allowed." },
      { key: "Points per Drive Differential", description: "PPD net." },
    ],
  },
];

export function SectionsChartGrid({ report }: { report?: ParsedReport | null }) {
  if (!report) return null;

  return (
    <section className="space-y-8 rounded-[32px] border border-white/60 bg-white/80 p-6 shadow-[0_25px_70px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      {SECTION_CONFIG.map((section) => {
        const availableTables = (section.charts ?? []).filter((t) => report.tables[t.key]);
        if (availableTables.length === 0) return null;

        return (
          <div key={section.heading} className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">
                  {section.heading}
                </p>
                <h3 className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {formatHeading(section.heading)}
                </h3>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {availableTables.map((tableEntry) => (
                <ChartTile
                  key={tableEntry.key}
                  table={report.tables[tableEntry.key]!}
                  report={report}
                  description={tableEntry.description}
                />
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}

function ChartTile({
  table,
  report,
  description,
}: {
  table: ParsedTable;
  report: ParsedReport;
  description: string;
}) {
  const data = buildSeries(table, report);
  return (
    <div className="rounded-[24px] border border-white/60 bg-white/90 p-4 shadow-inner dark:border-white/10 dark:bg-white/5">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-base font-semibold text-slate-900 dark:text-white">
            {table.heading}
          </h4>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      {data.length ? (
        <div className="mt-4 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.1)" />
              <XAxis dataKey="split" tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 11 }} />
              <YAxis tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 11 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="home"
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="away"
                stroke="#f97316"
                strokeWidth={3}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="mt-6 text-xs text-muted-foreground">Not enough data to chart.</p>
      )}
    </div>
  );
}

function buildSeries(table: ParsedTable, report: ParsedReport) {
  if (table.rows.length < 2 || table.headers.length < 2) return [];
  const splits = table.headers.slice(1);
  const homeRow = findRowForTeam(table, report.teams.home);
  const awayRow = findRowForTeam(table, report.teams.away);
  if (!homeRow || !awayRow) return [];

  return splits.map((split, idx) => ({
    split,
    home: parseValue(homeRow[idx + 1]),
    away: parseValue(awayRow[idx + 1]),
  }));
}

function findRowForTeam(table: ParsedTable, team: string) {
  return table.rows.find((row) =>
    row[0]?.toUpperCase().includes(team.split(" ")[0]?.toUpperCase() ?? team.toUpperCase()),
  );
}

function parseValue(cell: string | undefined) {
  if (!cell) return 0;
  if (cell.toLowerCase().includes("n/a")) return 0;
  const numeric = parseFloat(cell.replace(/[^\d.-]/g, ""));
  if (Number.isNaN(numeric)) return 0;
  if (cell.includes("%") || cell.includes("pp")) {
    return numeric;
  }
  return numeric;
}

function formatHeading(raw: string) {
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}
