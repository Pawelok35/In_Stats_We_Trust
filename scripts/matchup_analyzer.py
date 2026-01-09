from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Tuple

Tag = Literal["GOY", "GOM", "GOW", "VALUE PLAY", "NEUTRAL"]

WINDOW_COLUMNS = {
    "season": "Season-to-date",
    "last5": "Last 5",
    "last3": "Last 3",
}

TAG_COMMENTS = {
    "GOY": "🔥 Season-level conviction — pełna zgodność metryk i rynku.",
    "GOM": "📈 Strong monthly signal — wysokie zaufanie modelowe.",
    "GOW": "💪 Weekly value pick — wyraźny edge vs rynek.",
    "VALUE PLAY": "⚖️ Moderate value — umiarkowany edge.",
    "NEUTRAL": "😴 Brak value — model i rynek w równowadze.",
}

TAG_COLORS: Dict[Tag, str] = {
    "VALUE PLAY": "#1f75fe",  # niebieski
    "GOW": "#ff8c00",  # pomarańczowy
    "GOM": "#9c27b0",  # fiolet
    "GOY": "#2ecc71",  # zielony
}

DEFAULT_TAG_RULES: Dict[str, Dict[str, float]] = {
    "GOY": {"confidence": 90.0, "edge": 6.0, "powerscore_diff": 0.06},
    "GOM": {"confidence": 85.0, "edge": 4.5, "powerscore_diff": 0.05},
    "GOW": {"confidence": 78.0, "edge": 3.0, "powerscore_diff": 0.04},
    "VALUE PLAY": {"confidence": 68.0, "edge": 2.0, "powerscore_diff": 0.0},
}

TAG_RULES: Dict[str, Dict[str, float]] = DEFAULT_TAG_RULES.copy()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def parse_numeric(cell: str) -> float:
    cleaned = cell.strip()
    if cleaned.lower() in {"n/a", "na", "nan", ""}:
        raise ValueError(f"Brak wartości liczbowej w komórce: {cell!r}")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        raise ValueError(f"Nie udało się sparsować wartości z: {cell!r}")
    return float(match.group())


@dataclass
class MarkdownTable:
    headers: List[str]
    rows: List[Dict[str, str]]

    def row_by(self, key_column: str) -> Dict[str, Dict[str, str]]:
        return {row[key_column].strip(): row for row in self.rows}


class MatchupReport:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def _find_header_index(self, header: str) -> int:
        normalized = header.strip()
        for idx, line in enumerate(self.lines):
            if not line.strip().startswith("#"):
                continue
            candidate = line.lstrip("#").strip()
            if candidate == normalized:
                return idx
        raise ValueError(f"Nie znaleziono sekcji: {header}")

    def get_table(self, header: str) -> MarkdownTable:
        start_idx = self._find_header_index(header)
        line_idx = start_idx + 1
        n_lines = len(self.lines)
        while line_idx < n_lines and not self.lines[line_idx].strip().startswith("|"):
            if self.lines[line_idx].strip():
                break
            line_idx += 1
        table_lines: List[str] = []
        while line_idx < n_lines and self.lines[line_idx].strip().startswith("|"):
            table_lines.append(self.lines[line_idx])
            line_idx += 1
        if len(table_lines) < 2:
            raise ValueError(f"Nie wykryto tabeli w sekcji: {header}")
        header_line = table_lines[0]
        headers = [col.strip() for col in header_line.strip("| ").split("|")]
        data_rows: List[Dict[str, str]] = []
        for raw_line in table_lines[2:]:
            if set(raw_line.strip()) <= {"|", "-", " ", ":"}:
                continue
            values = [col.strip() for col in raw_line.strip("| ").split("|")]
            if len(values) != len(headers):
                continue
            data_rows.append(dict(zip(headers, values)))
        if not data_rows:
            raise ValueError(f"Brak wierszy danych w tabeli: {header}")
        return MarkdownTable(headers=headers, rows=data_rows)

    def parse_powerscore_values(self) -> Dict[str, float]:
        block_pattern = re.compile(
            r"\*\*Model \(4 metrics\):\*\*\s*(?:\r?\n)?\s*([A-Z]{2,3}) edge:\s*[+\-]?\d+\.\d+\s*\("
            r"([A-Z]{2,3})\s*([+\-]?\d+\.\d+)\s*vs\s*([A-Z]{2,3})\s*([+\-]?\d+\.\d+)\)",
            re.MULTILINE,
        )
        match = block_pattern.search(self.text)
        if not match:
            raise ValueError("Nie znaleziono sekcji **Model (4 metrics)** w podsumowaniu PowerScore.")
        _, team_a, value_a, team_b, value_b = match.groups()
        return {team_a: float(value_a), team_b: float(value_b)}


