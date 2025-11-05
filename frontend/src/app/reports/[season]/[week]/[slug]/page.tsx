import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { fetchCore12Preview } from "@/lib/api";
import {
  listAvailableWeeks,
  loadMatchupMarkdown,
  loadMatchupManifest,
} from "@/lib/reports";

type ReportPageParams = {
  season: string;
  week: string;
  slug: string;
};

type ReportPageProps = {
  params: Promise<ReportPageParams>;
};

export default async function ReportPage({ params }: ReportPageProps) {
  const { season: seasonParam, week: weekParam, slug } = await params;
  const season = Number(seasonParam);
  const week = Number(weekParam);

  if (!Number.isFinite(season) || !Number.isFinite(week) || !slug) {
    notFound();
  }

  const weeks = listAvailableWeeks();
  const hasWeek = weeks.some(
    (entry) => entry.season === season && entry.week === week,
  );
  if (!hasWeek) {
    notFound();
  }

  let markdown: string;
  try {
    markdown = loadMatchupMarkdown(season, week, slug);
  } catch (error) {
    console.error(error);
    notFound();
  }

  const title = slug.replace(/_/g, " ").replace(/\bvs\b/i, "vs");
  const [homeTeam, awayTeam] = slug
    .split("_vs_")
    .map((code) => code?.toUpperCase());

  let core12Rows: Awaited<ReturnType<typeof fetchCore12Preview>> | null = null;
  let core12Error: string | null = null;
  try {
    const preview = await fetchCore12Preview({ season, week, n: 32 });
    core12Rows = preview.filter((row) => {
      const team = String(row.TEAM ?? "").toUpperCase();
      return team === homeTeam || team === awayTeam;
    });
  } catch (error) {
    core12Error =
      error instanceof Error ? error.message : "Nie udało się pobrać danych Core12.";
  }

  const manifest = loadMatchupManifest(season, week, slug);

  return (
    <main className="min-h-screen bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="space-y-3">
          <Link
            href={`/weeks/${season}/${week}`}
            className="text-sm font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Powrót do listy meczów
          </Link>
          <div className="flex flex-col gap-2">
            <Badge variant="outline" className="w-fit text-sm">
              Sezon {season} · Week {week}
            </Badge>
            <h1 className="text-3xl font-semibold sm:text-4xl">{title}</h1>
            <p className="text-muted-foreground">
              Renderowany raport Markdown wygenerowany przez pipeline „In Stats
              We Trust”.
            </p>
          </div>
        </div>

        <Separator />

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Core12 preview</h2>
          {core12Error ? (
            <Alert variant="destructive">
              <AlertTitle>Nie udało się pobrać danych</AlertTitle>
              <AlertDescription>{core12Error}</AlertDescription>
            </Alert>
          ) : core12Rows === null ? (
            <Skeleton className="h-32 w-full" />
          ) : core12Rows.length === 0 ? (
            <Alert>
              <AlertTitle>Brak danych Core12</AlertTitle>
              <AlertDescription>
              Nie znaleziono wierszy Core12 dla drużyn {homeTeam} i {awayTeam} w tygodniu {week}.
              </AlertDescription>
            </Alert>
          ) : (
            <Table>
              <TableCaption>
                Dane z FastAPI: <code>/metrics/core12/preview</code> (season {season}, week {week})
              </TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>TEAM</TableHead>
                  <TableHead>core_epa_offense</TableHead>
                  <TableHead>core_epa_defense</TableHead>
                  <TableHead>success_rate_offense</TableHead>
                  <TableHead>pressure_rate_defense</TableHead>
                  <TableHead>tempo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {core12Rows.map((row) => (
                  <TableRow key={String(row.TEAM)}>
                    <TableCell className="font-semibold">{row.TEAM}</TableCell>
                    <TableCell>{formatNumber(row.core_epa_offense)}</TableCell>
                    <TableCell>{formatNumber(row.core_epa_defense)}</TableCell>
                    <TableCell>{formatPercent(row.success_rate_offense)}</TableCell>
                    <TableCell>{formatPercent(row.pressure_rate_defense)}</TableCell>
                    <TableCell>{formatNumber(row.tempo)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </section>

        {manifest && (
          <>
            <Separator />
            <section className="space-y-4">
              <h2 className="text-2xl font-semibold">Manifest i assets</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Plik raportu</CardTitle>
                    <CardDescription>
                      Metadane z <code>manifest.json</code>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    {manifest.markdown ? (
                      <>
                        <div>
                          <span className="font-medium">Ścieżka:</span>{" "}
                          <code className="break-all">{manifest.markdown.path}</code>
                        </div>
                        <div>
                          <span className="font-medium">SHA-256:</span>{" "}
                          <code className="break-all">{manifest.markdown.sha256}</code>
                        </div>
                        <div>
                          <span className="font-medium">Rozmiar:</span>{" "}
                          {formatBytes(manifest.markdown.size)}
                        </div>
                      </>
                    ) : (
                      <p>Brak pozycji w manifeście dla pliku Markdown.</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Assets</CardTitle>
                    <CardDescription>
                      Pliki z katalogu <code>assets/{slug}</code>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    {manifest.assets.length === 0 ? (
                      <p>Brak dodatkowych assets dla tego meczu.</p>
                    ) : (
                      manifest.assets.map((asset) => {
                        const filename = pathBasename(asset.path);
                        return (
                          <div
                            key={asset.path}
                            className="space-y-1 rounded-lg border p-3"
                          >
                            <div className="flex flex-col gap-1">
                              <span className="font-medium">{filename}</span>
                              <span className="text-muted-foreground">
                                Rozmiar: {formatBytes(asset.size)}
                              </span>
                            </div>
                            {isPreviewableImage(filename) ? (
                              <div className="overflow-hidden rounded-md border bg-muted/40">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={`/api/assets/${season}/${week}/${slug}/${filename}`}
                                  alt={filename}
                                  className="h-auto w-full max-h-80 object-contain bg-white"
                                />
                              </div>
                            ) : (
                              <Link
                                href={`/api/assets/${season}/${week}/${slug}/${filename}`}
                                className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                              >
                                Pobierz
                              </Link>
                            )}
                          </div>
                        );
                      })
                    )}
                  </CardContent>
                </Card>
              </div>
            </section>
          </>
        )}

        <Separator />

        <article className="markdown-body rounded-xl border bg-card p-6 shadow-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
        </article>
      </div>
    </main>
  );
}

function formatNumber(value: unknown, digits = 3): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }
  return value.toFixed(digits);
}

function formatPercent(value: unknown, digits = 1): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes)) {
    return "—";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function pathBasename(filePath: string): string {
  return filePath.split(/[/\\]/).pop() ?? filePath;
}

function isPreviewableImage(filename: string): boolean {
  return /\.(png|jpg|jpeg|webp|gif)$/i.test(filename);
}
