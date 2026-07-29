export type PickDecision = "bet" | "lean" | "avoid" | "no bet";

export type OperationalPick = {
  id: string;
  season: number;
  week: number;
  variant: string;
  variantStatus: string;
  home: string;
  away: string;
  matchup: string;
  tag: string;
  modelWinner: string;
  marketWinner?: string;
  confidence: number | null;
  edgeVsLine: number | null;
  handicap: number | null;
  spread: number | null;
  total: number | null;
  window?: string;
  report?: string;
  slug: string;
  decision: PickDecision;
  modelVersion?: string;
  dataCutoff?: string;
  commitSha?: string;
  configSha256?: string;
  generatedAt?: string;
};