@dataclass
class ReportMetrics:
    epa_offense: Dict[str, float]
    epa_defense: Dict[str, float]
    success_rate_offense: Dict[str, float]
    third_down: Dict[str, float]
    red_zone: Dict[str, float]
    explosive: Dict[str, float]
    ppd_diff: Dict[str, float]
    powerscore: Dict[str, float]
    turnover_margin: Dict[str, float]
    pressure_rate_def: Dict[str, float]
    field_position_edge: Dict[str, float]
    trend_scores: Dict[str, float]
    analog_ppd: Dict[str, float]


def _get_table_flexible(report: MatchupReport, header: str) -> MarkdownTable:
    """Allow minor variations in header suffixes (e.g., up to Week 5 vs Week 9)."""
    try:
        return report.get_table(header)
    except ValueError:
        prefix = header.split("(")[0].strip()
        for line in report.lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                candidate = stripped[3:].strip()
                if candidate.startswith(prefix):
                    return report.get_table(candidate)
        raise


def load_report_metrics(report: MatchupReport, home: str, away: str, window: str) -> ReportMetrics:
    column = WINDOW_COLUMNS[window]
    ps_table = _get_table_flexible(report, "PowerScore Breakdown (Model)")
    ps_rows = ps_table.row_by("Component")
    required_components = ["EPA Offense", "EPA Defense", "Success Rate Offense"]
    for comp in required_components:
        if comp not in ps_rows:
            raise ValueError(f"Brak komponentu '{comp}' w PowerScore Breakdown.")
    epa_off = {team: parse_numeric(ps_rows["EPA Offense"][team]) for team in (home, away)}
    epa_def = {team: parse_numeric(ps_rows["EPA Defense"][team]) for team in (home, away)}

    def percent_table(header: str) -> Dict[str, float]:
        table = _get_table_flexible(report, header)
        rows = table.row_by("Team")
        return {team: parse_numeric(rows[team][column]) for team in (home, away)}

    success_form = percent_table("Success Rate Offense Form (up to Week 9)")
    third_down = percent_table("Third Down Conversion Form (up to Week 9)")
    red_zone = percent_table("Red Zone TD Rate (Off) Form (up to Week 9)")
    explosive = percent_table("Explosive Play Rate (Off) Form (up to Week 9)")
    ppd = percent_table("Points per Drive Differential Form (up to Week 9)")
    powerscore = report.parse_powerscore_values()

    table_seven = _get_table_flexible(report, "PowerScore Breakdown (7 Metrics)")
    seven_rows = table_seven.row_by("Component")
    try:
        turnover_row = seven_rows["Turnover Margin"]
        pressure_row = seven_rows["Pressure Rate (Def)"]
    except KeyError as exc:
        raise ValueError("Brakuje wiersza w tabeli PowerScore Breakdown (7 Metrics).") from exc
    turnover = {team: parse_numeric(turnover_row[team]) for team in (home, away)}
    pressure = {team: parse_numeric(pressure_row[team]) for team in (home, away)}

    field_table = _get_table_flexible(report, "Field Position Edge (own - opp)")
    field_rows = field_table.row_by("Team")
    field_position: Dict[str, float] = {}
    for team in (home, away):
        row = field_rows.get(team)
        if row:
            field_position[team] = parse_numeric(row[WINDOW_COLUMNS["season"]])
        else:
            field_position[team] = 0.0

    trend_scores: Dict[str, float] = {home: 0.0, away: 0.0}
    trend_weights = {
        "Off EPA": 0.5,
        "Off SR": 0.4,
        "Def EPA": 0.4,
        "Def SR": 0.3,
        "Tempo": 0.2,
    }
    try:
        trend_table = _get_table_flexible(report, "Trend Summary (last 3 weeks)")
        trend_rows = trend_table.rows
        for row in trend_rows:
            metric = row["Metric"]
            trend = row["Trend"].strip().lower()
            for team in (home, away):
                if metric.startswith(f"Off EPA {team}"):
                    weight = trend_weights["Off EPA"]
                elif metric.startswith(f"Off SR {team}"):
                    weight = trend_weights["Off SR"]
                elif metric.startswith(f"Def EPA {team}"):
                    weight = -trend_weights["Def EPA"]
                elif metric.startswith(f"Def SR {team}"):
                    weight = -trend_weights["Def SR"]
                elif metric.startswith(f"Tempo {team}"):
                    weight = trend_weights["Tempo"]
                else:
                    continue
                if "+ improving" in trend:
                    trend_scores[team] += weight
                elif "- declining" in trend:
                    trend_scores[team] -= weight
    except ValueError:
        trend_scores = {home: 0.0, away: 0.0}

    analog_ppd = {home: 0.0, away: 0.0}
    analog_markers = {
        home: f"**{home} analogs vs {away} profile**",
        away: f"**{away} analogs vs {home} profile**",
    }
    for team, marker in analog_markers.items():
        try:
            start_idx = report.lines.index(marker) + 3
        except ValueError:
            continue
        table_lines = []
        idx = start_idx
        while idx < len(report.lines) and report.lines[idx].startswith("|"):
            table_lines.append(report.lines[idx])
            idx += 1
        if len(table_lines) < 2:
            continue
        headers = [col.strip() for col in table_lines[0].strip("| ").split("|")]
        entries = table_lines[2:]
        values = []
        for entry in entries:
            cols = [col.strip() for col in entry.strip("| ").split("|")]
            if len(cols) != len(headers):
                continue
            row = dict(zip(headers, cols))
            sim_match = re.search(r"[-+]?\d+(?:\.\d+)?", row.get("Similarity", "0") or "0")
            if not sim_match:
                continue
            similarity = float(sim_match.group())
            ppd_match = re.search(r"[-+]?\d+(?:\.\d+)?", row.get("PPD Diff", "0") or "0")
            ppd_value = float(ppd_match.group()) if ppd_match else 0.0
            if similarity >= 0.7:
                values.append(ppd_value * similarity)
        if values:
            analog_ppd[team] = sum(values) / len(values)

    def ensure_team(mapping: Dict[str, float], allow_missing: bool = False) -> Dict[str, float]:
        missing = [team for team in (home, away) if team not in mapping]
        if missing and not allow_missing:
            raise ValueError(f"Brak danych dla: {', '.join(missing)}.")
        return {home: mapping.get(home, 0.0), away: mapping.get(away, 0.0)}

    return ReportMetrics(
        epa_offense=ensure_team(epa_off),
        epa_defense=ensure_team(epa_def),
        success_rate_offense=ensure_team(success_form),
        third_down=ensure_team(third_down),
        red_zone=ensure_team(red_zone),
        explosive=ensure_team(explosive),
        ppd_diff=ensure_team(ppd),
        powerscore=ensure_team(powerscore),
        turnover_margin=ensure_team(turnover),
        pressure_rate_def=ensure_team(pressure),
        field_position_edge=ensure_team(field_position),
        trend_scores=ensure_team(trend_scores, allow_missing=True),
        analog_ppd=ensure_team(analog_ppd, allow_missing=True),
    )


