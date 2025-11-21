export type WeatherPick = {
  id: string;
  codename:
    | "Ultimate Supercell"
    | "Supercell"
    | "Vortex"
    | "Cyclone"
    | "Gale"
    | "Breeze"
    | "Calm";
  rating: number | null;
  stake: number | null;
  matchup: string;
  direction: string;
  season: number;
  week: number;
  slug: string;
  badge: string;
};

export const weatherPicks: WeatherPick[] = [
  {
    id: "ultimate-none",
    codename: "Ultimate Supercell",
    rating: null,
    stake: null,
    matchup: "Brak sygnału",
    direction: "-",
    season: 2025,
    week: 12,
    slug: "HOU_vs_BUF",
    badge: "Awaiting perfect storm",
  },
  {
    id: "buf-tb",
    codename: "Supercell",
    rating: 6.3,
    stake: 3.5,
    matchup: "BUF vs TB",
    direction: "BUF -5.5",
    season: 2025,
    week: 12,
    slug: "BUF_vs_TB",
    badge: "Triple GOY stack",
  },
  {
    id: "ten-hou",
    codename: "Supercell",
    rating: 6.3,
    stake: 3.5,
    matchup: "TEN vs HOU",
    direction: "HOU -7.5",
    season: 2025,
    week: 12,
    slug: "TEN_vs_HOU",
    badge: "Model loves HOU",
  },
  {
    id: "lv-dal",
    codename: "Vortex",
    rating: 5.9,
    stake: 3.0,
    matchup: "LV vs DAL",
    direction: "DAL -3.5",
    season: 2025,
    week: 12,
    slug: "LV_vs_DAL",
    badge: "DAQ grade confidence",
  },
  {
    id: "pit-cin",
    codename: "Gale",
    rating: 3.8,
    stake: 2.0,
    matchup: "PIT vs CIN",
    direction: "PIT -5.5",
    season: 2025,
    week: 12,
    slug: "PIT_vs_CIN",
    badge: "SR + tempo edge",
  },
  {
    id: "cle-bal",
    codename: "Calm",
    rating: 1.7,
    stake: 1.0,
    matchup: "CLE vs BAL",
    direction: "BAL -8.5",
    season: 2025,
    week: 12,
    slug: "CLE_vs_BAL",
    badge: "Tracking only",
  },
];
