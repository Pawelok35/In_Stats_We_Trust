"use client";

import type { ParsedReport, ParsedTable } from "@/lib/markdown-parser";

export function ReportSections({ report }: { report?: ParsedReport | null }) {
  if (!report || report.sections.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4 rounded-[32px] border border-white/60 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Full report</p>
        <h3 className="text-2xl font-semibold text-slate-900 dark:text-white">
          Parsed matchup tables
        </h3>
        <p className="text-sm text-muted-foreground">
          Every markdown table is rendered below for quick inspection.
        </p>
      </div>
      <div className="grid gap-4">
        {report.sections.map((table) => (
          <article
            key={table.heading}
            className="rounded-[24px] border border-white/60 bg-white/90 p-4 text-sm shadow-inner dark:border-white/10 dark:bg-white/5"
          >
            <h4 className="text-lg font-semibold text-slate-900 dark:text-white">
              {table.heading}
            </h4>
            <div className="mt-3 overflow-auto">
              <MiniTable table={table} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function MiniTable({ table }: { table: ParsedTable }) {
  return (
    <table className="w-full min-w-[320px] border-collapse text-xs">
      <thead>
        <tr className="rounded-lg bg-gradient-to-r from-primary/10 to-blue-50 text-left text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          {table.headers.map((header) => (
            <th key={header} className="px-3 py-2 first:rounded-l-2xl last:rounded-r-2xl">
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, idx) => (
          <tr
            key={`${table.heading}-${idx}`}
            className="border-b border-white/70 text-slate-700 last:border-none dark:border-white/5 dark:text-white/80"
          >
            {row.map((cell, cellIdx) => (
              <td key={`${table.heading}-${idx}-${cellIdx}`} className="px-3 py-2">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