@dataclass
class MatchInput:
    spread: float
    total: float
    home_field: bool
    prime_time: bool
    adv_ppd: float
    diff_success: float
    diff_third_down: float
    diff_red_zone: float
    diff_explosive: float
    powerscore_diff: float
    diff_turnover: float
    diff_pressure: float
    diff_field_position: float
    diff_trend: float
    diff_analog: float


def build_match_input(metrics: ReportMetrics, home: str, away: str, args: argparse.Namespace) -> MatchInput:
    adv_ppd = metrics.ppd_diff[home] - metrics.ppd_diff[away]
    diff_success = metrics.success_rate_offense[home] - metrics.success_rate_offense[away]
    diff_third = metrics.third_down[home] - metrics.third_down[away]
    diff_rz = metrics.red_zone[home] - metrics.red_zone[away]
    diff_explosive = metrics.explosive[home] - metrics.explosive[away]
    powerscore_diff = metrics.powerscore[home] - metrics.powerscore[away]
    return MatchInput(
        spread=args.spread,
        total=args.total,
        home_field=not args.neutral_site,
        prime_time=args.prime_time,
        adv_ppd=adv_ppd,
        diff_success=diff_success,
        diff_third_down=diff_third,
        diff_red_zone=diff_rz,
        diff_explosive=diff_explosive,
        powerscore_diff=powerscore_diff,
        diff_turnover=metrics.turnover_margin[home] - metrics.turnover_margin[away],
        diff_pressure=metrics.pressure_rate_def[home] - metrics.pressure_rate_def[away],
        diff_field_position=metrics.field_position_edge[home] - metrics.field_position_edge[away],
        diff_trend=metrics.trend_scores[home] - metrics.trend_scores[away],
        diff_analog=metrics.analog_ppd[home] - metrics.analog_ppd[away],
    )


