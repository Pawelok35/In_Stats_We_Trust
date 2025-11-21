"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ParsedReport, ParsedTable } from "@/lib/markdown-parser";

type Props = {
  report?: ParsedReport | null;
};

export function MatchupCharts({ report }: Props) {
  const powerScore = buildPowerScoreData(report?.tables["PowerScore Breakdown (Model)"]);
  const sevenMetrics = buildPowerScoreData(report?.tables["PowerScore Breakdown (7 Metrics)"]);
  const driveContext = buildDriveContext(report?.tables["Drive Context"]);
  const successTrend = buildSuccessTrend(report?.tables["Game Script Projection"]);

  if (!report) {
    return (
      <div className="glass-card p-6 text-center text-sm text-muted-foreground">
        Select a matchup to unlock analytics.
      </div>
    );
  }

  return (
    <div className="grid gap-6 rounded-[32px] bg-white/60 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:bg-white/5">
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="PowerScore Breakdown (Model)">
          {powerScore.length ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={powerScore} barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                <XAxis dataKey="metric" tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <YAxis tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="home" fill="url(#homeGradient)" radius={[12, 12, 12, 12]} />
                <Bar dataKey="away" fill="url(#awayGradient)" radius={[12, 12, 12, 12]} />
                <defs>
                  <linearGradient id="homeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.9} />
                    <stop offset="95%" stopColor="#36cfc9" stopOpacity={0.6} />
                  </linearGradient>
                  <linearGradient id="awayGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.85} />
                    <stop offset="95%" stopColor="#fb7185" stopOpacity={0.5} />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState />
          )}
        </ChartCard>

        <ChartCard title="PowerScore Breakdown (7 metrics)">
          {sevenMetrics.length ? (
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={sevenMetrics}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <Radar
                  name={report.teams.home}
                  dataKey="home"
                  stroke="#2563eb"
                  fill="#2563eb"
                  fillOpacity={0.35}
                />
                <Radar
                  name={report.teams.away}
                  dataKey="away"
                  stroke="#f97316"
                  fill="#f97316"
                  fillOpacity={0.25}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState />
          )}
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Drive Context · Points per Drive">
          {driveContext.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={driveContext}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                <XAxis dataKey="split" tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <YAxis tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="home"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="away"
                  stroke="#f97316"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState />
          )}
        </ChartCard>

        <ChartCard title="Success rate / EPA trend">
          {successTrend.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={successTrend}>
                <defs>
                  <linearGradient id="homeArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="awayArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#fb7185" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#fb7185" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.08)" />
                <XAxis dataKey="label" tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <YAxis tick={{ fill: "rgba(15,23,42,0.6)", fontSize: 12 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="home"
                  stroke="#22d3ee"
                  fillOpacity={1}
                  fill="url(#homeArea)"
                  strokeWidth={3}
                />
                <Area
                  type="monotone"
                  dataKey="away"
                  stroke="#fb7185"
                  fillOpacity={1}
                  fill="url(#awayArea)"
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState />
          )}
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[28px] border border-white/40 bg-white/80 p-5 shadow-inner dark:border-white/10 dark:bg-white/5">
      <p className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">{title}</p>
      <div className="mt-4 h-full">{children}</div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-56 items-center justify-center rounded-3xl border border-dashed border-muted-foreground/40 text-sm text-muted-foreground">
      Data not available in the current report.
    </div>
  );
}

function buildPowerScoreData(table?: ParsedTable) {
  if (!table) return [];
  const [, home, away] = table.headers;
  return table.rows.map((row) => ({
    metric: row[0],
    home: parseFloat(row[1]) || 0,
    away: parseFloat(row[2]) || 0,
    homeLabel: home,
    awayLabel: away,
  }));
}

function buildDriveContext(table?: ParsedTable) {
  if (!table) return [];
  return table.rows.map((row) => ({
    split: row[0],
    home: parseFloat(row[1]) || 0,
    away: parseFloat(row[2]) || 0,
  }));
}

function buildSuccessTrend(table?: ParsedTable) {
  if (!table) return [];
  return table.rows.map((row) => ({
    label: row[0],
    home: parseFloat(row[1]) || 0,
    away: parseFloat(row[2]) || 0,
  }));
}