def compute_model_margin(inp: MatchInput) -> float:
    margin = (inp.adv_ppd / 0.10) * 1.0
    margin += (inp.diff_success / 5.0) * 2.0
    margin += (inp.diff_third_down / 10.0) * 3.0
    margin += (inp.diff_red_zone / 10.0) * 3.0
    margin += (inp.diff_explosive / 5.0) * 2.0
    margin += (inp.diff_turnover / 0.5) * 0.5
    margin += (inp.diff_pressure / 5.0) * 0.8
    margin += (inp.diff_field_position / 10.0) * 1.0
    margin += inp.diff_trend * 0.5
    margin += inp.diff_analog * 0.5
    if inp.home_field:
        margin += 1.0
    if inp.prime_time and inp.powerscore_diff > 0:
        margin += 0.5
    return margin


def classify(confidence: float, edge: float, ps_diff: float) -> Tag:
    if confidence < 68 or edge <= 0:
        return "NEUTRAL"
    for tag in ("GOY", "GOM", "GOW", "VALUE PLAY"):
        rule = TAG_RULES.get(tag) or {}
        if (
            confidence >= rule.get("confidence", 999)
            and edge >= rule.get("edge", 999)
            and ps_diff >= rule.get("powerscore_diff", 0)
        ):
            return tag  # type: ignore[return-value]
    return "NEUTRAL"


def set_tag_rules(rules: Dict[str, Dict[str, float]]) -> None:
    global TAG_RULES
    merged = DEFAULT_TAG_RULES.copy()
    for tag, rule in rules.items():
        merged[tag.upper()] = {
            "confidence": float(rule.get("confidence", merged.get(tag.upper(), {}).get("confidence", 0))),
            "edge": float(rule.get("edge", merged.get(tag.upper(), {}).get("edge", 0))),
            "powerscore_diff": float(
                rule.get("powerscore_diff", merged.get(tag.upper(), {}).get("powerscore_diff", 0))
            ),
        }
    TAG_RULES = merged


@dataclass
class ProjectionResult:
    adv_model: float
    prob_model: int
    model_score: Tuple[float, float]
    adv_market: float
    prob_market: int
    market_score: Tuple[float, float]
    edge_vs_line: float
    confidence: float
    powerscore_diff: float
    tag: Tag
    model_winner: str
    market_winner: str
    winner_margin: float
    winner_powerscore_diff: float
    winner_line: float


@dataclass
class AnalysisOutput:
    text: str
    projection: ProjectionResult


def build_projection(inp: MatchInput, home: str, away: str) -> ProjectionResult:
    adv_model = compute_model_margin(inp)
    prob_model = round(clamp(55 + adv_model * 4.2, 5, 95))
    min_total = inp.total * 0.75
    max_total = inp.total * 1.25
    model_total = clamp(inp.total + adv_model, min_total, max_total)
    home_model = (model_total + adv_model) / 2
    away_model = model_total - home_model
    adv_market = -inp.spread
    if abs(adv_market) >= 10:
        market_total = model_total
    else:
        market_total = inp.total
    home_market = (market_total + adv_market) / 2
    away_market = market_total - home_market
    prob_market_home = clamp(50 + adv_market * 3.5, 5, 95)

    model_winner = home if adv_model >= 0 else away
    market_winner = home if adv_market >= 0 else away
    winner_margin = adv_model if adv_model >= 0 else -adv_model
    prob_model_winner = prob_model if model_winner == home else 100 - prob_model
    prob_market_winner = prob_market_home if market_winner == home else 100 - prob_market_home
    market_margin_for_winner = (-inp.spread) if model_winner == home else inp.spread
    edge = winner_margin - market_margin_for_winner
    winner_ps_diff = inp.powerscore_diff if model_winner == home else -inp.powerscore_diff
    confidence = prob_model_winner
    if winner_ps_diff >= 0.05:
        confidence += 3
    elif winner_ps_diff >= 0.03:
        confidence += 1.5

    # Context tweaks (minimal, bez ingerencji w model margines):
    # 1) Road favorite duży chalk: jeśli spread >= 7 (home dog → wyjazdowy faworyt), obniż nieco confidence.
    if inp.home_field and inp.spread >= 7:
        confidence -= 2.0

    # 2) Field position edge jako proxy ST: duża przewaga/strata start_field_position_edge wzmacnia/osłabia confidence.
    if inp.diff_field_position >= 5:
        confidence += 1.0
    elif inp.diff_field_position <= -5:
        confidence -= 1.0

    # 3) Pressure diff (def pressure vs def pressure przeciwnika) – lekki boost/cięcie.
    if inp.diff_pressure >= 5:
        confidence += 1.0
    elif inp.diff_pressure <= -5:
        confidence -= 1.0

    confidence = clamp(confidence, 0, 100)
    tag = classify(confidence, edge, winner_ps_diff)
    winner_line = inp.spread if model_winner == home else -inp.spread
    return ProjectionResult(
        adv_model=adv_model,
        prob_model=round(prob_model_winner),
        model_score=(round(home_model, 1), round(away_model, 1)),
        adv_market=adv_market,
        prob_market=round(prob_market_winner),
        market_score=(round(home_market, 1), round(away_market, 1)),
        edge_vs_line=edge,
        confidence=confidence,
        powerscore_diff=inp.powerscore_diff,
        tag=tag,
        model_winner=model_winner,
        market_winner=market_winner,
        winner_margin=winner_margin,
        winner_powerscore_diff=winner_ps_diff,
        winner_line=winner_line,
    )


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def format_ppd(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.3f}"


def build_reason_sentences(metrics: ReportMetrics, home: str, away: str, adv: float) -> List[str]:
    winner = home if adv >= 0 else away
    loser = away if winner == home else home
    sentences: List[Tuple[float, str]] = []

    ppd_diff = metrics.ppd_diff[winner] - metrics.ppd_diff[loser]
    if ppd_diff > 0:
        text = (
            f"{winner} prowadzi w Points per Drive Differential ({format_ppd(metrics.ppd_diff[winner])} vs "
            f"{format_ppd(metrics.ppd_diff[loser])}), więc bazowa efektywność napędza przewagę."
        )
        sentences.append((abs(ppd_diff), text))

    sr_diff = metrics.success_rate_offense[winner] - metrics.success_rate_offense[loser]
    if sr_diff > 0:
        text = (
            f"Success Rate Offense pokazuje {winner} na poziomie {format_percent(metrics.success_rate_offense[winner])} "
            f"vs {format_percent(metrics.success_rate_offense[loser])} ({sr_diff:+.1f} pp)."
        )
        sentences.append((abs(sr_diff), text))

    td_diff = metrics.third_down[winner] - metrics.third_down[loser]
    if td_diff > 0:
        text = (
            f"Na 3rd down {winner} utrzymuje {format_percent(metrics.third_down[winner])}, podczas gdy {loser} jest na "
            f"{format_percent(metrics.third_down[loser])}, co stabilizuje serie ofensywne."
        )
        sentences.append((abs(td_diff), text))

    rz_diff = metrics.red_zone[winner] - metrics.red_zone[loser]
    if rz_diff > 0:
        text = (
            f"Red Zone TD Rate sprzyja {winner} ({format_percent(metrics.red_zone[winner])} vs "
            f"{format_percent(metrics.red_zone[loser])})."
        )
        sentences.append((abs(rz_diff), text))

    expl_diff = metrics.explosive[winner] - metrics.explosive[loser]
    if expl_diff > 0:
        text = (
            f"Explosive Play Rate pozostaje po stronie {winner} ({format_percent(metrics.explosive[winner])} vs "
            f"{format_percent(metrics.explosive[loser])}), więc big-play equity jest wyższe."
        )
        sentences.append((abs(expl_diff), text))

    ps_diff = metrics.powerscore[winner] - metrics.powerscore[loser]
    if ps_diff > 0:
        text = (
            f"PowerScore Summary potwierdza przewagę {winner}: {winner} {metrics.powerscore[winner]:+.3f} "
            f"vs {loser} {metrics.powerscore[loser]:+.3f}."
        )
        sentences.append((abs(ps_diff) * 100, text))

    turnover_diff = metrics.turnover_margin[winner] - metrics.turnover_margin[loser]
    if turnover_diff > 0:
        text = (
            f"Turnover margin faworyzuje {winner} ({metrics.turnover_margin[winner]:+.2f} vs "
            f"{metrics.turnover_margin[loser]:+.2f}), co przekłada się na dodatkowe posiadania."
        )
        sentences.append((abs(turnover_diff) * 1.5, text))

    pressure_diff = metrics.pressure_rate_def[winner] - metrics.pressure_rate_def[loser]
    if pressure_diff > 0:
        text = (
            f"Defensive pressure rate wspiera {winner} ({metrics.pressure_rate_def[winner]:+.1f}% vs "
            f"{metrics.pressure_rate_def[loser]:+.1f}%), więc pasy rywala będą częściej pod presją."
        )
        sentences.append((abs(pressure_diff), text))

    field_diff = metrics.field_position_edge[winner] - metrics.field_position_edge[loser]
    if field_diff > 0:
        text = (
            f"Field position edge wynosi {field_diff:+.1f} yds na rzecz {winner} "
            f"({metrics.field_position_edge[winner]:.1f} vs {metrics.field_position_edge[loser]:.1f}), "
            "co skraca ich boisko."
        )
        sentences.append((abs(field_diff), text))

    sentences.sort(key=lambda item: item[0], reverse=True)
    top_sentences = [text for _, text in sentences[:5]]
    if len(top_sentences) < 3:
        fallback = (
            f"{winner} utrzymuje modelowy margines {abs(adv):.1f} pkt względem {loser}, "
            "łącząc przewagę efektywności i formy."
        )
        top_sentences.append(fallback)
    return top_sentences[:5]


def build_forum_outputs(metrics: ReportMetrics, home: str, away: str, proj: ProjectionResult) -> Tuple[str, str]:
    lines_a = [
        f"PowerScore (Model) — {home} {metrics.powerscore[home]:+.3f} vs {away} {metrics.powerscore[away]:+.3f}.",
        f"Points per Drive Differential — {home} {format_ppd(metrics.ppd_diff[home])} vs {away} {format_ppd(metrics.ppd_diff[away])}.",
        f"Success Rate Offense — {home} {format_percent(metrics.success_rate_offense[home])} vs "
        f"{away} {format_percent(metrics.success_rate_offense[away])}.",
        f"Third Down Conversion — {home} {format_percent(metrics.third_down[home])} vs "
        f"{away} {format_percent(metrics.third_down[away])}.",
        f"Red Zone TD Rate — {home} {format_percent(metrics.red_zone[home])} vs "
        f"{away} {format_percent(metrics.red_zone[away])}.",
        f"Explosive Play Rate — {home} {format_percent(metrics.explosive[home])} vs "
        f"{away} {format_percent(metrics.explosive[away])}.",
        f"Model margin {proj.adv_model:.1f} pts vs market spread {home} {proj.adv_market:+.1f}.",
    ]
    forum_a = " ".join(lines_a[:7])

    winner = home if proj.adv_model >= 0 else away
    loser = away if winner == home else home
    lines_b = [
        f"Model idzie w stronę {winner} po marginesie {proj.adv_model:.1f} pkt.",
        f"{winner} notuje {format_ppd(metrics.ppd_diff[winner])} PPD vs {format_ppd(metrics.ppd_diff[loser])} u {loser}.",
        f"Różnica w Success Rate to {format_percent(metrics.success_rate_offense[winner])} vs "
        f"{format_percent(metrics.success_rate_offense[loser])}.",
        f"Na 3rd down {winner} ({format_percent(metrics.third_down[winner])}) wygląda solidniej niż {loser} "
        f"({format_percent(metrics.third_down[loser])}).",
        f"Red Zone i explosiveness ( {format_percent(metrics.red_zone[winner])} / {format_percent(metrics.explosive[winner])} ) "
        f"utrzymują przewagę jakościową.",
        f"Market trzyma {proj.adv_market:.1f} pkt, więc edge vs linia to {proj.edge_vs_line:+.1f}.",
    ]
    forum_b = " ".join(lines_b)
    return forum_a, forum_b


def render_output(home: str, away: str, metrics: ReportMetrics, proj: ProjectionResult) -> str:
    model_winner = proj.model_winner
    market_winner = proj.market_winner
    reason_sentences = build_reason_sentences(metrics, home, away, proj.adv_model)
    forum_a, forum_b = build_forum_outputs(metrics, home, away, proj)
    tag_comment = TAG_COMMENTS[proj.tag]
    tag_color = TAG_COLORS.get(proj.tag)
    colored_tag = (
        f"<span style=\"color:{tag_color}; font-weight:600;\">{proj.tag}</span>"
        if tag_color
        else proj.tag
    )
    lines = [
        "🔹 MODEL PROJECTION (Pure)",
        f"1️⃣ Estimated Score (Model) – {home} {proj.model_score[0]} – {away} {proj.model_score[1]}",
        f"2️⃣ Predicted Winner (Model) – {model_winner}",
        f"3️⃣ Predicted Margin (Model) – {model_winner} by {proj.winner_margin:.1f} pts",
        f"4️⃣ Win Probability (Model) – {proj.prob_model}% ({model_winner})",
        "5️⃣ Why This Team Wins (Model) – " + " ".join(reason_sentences),
        "",
        "🔹 MARKET PROJECTION (Balanced)",
        f"1️⃣ Estimated Score (Market) – {home} {proj.market_score[0]} – {away} {proj.market_score[1]}",
        f"2️⃣ Predicted Winner (Market) – {market_winner}",
        f"3️⃣ Predicted Margin (Market) – {market_winner} by {abs(proj.adv_market):.1f} pts",
        f"4️⃣ Win Probability (Market) – {proj.prob_market}% ({market_winner})",
        f"5️⃣ Forum Output (A) – {forum_a}",
        f"6️⃣ Forum Output (B) – {forum_b}",
        "",
        "🔹 MODEL vs MARKET",
        f"• Edge_vs_Line (winner) = {proj.edge_vs_line:+.1f} pts",
        f"• PowerScoreDiff (winner) = {proj.winner_powerscore_diff:+.3f}",
        f"• Confidence = {proj.confidence:.1f}%",
        "",
        f"🏷 Model Tag: {proj.tag} — based on {proj.confidence:.1f}% confidence, "
        f"{proj.edge_vs_line:+.1f} pts model edge vs line, and PowerScore Δ {proj.winner_powerscore_diff:+.3f}.",
        tag_comment,
        "",
        "SUMMARY:",
        "1. MODEL PROJECTION (Pure)",
        f"   • Estimated Score – {home} {proj.model_score[0]} – {away} {proj.model_score[1]}",
        f"   • Win Probability – {proj.prob_model}% ({model_winner})",
        "",
        "2. MARKET PROJECTION (Balanced)",
        f"   • Estimated Score – {home} {proj.market_score[0]} – {away} {proj.market_score[1]}",
        f"   • Win Probability – {proj.prob_market}% ({market_winner})",
        "",
        f"🏷 Model Tag: {colored_tag} — {model_winner} (HC {proj.winner_line:+.1f})",
    ]
    return "\n".join(lines)


def run(report_path: Path, home: str, away: str, args: argparse.Namespace) -> AnalysisOutput:
    report = MatchupReport(report_path)
    metrics = load_report_metrics(report, home, away, args.window)
    match_input = build_match_input(metrics, home, away, args)
    projection = build_projection(match_input, home, away)
    rendered = render_output(home, away, metrics, projection)
    return AnalysisOutput(text=rendered, projection=projection)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NFL Matchup Analyst v4.8 (Aggressive-Balanced).")
    parser.add_argument("--report", type=Path, required=True, help="Ścieżka do pliku raportu Markdown.")
    parser.add_argument("--home", required=True, help="Kod gospodarza (np. CHI).")
    parser.add_argument("--away", required=True, help="Kod gości (np. NYG).")
    parser.add_argument("--spread", type=float, required=True, help="Linia na gospodarza (np. -4.5 jeśli faworyt).")
    parser.add_argument("--total", type=float, required=True, help="Linia punktowa (Total).")
    parser.add_argument("--prime-time", action="store_true", help="Zaznacz jeśli spotkanie jest w prime time.")
    parser.add_argument("--neutral-site", action="store_true", help="Ustaw jeśli mecz na neutralnym stadionie.")
    parser.add_argument(
        "--window",
        choices=list(WINDOW_COLUMNS.keys()),
        default="season",
        help="Który horyzont formy wykorzystać do różnic (domyślnie season).",
    )
    parser.add_argument("--output", type=Path, help="Opcjonalna ścieżka zapisu wyniku (Markdown).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = args.report
    if not report_path.exists():
        raise FileNotFoundError(report_path)
    home = args.home.upper()
    away = args.away.upper()
    result = run(report_path, home, away, args)
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    sys.stdout.buffer.write(result.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
