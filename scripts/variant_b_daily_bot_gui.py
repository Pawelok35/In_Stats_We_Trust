from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from datetime import datetime, timezone
from pathlib import Path
from tkinter import messagebox, ttk

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_scenario.batch import (
    BatchGameInput,
    BatchValidationError,
    block_options,
    build_entries,
    completeness,
    games_for_block,
    generate_batch_post,
    validate_entry,
)
from live_scenario.forum_formatter import build_forum_post
from live_scenario.week_games import (
    ScheduleLoadError,
    WeekGame,
    invert_score_pair,
    label_for_active_pick,
    load_week_games,
)

BOT_SCRIPT = REPO_ROOT / "scripts" / "variant_b_daily_bot.py"
BOT_CONFIG = REPO_ROOT / "config" / "variant_b_daily_bot.yaml"
LIVE_SCENARIO_SCRIPT = REPO_ROOT / "scripts" / "live_quarter_scenario_matrix.py"
LIVE_SCENARIO_V2_SCRIPT = REPO_ROOT / "scripts" / "live_scenario_v2.py"
LIVE_SCENARIO_MANIFEST = REPO_ROOT / "data" / "live_scenario" / "manifest.json"
LIVE_SCENARIO_PROCESSED = (
    REPO_ROOT / "data" / "live_scenario" / "processed" / "team_game_scenario_rows.parquet"
)
LIVE_WEEK_GAMES_DIAGNOSTIC_LOG = REPO_ROOT / "research" / "live_scenario_week_games_diagnostics.log"
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON_EXE = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
PREGAME_DATA_ROOT = REPO_ROOT / "data" / "pregame"

DAY_OPTIONS = [
    ("auto", "Auto - dzisiejszy dzien"),
    ("monday", "Poniedzialek - final MNF"),
    ("tuesday", "Wtorek - close week + skan"),
    ("wednesday", "Sroda - TNF delta"),
    ("thursday", "Czwartek - final TNF + Sunday/MNF"),
    ("friday", "Piatek - refresh Sunday/MNF"),
    ("saturday", "Sobota - pre-final Sunday/MNF"),
    ("sunday", "Niedziela - final Sunday + MNF"),
]

WEEK_TEST_DAYS = ["tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "monday"]
ACTION_TAGS = {"VALUE PLAY", "GOW", "GOM", "GOY"}
WATCHLIST_MIN_ABS_EDGE = 2.0
LIVE_PATH_OPTIONS = [
    "START",
    "WIN",
    "LOSS",
    "TIE",
    "WIN-WIN",
    "WIN-LOSS",
    "WIN-TIE",
    "LOSS-WIN",
    "LOSS-LOSS",
    "LOSS-TIE",
    "TIE-WIN",
    "TIE-LOSS",
    "TIE-TIE",
    "WIN-WIN-WIN",
    "WIN-WIN-LOSS",
    "WIN-LOSS-WIN",
    "WIN-LOSS-LOSS",
    "LOSS-WIN-WIN",
    "LOSS-WIN-LOSS",
    "LOSS-LOSS-WIN",
    "LOSS-LOSS-LOSS",
]
DAY_LABELS_PL = {
    "monday": "poniedzialek",
    "tuesday": "wtorek",
    "wednesday": "sroda",
    "thursday": "czwartek",
    "friday": "piatek",
    "saturday": "sobota",
    "sunday": "niedziela",
}


def build_game_id(record: dict) -> str:
    season = int(record.get("season") or 0)
    week = int(record.get("week") or 0)
    away = str(record.get("away") or "AWAY").upper()
    home = str(record.get("home") or "HOME").upper()
    return f"{season}_w{week:02d}_{away}_at_{home}"


def is_watchlist_record(record: dict, *, min_abs_edge: float = WATCHLIST_MIN_ABS_EDGE) -> bool:
    """Return whether a neutral model result belongs on the operator watchlist."""
    if str(record.get("tag") or "").strip().upper() != "NEUTRAL":
        return False
    try:
        edge = abs(float(record.get("edge_vs_line")))
    except (TypeError, ValueError):
        return False
    return edge >= min_abs_edge


def week_generated_artifact_paths(
    repo_root: Path,
    season: int,
    week: int,
    variant: str,
) -> list[Path]:
    """Return resettable outputs, excluding all manually supplied evidence."""
    return [
        repo_root / "research" / "daily_bot" / str(season) / f"week_{week:02d}",
        repo_root / "research" / "variant_b_week_flow" / str(season) / f"week_{week:02d}",
        repo_root / "data" / "learning_ledger" / str(season) / f"week_{week:02d}",
        repo_root / "data" / "proof_ready_checks" / str(season) / f"week_{week:02d}_lines_check.md",
        repo_root / "data" / f"picks_{variant}" / str(season) / f"week_{week:02d}.jsonl",
        repo_root / "config" / "lines" / str(season) / f"week{week}_lines.yaml",
    ]


class DailyBotGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Variant B Daily Bot")
        self.geometry("1280x980")
        self.minsize(860, 740)
        self.last_report: Path | None = None
        self.bot_config = self._load_bot_config()
        self.selected_pick_record: dict | None = None
        self.live_buttons: list[ttk.Button] = []
        self.live_settings_visible = True
        self.live_mode_var = tk.StringVar(value="BASIC_AFTER_Q2")
        self.live_basic_payload: dict | None = None
        self.live_week_games: dict[str, WeekGame] = {}
        self.live_active_game: WeekGame | None = None
        self.live_current_perspective: str | None = None
        self.live_week_games_metadata: dict | None = None
        self.live_batch_all_games: list[WeekGame] = []
        self.live_batch_entries: dict[str, BatchGameInput] = {}
        self.live_batch_row_widgets: dict[str, dict[str, tk.Widget]] = {}
        self.live_batch_metadata: dict | None = None
        self.live_batch_output_dirty = True
        self.run_started_at: datetime | None = None
        self.run_label = "IDLE"
        self._build_ui()

    def _load_bot_config(self) -> dict:
        try:
            with BOT_CONFIG.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:
            messagebox.showerror("Config error", f"Nie moge wczytac configu:\n{exc}")
            return {}
        return data if isinstance(data, dict) else {}

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.configure("TButton", padding=(8, 4))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Active.TLabel", font=("Segoe UI", 10, "bold"))

        shell = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, sashrelief=tk.RAISED)
        shell.pack(fill=tk.BOTH, expand=True)

        left_shell = ttk.Frame(shell, width=880)
        right_shell = ttk.Frame(shell, padding=10, width=400)
        left_shell.pack_propagate(False)
        right_shell.pack_propagate(False)
        shell.add(left_shell, minsize=700, stretch="always")
        shell.add(right_shell, minsize=360, stretch="never")

        def _set_initial_sash() -> None:
            width = max(self.winfo_width(), self.winfo_reqwidth(), 1280)
            shell.sash_place(0, max(700, min(width - 380, int(width * 0.72))), 1)

        self.after_idle(_set_initial_sash)
        self.after(250, _set_initial_sash)

        canvas = tk.Canvas(left_shell, highlightthickness=0)
        self.page_canvas = canvas
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        page_scroll = ttk.Scrollbar(left_shell, orient=tk.VERTICAL, command=canvas.yview)
        page_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=page_scroll.set)

        root = ttk.Frame(canvas, padding=14)
        root_window = canvas.create_window((0, 0), window=root, anchor=tk.NW)

        live_canvas = tk.Canvas(right_shell, highlightthickness=0)
        live_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        live_scroll = ttk.Scrollbar(right_shell, orient=tk.VERTICAL, command=live_canvas.yview)
        live_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        live_canvas.configure(yscrollcommand=live_scroll.set)
        self.live_canvas = live_canvas
        live_root = ttk.Frame(live_canvas, padding=(0, 0, 8, 0))
        live_root_window = live_canvas.create_window((0, 0), window=live_root, anchor=tk.NW)
        self.live_root = live_root

        def _sync_scroll_region(_event: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_canvas_width(event: tk.Event) -> None:
            canvas.itemconfigure(root_window, width=event.width)

        def _sync_live_scroll_region(_event: tk.Event) -> None:
            live_canvas.configure(scrollregion=live_canvas.bbox("all"))

        def _sync_live_canvas_width(event: tk.Event) -> None:
            live_canvas.itemconfigure(live_root_window, width=event.width)

        def _mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _live_mousewheel(event: tk.Event) -> None:
            live_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        root.bind("<Configure>", _sync_scroll_region)
        canvas.bind("<Configure>", _sync_canvas_width)
        canvas.bind("<MouseWheel>", _mousewheel)
        root.bind("<MouseWheel>", _mousewheel)
        live_root.bind("<Configure>", _sync_live_scroll_region)
        live_canvas.bind("<Configure>", _sync_live_canvas_width)
        live_canvas.bind("<MouseWheel>", _live_mousewheel)
        live_root.bind("<MouseWheel>", _live_mousewheel)

        header = ttk.Label(root, text="Variant B Daily Bot", font=("Segoe UI", 16, "bold"))
        header.pack(anchor=tk.W)

        desc = ttk.Label(
            root,
            text="Centrum pracy dziennej: najpierw plan dnia, potem linie, picki, GPT/quote i finalny raport.",
        )
        desc.pack(anchor=tk.W, pady=(4, 14))

        form = ttk.Frame(root)
        form.pack(fill=tk.X)

        ttk.Label(form, text="Season").grid(row=0, column=0, sticky=tk.W)
        self.season_var = tk.StringVar(value="2026")
        ttk.Entry(form, textvariable=self.season_var, width=10).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 12)
        )

        ttk.Label(form, text="Week").grid(row=0, column=1, sticky=tk.W)
        self.week_var = tk.StringVar(value="1")
        ttk.Entry(form, textvariable=self.week_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=(0, 12)
        )

        ttk.Label(form, text="Day").grid(row=0, column=2, sticky=tk.W)
        self.day_var = tk.StringVar(value=DAY_OPTIONS[0][0])
        day_box = ttk.Combobox(
            form,
            textvariable=self.day_var,
            values=[item[0] for item in DAY_OPTIONS],
            state="readonly",
            width=18,
        )
        day_box.grid(row=1, column=2, sticky=tk.W, padx=(0, 12))

        self.day_help_var = tk.StringVar(value=self._day_label(self.day_var.get()))
        day_help = ttk.Label(form, textvariable=self.day_help_var)
        day_help.grid(row=1, column=3, sticky=tk.W)
        day_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_day_plan())

        self.now_var = tk.StringVar(value="")
        ttk.Label(form, textvariable=self.now_var).grid(row=1, column=4, sticky=tk.W, padx=(18, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(14, 10))

        self.dry_button = ttk.Button(buttons, text="1. Sprawdz plan", command=lambda: self._run_bot(False))
        self.dry_button.grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        self.execute_button = ttk.Button(buttons, text="2. Wykonaj dzien", command=lambda: self._confirm_execute())
        self.execute_button.grid(row=0, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        self.week_dry_button = ttk.Button(
            buttons,
            text="Test tygodnia Tue-Mon",
            command=self._run_week_dry_run,
        )
        self.week_dry_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        self.reset_button = ttk.Button(
            buttons,
            text="Reset testu tygodnia",
            command=self._reset_week_test_data,
        )
        self.reset_button.grid(row=0, column=3, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        ttk.Button(buttons, text="Otworz raport dnia", command=self._open_last_report).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Button(buttons, text="Otworz folder raportow", command=self._open_report_folder).grid(
            row=1, column=1, sticky=tk.W, padx=(0, 8)
        )
        self.status_var = tk.StringVar(value="STATUS: READY")
        self.status_label = ttk.Label(
            root,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 6))

        active_frame = ttk.LabelFrame(root, text="Aktywny mecz")
        self.active_frame = active_frame
        active_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        self.active_match_var = tk.StringVar(
            value="Brak aktywnego picka. Kliknij 'Zaladuj picki' i wybierz mecz z listy."
        )
        ttk.Label(active_frame, textvariable=self.active_match_var, style="Active.TLabel").pack(
            anchor=tk.W,
            padx=6,
            pady=6,
        )

        ledger_frame = ttk.LabelFrame(root, text="Centralny ledger pregame")
        ledger_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        ledger_actions = ttk.Frame(ledger_frame)
        ledger_actions.pack(fill=tk.X, padx=6, pady=(6, 3))
        ttk.Button(
            ledger_actions,
            text="Odswiez status ledgeru",
            command=self._refresh_central_ledger,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            ledger_actions,
            text="Otworz raport ledgeru",
            command=self._open_central_ledger_report,
        ).pack(side=tk.LEFT)
        self.ledger_status_text = tk.Text(ledger_frame, height=5, wrap=tk.WORD)
        self.ledger_status_text.pack(fill=tk.X, padx=6, pady=(3, 6))
        self.ledger_status_text.insert(
            tk.END,
            "Centralny ledger nie zostal jeszcze odczytany.\n"
            "Uzyj odswiezenia po zapisaniu danych tygodnia.",
        )
        self.ledger_status_text.configure(state=tk.DISABLED)

        workflow_frame = ttk.LabelFrame(root, text="Szybka kolejnosc pracy")
        workflow_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        ttk.Label(
            workflow_frame,
            text=(
                "1) Plan dnia -> 2) Linie/book snapshot -> 3) Picki -> "
                "4) GPT research -> 5) Quote -> 6) Execute i raport"
            ),
        ).pack(anchor=tk.W, padx=6, pady=6)

        plan_frame = ttk.LabelFrame(root, text="1. Plan dnia")
        plan_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.plan_text = tk.Text(plan_frame, wrap=tk.WORD, height=7)
        self.plan_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        plan_scroll = ttk.Scrollbar(plan_frame, command=self.plan_text.yview)
        plan_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.plan_text.configure(yscrollcommand=plan_scroll.set)

        picks_frame = ttk.LabelFrame(root, text="3. Picki modelu i watchlista")
        picks_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        picks_top = ttk.Frame(picks_frame)
        picks_top.pack(fill=tk.X, padx=6, pady=6)

        ttk.Button(picks_top, text="Zaladuj picki", command=self._load_model_picks).pack(
            side=tk.LEFT
        )
        ttk.Label(picks_top, text="Pick").pack(side=tk.LEFT, padx=(12, 4))
        self.pick_var = tk.StringVar(value="")
        self.pick_box = ttk.Combobox(
            picks_top,
            textvariable=self.pick_var,
            values=[],
            state="readonly",
            width=72,
        )
        self.pick_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.pick_box.bind("<<ComboboxSelected>>", lambda _event: self._select_model_pick())

        self.pick_summary_var = tk.StringVar(value="No model picks loaded.")
        ttk.Label(picks_frame, textvariable=self.pick_summary_var).pack(
            anchor=tk.W, padx=6, pady=(0, 6)
        )
        self.model_pick_records: dict[str, dict] = {}
        watch_top = ttk.Frame(picks_frame)
        watch_top.pack(fill=tk.X, padx=6, pady=(0, 6))

        ttk.Label(watch_top, text="Watchlist").pack(side=tk.LEFT)
        self.watch_var = tk.StringVar(value="")
        self.watch_box = ttk.Combobox(
            watch_top,
            textvariable=self.watch_var,
            values=[],
            state="readonly",
            width=96,
        )
        self.watch_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.watch_box.bind("<<ComboboxSelected>>", lambda _event: self._select_watchlist_pick())
        self.watch_summary_var = tk.StringVar(value="No watchlist loaded.")
        ttk.Label(picks_frame, textvariable=self.watch_summary_var).pack(
            anchor=tk.W, padx=6, pady=(0, 6)
        )
        self.watch_records: dict[str, dict] = {}

        paste_frame = ttk.LabelFrame(root, text="2/4. Wklejka: book snapshot albo GPT research")
        paste_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        paste_frame.pack_configure(before=picks_frame)

        paste_top = ttk.Frame(paste_frame)
        paste_top.pack(fill=tk.X, padx=6, pady=(6, 4))

        ttk.Label(paste_top, text="Game ID").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
        self.game_id_var = tk.StringVar(value="2026_w01_SF_at_LA")
        ttk.Entry(paste_top, textvariable=self.game_id_var, width=28).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 12)
        )

        ttk.Label(paste_top, text="Type").grid(row=0, column=2, sticky=tk.W, padx=(0, 4))
        self.gpt_snapshot_type_var = tk.StringVar(value="delta_refresh")
        self.snapshot_type_box = ttk.Combobox(
            paste_top,
            textvariable=self.gpt_snapshot_type_var,
            values=["full_19_points", "delta_refresh"],
            state="readonly",
            width=18,
        )
        self.snapshot_type_box.grid(row=0, column=3, sticky=tk.W, padx=(0, 12))
        self.snapshot_type_box.bind("<<ComboboxSelected>>", lambda _event: self._generate_gpt_prompt())

        ttk.Label(paste_top, text="Source").grid(row=0, column=4, sticky=tk.W, padx=(0, 4))
        self.gpt_source_var = tk.StringVar(value="GPT")
        ttk.Entry(paste_top, textvariable=self.gpt_source_var, width=18).grid(
            row=0, column=5, sticky=tk.W
        )

        paste_buttons = ttk.Frame(paste_frame)
        paste_buttons.pack(fill=tk.X, padx=6, pady=(0, 6))

        ttk.Label(paste_buttons, text="GPT research").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 6))
        ttk.Button(paste_buttons, text="Kopiuj prompt GPT", command=self._copy_gpt_prompt).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 6)
        )
        ttk.Button(paste_buttons, text="Odswiez prompt", command=self._generate_gpt_prompt).grid(
            row=0, column=2, sticky=tk.W, padx=(0, 8), pady=(0, 6)
        )
        ttk.Button(paste_buttons, text="Zapisz wynik GPT", command=self._save_gpt_snapshot).grid(
            row=0, column=3, sticky=tk.W, padx=(0, 8), pady=(0, 6)
        )
        ttk.Button(paste_buttons, text="Folder GPT", command=self._open_gpt_folder).grid(
            row=0, column=4, sticky=tk.W, padx=(0, 8), pady=(0, 6)
        )
        ttk.Label(paste_buttons, text="Book snapshot").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 6))
        ttk.Button(
            paste_buttons,
            text="Kopiuj prompt do screena",
            command=self._copy_book_snapshot_prompt,
        ).grid(row=1, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 6))
        ttk.Button(
            paste_buttons,
            text="Zapisz snapshot z wklejki",
            command=self._save_book_snapshot_from_paste,
        ).grid(row=1, column=2, sticky=tk.W, padx=(0, 8), pady=(0, 6))
        ttk.Button(
            paste_buttons,
            text="Konwertuj na linie",
            command=self._convert_book_snapshot_to_lines,
        ).grid(row=1, column=3, sticky=tk.W, padx=(0, 8), pady=(0, 6))
        ttk.Label(paste_buttons, text="Pomoc").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 6))
        ttk.Button(
            paste_buttons,
            text="Kopiuj instrukcje dla Codex",
            command=self._copy_codex_save_instruction,
        ).grid(row=2, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 6))

        self.gpt_paste_text = tk.Text(paste_frame, wrap=tk.WORD, height=6)
        self.gpt_paste_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        quote_frame = ttk.LabelFrame(root, text="5. Quote dla wybranego picka")
        quote_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        quote_top = ttk.Frame(quote_frame)
        quote_top.pack(fill=tk.X, padx=6, pady=6)
        self.quote_book_var = tk.StringVar(value="")
        self.quote_spread_var = tk.StringVar(value="")
        self.quote_price_var = tk.StringVar(value="")
        self.quote_timestamp_var = tk.StringVar(value="")
        self.quote_status_var = tk.StringVar(value="DISPLAYED_UNVERIFIED")
        for label, variable, width in (
            ("Book", self.quote_book_var, 16),
            ("Spread", self.quote_spread_var, 8),
            ("Price", self.quote_price_var, 8),
            ("UTC timestamp", self.quote_timestamp_var, 25),
        ):
            ttk.Label(quote_top, text=label).pack(side=tk.LEFT, padx=(0, 4))
            ttk.Entry(quote_top, textvariable=variable, width=width).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(quote_top, text="Status").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            quote_top,
            textvariable=self.quote_status_var,
            values=["DISPLAYED_UNVERIFIED", "CONFIRMED_AT_BOOK", "BETSLIP_CONFIRMED_AT_TARGET_STAKE"],
            state="readonly",
            width=29,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(quote_top, text="Use current UTC", command=self._set_quote_timestamp_now).pack(side=tk.LEFT)
        ttk.Button(quote_top, text="Save quote", command=self._save_market_quote).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(
            quote_frame,
            text="Zapisuje quote dla wybranego picka. Status CONFIRMED oznacza, że sprawdziłeś go bezpośrednio u booka.",
        ).pack(anchor=tk.W, padx=6, pady=(0, 6))

        prompt_frame = ttk.LabelFrame(root, text="Prompt GPT dla wybranego dnia / meczu")
        prompt_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.gpt_prompt_text = tk.Text(prompt_frame, wrap=tk.WORD, height=6)
        self.gpt_prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        prompt_scroll = ttk.Scrollbar(prompt_frame, command=self.gpt_prompt_text.yview)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.gpt_prompt_text.configure(yscrollcommand=prompt_scroll.set)

        self._build_live_scenario_panel()

        output_frame = ttk.LabelFrame(root, text="6. Output / log wykonania")
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output = tk.Text(output_frame, wrap=tk.WORD, height=12)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(output_frame, command=self.output.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scroll.set)

        self._write_line("Gotowe. Najpierw uzyj Dry run.")
        self._refresh_day_plan()
        self._generate_gpt_prompt()
        self._update_clock()

    def _build_live_scenario_panel(self) -> None:
        container = self.live_root

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="LIVE SCENARIO", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        self.live_status_var = tk.StringVar(value="READY")
        ttk.Label(header, textvariable=self.live_status_var, style="Active.TLabel").pack(anchor=tk.W)
        self.live_dataset_status_var = tk.StringVar(value=self._live_dataset_status_text())
        ttk.Label(header, textvariable=self.live_dataset_status_var, justify=tk.LEFT).pack(anchor=tk.W)

        active_frame = ttk.LabelFrame(container, text="Active Scenario")
        active_frame.pack(fill=tk.X, pady=(0, 8))
        self.live_active_var = tk.StringVar(value="No active scenario.")
        ttk.Label(
            active_frame,
            textvariable=self.live_active_var,
            justify=tk.LEFT,
            wraplength=340,
        ).pack(fill=tk.X, padx=6, pady=6)

        settings_header = ttk.Frame(container)
        settings_header.pack(fill=tk.X, pady=(0, 4))
        self.live_settings_button = ttk.Button(
            settings_header,
            text="Ukryj Scenario Settings",
            command=self._toggle_live_settings,
        )
        self.live_settings_button.pack(anchor=tk.W)

        self.live_settings_notebook = ttk.Notebook(container)
        # Keep a full halftime block visible; the outer right-panel scrollbar
        # remains available for the rest of Live Scenario.
        self.live_settings_notebook.configure(height=760)
        self.live_settings_notebook.pack(fill=tk.X, pady=(0, 8))
        self.live_basic_tab = ttk.Frame(self.live_settings_notebook)
        self.live_manual_tab = ttk.Frame(self.live_settings_notebook)
        self.live_batch_tab = ttk.Frame(self.live_settings_notebook)
        self.live_settings_notebook.add(self.live_basic_tab, text="BASIC AFTER Q2")
        self.live_settings_notebook.add(self.live_manual_tab, text="MANUAL LOOKUP")
        self.live_settings_notebook.add(self.live_batch_tab, text="BATCH AFTER Q2")
        self.live_settings_notebook.bind(
            "<<NotebookTabChanged>>",
            lambda _event: self._on_live_mode_changed(),
        )

        self.live_basic_frame = ttk.LabelFrame(
            self.live_basic_tab,
            text="Basic After Q2 Inputs",
        )
        self.live_basic_frame.pack(fill=tk.X, pady=(0, 8))
        self.live_basic_frame.columnconfigure(1, weight=1)

        self.live_settings_frame = ttk.LabelFrame(
            self.live_manual_tab,
            text="Manual Lookup Settings",
        )
        self.live_settings_frame.pack(fill=tk.X, pady=(0, 8))
        self.live_settings_frame.columnconfigure(1, weight=1)

        self.live_start_season_var = tk.StringVar(value="2015")
        self.live_end_season_var = tk.StringVar(value="2025")
        self.live_game_season_var = tk.StringVar(value="2026")
        self.live_game_week_var = tk.StringVar(value="1")
        self.live_game_var = tk.StringVar(value="")
        self.live_perspective_var = tk.StringVar(value="")
        self.live_game_status_var = tk.StringVar(value="Week games not loaded.")
        self.live_lookup_path_var = tk.StringVar(value="WIN-WIN")
        self.live_event_var = tk.StringVar(value="TEAM_A_WIN_FINAL")
        self.live_settlement_var = tk.StringVar(value="TIE_IS_LOSS")
        self.live_decimal_var = tk.StringVar(value="")
        self.live_ml_var = tk.StringVar(value="")
        self.live_q1_var = tk.StringVar(value="")
        self.live_q2_var = tk.StringVar(value="")
        self.live_q3_var = tk.StringVar(value="")
        self.live_sample_mode_var = tk.StringVar(value="TEAM_A_HISTORY")
        self.live_team_var = tk.StringVar(value="")
        self.live_opponent_var = tk.StringVar(value="")
        self.live_role_var = tk.StringVar(value="")
        self.live_side_var = tk.StringVar(value="")
        self.live_spread_bucket_var = tk.StringVar(value="")
        self.live_phase_var = tk.StringVar(value="")

        def add_basic_row(row: int, label: str, widget: tk.Widget) -> None:
            ttk.Label(self.live_basic_frame, text=label).grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=(6, 8),
                pady=3,
            )
            widget.grid(row=row, column=1, sticky=tk.EW, padx=(0, 6), pady=3)

        def add_row(row: int, label: str, widget: tk.Widget) -> None:
            ttk.Label(self.live_settings_frame, text=label).grid(
                row=row,
                column=0,
                sticky=tk.W,
                padx=(6, 8),
                pady=3,
            )
            widget.grid(row=row, column=1, sticky=tk.EW, padx=(0, 6), pady=3)

        basic_season_row = ttk.Frame(self.live_basic_frame)
        ttk.Entry(basic_season_row, textvariable=self.live_start_season_var, width=7).pack(side=tk.LEFT)
        ttk.Label(basic_season_row, text=" to ").pack(side=tk.LEFT)
        ttk.Entry(basic_season_row, textvariable=self.live_end_season_var, width=7).pack(side=tk.LEFT)
        add_basic_row(0, "Seasons", basic_season_row)

        game_row = ttk.Frame(self.live_basic_frame)
        ttk.Label(game_row, text="Season").pack(side=tk.LEFT)
        ttk.Entry(game_row, textvariable=self.live_game_season_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(game_row, text="Week").pack(side=tk.LEFT)
        ttk.Entry(game_row, textvariable=self.live_game_week_var, width=5).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Button(game_row, text="LOAD WEEK GAMES", command=self._load_live_week_games).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        ttk.Button(game_row, text="USE ACTIVE PICK", command=self._use_active_pick_for_live).pack(
            side=tk.LEFT,
        )
        add_basic_row(1, "Week games", game_row)

        self.live_game_box = ttk.Combobox(
            self.live_basic_frame,
            textvariable=self.live_game_var,
            values=[],
            state="readonly",
            width=24,
        )
        self.live_game_box.bind("<<ComboboxSelected>>", lambda _event: self._select_live_week_game())
        add_basic_row(2, "Game", self.live_game_box)

        self.live_perspective_box = ttk.Combobox(
            self.live_basic_frame,
            textvariable=self.live_perspective_var,
            values=[],
            state="readonly",
            width=24,
        )
        self.live_perspective_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._select_live_perspective(),
        )
        add_basic_row(3, "Analyze perspective", self.live_perspective_box)

        ttk.Label(
            self.live_basic_frame,
            textvariable=self.live_game_status_var,
            justify=tk.LEFT,
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=6, pady=(0, 4))

        add_basic_row(5, "Team A", ttk.Entry(self.live_basic_frame, textvariable=self.live_team_var, width=24))
        add_basic_row(
            6,
            "Opponent",
            ttk.Entry(self.live_basic_frame, textvariable=self.live_opponent_var, width=24),
        )
        basic_quarter_row = ttk.Frame(self.live_basic_frame)
        ttk.Label(basic_quarter_row, text="Q1").pack(side=tk.LEFT)
        ttk.Entry(basic_quarter_row, textvariable=self.live_q1_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(basic_quarter_row, text="Q2").pack(side=tk.LEFT)
        ttk.Entry(basic_quarter_row, textvariable=self.live_q2_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(basic_quarter_row, text="Q3").pack(side=tk.LEFT)
        ttk.Entry(basic_quarter_row, textvariable=self.live_q3_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 0),
        )
        add_basic_row(7, "Quarter scores", basic_quarter_row)
        basic_odds_row = ttk.Frame(self.live_basic_frame)
        ttk.Label(basic_odds_row, text="Decimal").pack(side=tk.LEFT)
        ttk.Entry(basic_odds_row, textvariable=self.live_decimal_var, width=8).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(basic_odds_row, text="ML").pack(side=tk.LEFT)
        ttk.Entry(basic_odds_row, textvariable=self.live_ml_var, width=8).pack(side=tk.LEFT, padx=(4, 0))
        add_basic_row(8, "Live odds", basic_odds_row)
        basic_settlement_box = ttk.Combobox(
            self.live_basic_frame,
            textvariable=self.live_settlement_var,
            values=["TIE_IS_LOSS", "TIE_IS_PUSH"],
            state="readonly",
            width=24,
        )
        add_basic_row(9, "Settlement", basic_settlement_box)

        season_row = ttk.Frame(self.live_settings_frame)
        ttk.Entry(season_row, textvariable=self.live_start_season_var, width=7).pack(side=tk.LEFT)
        ttk.Label(season_row, text=" to ").pack(side=tk.LEFT)
        ttk.Entry(season_row, textvariable=self.live_end_season_var, width=7).pack(side=tk.LEFT)
        add_row(0, "Seasons", season_row)

        path_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_lookup_path_var,
            values=LIVE_PATH_OPTIONS,
            state="readonly",
            width=24,
        )
        add_row(1, "Path", path_box)

        event_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_event_var,
            values=[
                "TEAM_A_WIN_FINAL",
                "TEAM_A_WIN_NEXT_QUARTER",
                "TEAM_A_LEAD_AFTER_NEXT_QUARTER",
            ],
            state="readonly",
            width=24,
        )
        add_row(2, "Event", event_box)

        settlement_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_settlement_var,
            values=["TIE_IS_LOSS", "TIE_IS_PUSH"],
            state="readonly",
            width=24,
        )
        add_row(3, "Settlement", settlement_box)

        odds_row = ttk.Frame(self.live_settings_frame)
        ttk.Label(odds_row, text="Decimal").pack(side=tk.LEFT)
        ttk.Entry(odds_row, textvariable=self.live_decimal_var, width=8).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(odds_row, text="ML").pack(side=tk.LEFT)
        ttk.Entry(odds_row, textvariable=self.live_ml_var, width=8).pack(side=tk.LEFT, padx=(4, 0))
        add_row(4, "Live odds", odds_row)

        quarter_row = ttk.Frame(self.live_settings_frame)
        ttk.Label(quarter_row, text="Q1").pack(side=tk.LEFT)
        ttk.Entry(quarter_row, textvariable=self.live_q1_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(quarter_row, text="Q2").pack(side=tk.LEFT)
        ttk.Entry(quarter_row, textvariable=self.live_q2_var, width=7).pack(
            side=tk.LEFT,
            padx=(4, 8),
        )
        ttk.Label(quarter_row, text="Q3").pack(side=tk.LEFT)
        ttk.Entry(quarter_row, textvariable=self.live_q3_var, width=7).pack(side=tk.LEFT, padx=(4, 0))
        add_row(5, "Quarter scores", quarter_row)

        sample_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_sample_mode_var,
            values=["LEAGUE_WIDE", "TEAM_A_HISTORY", "TEAM_B_HISTORY", "HEAD_TO_HEAD"],
            state="readonly",
            width=24,
        )
        add_row(6, "Sample", sample_box)

        add_row(7, "Team A", ttk.Entry(self.live_settings_frame, textvariable=self.live_team_var, width=24))
        add_row(
            8,
            "Opponent",
            ttk.Entry(self.live_settings_frame, textvariable=self.live_opponent_var, width=24),
        )

        role_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_role_var,
            values=["", "FAVORITE", "UNDERDOG", "PICKEM_OR_UNKNOWN"],
            state="readonly",
            width=24,
        )
        add_row(9, "Role", role_box)

        side_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_side_var,
            values=["", "home", "away"],
            state="readonly",
            width=24,
        )
        add_row(10, "Side", side_box)

        spread_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_spread_bucket_var,
            values=["", "0.5-1.5", "2-3", "3.5-4.5", "5-6", "6.5-7", "7.5-9.5", "10-13.5", "14+"],
            width=24,
        )
        add_row(11, "Spread", spread_box)

        phase_box = ttk.Combobox(
            self.live_settings_frame,
            textvariable=self.live_phase_var,
            values=["", "EARLY", "MIDDLE", "LATE"],
            state="readonly",
            width=24,
        )
        add_row(12, "Phase", phase_box)

        self._build_live_batch_tab()

        for var in [
            self.live_start_season_var,
            self.live_end_season_var,
            self.live_lookup_path_var,
            self.live_event_var,
            self.live_settlement_var,
            self.live_q1_var,
            self.live_q2_var,
            self.live_q3_var,
            self.live_sample_mode_var,
            self.live_team_var,
            self.live_opponent_var,
            self.live_role_var,
            self.live_side_var,
            self.live_spread_bucket_var,
            self.live_phase_var,
        ]:
            var.trace_add("write", lambda *_args: self._update_live_active_summary())

        self.live_run_button = ttk.Button(
            container,
            text="RUN LIVE LOOKUP",
            command=lambda: self._run_live_scenario(rebuild_only=False),
        )
        self.live_compare_button = ttk.Button(
            container,
            text="RUN BASIC AFTER Q2",
            command=self._run_team_history_compare,
        )
        self.live_compare_button.pack(fill=tk.X, ipady=7, pady=(0, 8))

        self.live_buttons.extend([self.live_run_button, self.live_compare_button])

        self.live_summary_frame = ttk.LabelFrame(container, text="Summary")
        summary_frame = self.live_summary_frame
        summary_frame.pack(fill=tk.X, pady=(0, 8))
        self.live_result_var = tk.StringVar(value="")
        self.live_summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=7)
        self.live_summary_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0), pady=6)
        summary_scroll = ttk.Scrollbar(summary_frame, command=self.live_summary_text.yview)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 6), pady=6)
        self.live_summary_text.configure(yscrollcommand=summary_scroll.set)
        self._set_live_summary("Brak wyniku. Wybierz Path/Event i kliknij RUN LIVE LOOKUP.")

        forum_frame = ttk.LabelFrame(container, text="FORUM POST")
        forum_frame.pack(fill=tk.X, pady=(0, 8))
        self.live_forum_text = tk.Text(forum_frame, wrap=tk.WORD, height=8)
        self.live_forum_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        forum_scroll = ttk.Scrollbar(forum_frame, command=self.live_forum_text.yview)
        forum_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.live_forum_text.configure(yscrollcommand=forum_scroll.set)
        self.copy_forum_button = ttk.Button(
            container,
            text="COPY FORUM POST",
            command=self._copy_forum_post,
        )
        self.copy_forum_button.pack(fill=tk.X, pady=(0, 8))
        self.live_buttons.append(self.copy_forum_button)

        tools = ttk.Frame(container)
        tools.pack(fill=tk.X, pady=(0, 8))
        rebuild_live_button = ttk.Button(
            tools,
            text="Rebuild matrix",
            command=lambda: self._run_live_scenario(rebuild_only=True),
        )
        rebuild_live_button.pack(side=tk.LEFT, padx=(0, 6))
        open_live_button = ttk.Button(
            tools,
            text="Open folder",
            command=self._open_live_scenario_folder,
        )
        open_live_button.pack(side=tk.LEFT)
        self.live_buttons.extend([rebuild_live_button, open_live_button])

        tabs = ttk.Notebook(container)
        tabs.pack(fill=tk.BOTH, expand=True)

        calc_tab = ttk.Frame(tabs)
        raw_tab = ttk.Frame(tabs)
        tabs.add(calc_tab, text="Calculations")
        tabs.add(raw_tab, text="Raw Output")

        self.live_calculations_text = tk.Text(calc_tab, wrap=tk.WORD, height=8)
        self.live_calculations_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        calc_scroll = ttk.Scrollbar(calc_tab, command=self.live_calculations_text.yview)
        calc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.live_calculations_text.configure(yscrollcommand=calc_scroll.set)

        self.live_raw_text = tk.Text(raw_tab, wrap=tk.WORD, height=8)
        self.live_raw_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        raw_scroll = ttk.Scrollbar(raw_tab, command=self.live_raw_text.yview)
        raw_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.live_raw_text.configure(yscrollcommand=raw_scroll.set)

        self._sync_live_run_buttons()
        self._update_live_active_summary()

    def _build_live_batch_tab(self) -> None:
        """Build the operator-facing multi-game halftime form."""
        tab = self.live_batch_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        controls = ttk.Frame(tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.live_batch_season_var = tk.StringVar(value="2026")
        self.live_batch_week_var = tk.StringVar(value="1")
        self.live_batch_block_var = tk.StringVar(value="")
        ttk.Label(controls, text="Season").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.live_batch_season_var, width=7).pack(
            side=tk.LEFT, padx=(4, 8)
        )
        ttk.Label(controls, text="Week").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.live_batch_week_var, width=5).pack(
            side=tk.LEFT, padx=(4, 8)
        )
        ttk.Button(controls, text="REFRESH BLOCKS", command=self._refresh_live_batch_games).pack(
            side=tk.LEFT
        )

        block_row = ttk.Frame(tab)
        block_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(block_row, text="Kickoff block").pack(side=tk.LEFT)
        self.live_batch_block_box = ttk.Combobox(
            block_row,
            textvariable=self.live_batch_block_var,
            values=[],
            state="readonly",
            width=28,
        )
        self.live_batch_block_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self.live_batch_block_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._render_live_batch_rows(),
        )

        self.live_batch_status_var = tk.StringVar(value="Brak wybranego bloku.")
        ttk.Label(tab, textvariable=self.live_batch_status_var, justify=tk.LEFT).grid(
            row=3, column=0, sticky="ew", pady=(6, 4)
        )

        table_shell = ttk.Frame(tab)
        table_shell.grid(row=2, column=0, sticky="nsew")
        table_shell.columnconfigure(0, weight=1)
        table_shell.rowconfigure(0, weight=1)
        self.live_batch_canvas = tk.Canvas(table_shell, height=620, highlightthickness=0)
        self.live_batch_canvas.grid(row=0, column=0, sticky="nsew")
        batch_scroll = ttk.Scrollbar(table_shell, orient=tk.VERTICAL, command=self.live_batch_canvas.yview)
        batch_scroll.grid(row=0, column=1, sticky="ns")
        self.live_batch_canvas.configure(yscrollcommand=batch_scroll.set)
        self.live_batch_rows_frame = ttk.Frame(self.live_batch_canvas)
        batch_window = self.live_batch_canvas.create_window(
            (0, 0), window=self.live_batch_rows_frame, anchor=tk.NW
        )
        self.live_batch_rows_frame.bind(
            "<Configure>",
            lambda _event: self.live_batch_canvas.configure(
                scrollregion=self.live_batch_canvas.bbox("all")
            ),
        )
        self.live_batch_canvas.bind(
            "<Configure>",
            lambda event: self.live_batch_canvas.itemconfigure(batch_window, width=event.width),
        )

        actions = ttk.Frame(tab)
        actions.grid(row=4, column=0, sticky="ew", pady=(6, 4))
        self.live_batch_generate_button = ttk.Button(
            actions, text="GENERUJ ZBIORCZY POST", command=self._generate_live_batch_post
        )
        self.live_batch_generate_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.live_batch_partial_button = ttk.Button(
            actions, text="GENERUJ TYLKO GOTOWE", command=self._generate_live_batch_partial
        )
        self.live_batch_partial_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.live_batch_copy_button = ttk.Button(
            tab, text="KOPIUJ ZBIORCZY POST", command=self._copy_live_batch_post
        )
        self.live_batch_copy_button.grid(row=5, column=0, sticky="ew", pady=(0, 4))
        self.live_batch_output = tk.Text(tab, wrap=tk.WORD, height=10)
        self.live_batch_output.grid(row=6, column=0, sticky="nsew")
        self.live_batch_output.configure(state=tk.DISABLED)

    def _refresh_live_batch_games(self) -> None:
        try:
            season = int(self.live_batch_season_var.get().strip())
            week = int(self.live_batch_week_var.get().strip())
        except ValueError:
            self.live_batch_status_var.set("Season i Week musza byc liczbami.")
            return
        try:
            games, metadata = load_week_games(
                data_root=REPO_ROOT / "data",
                season=season,
                week=week,
                picks_path=self._live_picks_path_for_week(season, week),
            )
        except Exception as exc:
            self._log_live_week_games_exception(season, week, exc)
            self.live_batch_status_var.set(f"Schedule refresh failed: {exc}")
            return
        previous = dict(self.live_batch_entries)
        self.live_batch_all_games = games
        self.live_batch_metadata = metadata
        self.live_batch_entries = {
            entry.game_id: entry
            for entry in build_entries(games, previous=previous)
        }
        blocks = block_options(games)
        self.live_batch_block_box.configure(values=blocks)
        if not blocks:
            self.live_batch_block_var.set("")
            self._render_live_batch_rows()
            self.live_batch_status_var.set(
                f"Brak meczow dla {season} Week {week}. Zrodlo: {metadata.get('schedule_source', 'MISSING')}"
            )
            return
        if self.live_batch_block_var.get() not in blocks:
            self.live_batch_block_var.set(blocks[0])
        self.live_batch_output_dirty = True
        self._render_live_batch_rows()

    def _batch_current_entries(self) -> list[BatchGameInput]:
        games = games_for_block(self.live_batch_all_games, self.live_batch_block_var.get())
        return [self.live_batch_entries[game.game_id] for game in games]

    def _render_live_batch_rows(self) -> None:
        if not hasattr(self, "live_batch_rows_frame"):
            return
        self.live_batch_output_dirty = True
        for child in self.live_batch_rows_frame.winfo_children():
            child.destroy()
        self.live_batch_row_widgets = {}
        entries = self._batch_current_entries()
        headers = ["Game", "Q1 A-H", "Q2 A-H", "Spread A (away)", "Status"]
        for column, header in enumerate(headers):
            ttk.Label(
                self.live_batch_rows_frame, text=header, font=("Segoe UI", 9, "bold")
            ).grid(row=0, column=column, sticky=tk.W, padx=2, pady=2)
        for row, entry in enumerate(entries, start=1):
            ttk.Label(
                self.live_batch_rows_frame,
                text=f"{entry.label}\n{entry.game_id}",
                justify=tk.LEFT,
                width=22,
            ).grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
            q1_away = tk.StringVar(value=entry.q1_away)
            q1_home = tk.StringVar(value=entry.q1_home)
            q2_away = tk.StringVar(value=entry.q2_away)
            q2_home = tk.StringVar(value=entry.q2_home)
            spread = tk.StringVar(value=entry.spread_away)
            status = tk.StringVar(value=entry.status)
            fields = {
                "q1_away": q1_away,
                "q1_home": q1_home,
                "q2_away": q2_away,
                "q2_home": q2_home,
                "spread_away": spread,
                "status": status,
            }
            for variable in fields.values():
                variable.trace_add(
                    "write",
                    lambda *_args, current=entry, values=fields: self._batch_field_changed(
                        current, values
                    ),
                )
            q1_frame = ttk.Frame(self.live_batch_rows_frame)
            ttk.Entry(q1_frame, textvariable=q1_away, width=3).pack(side=tk.LEFT)
            ttk.Label(q1_frame, text="-").pack(side=tk.LEFT)
            ttk.Entry(q1_frame, textvariable=q1_home, width=3).pack(side=tk.LEFT)
            q1_frame.grid(row=row, column=1, padx=2, pady=2)
            q2_frame = ttk.Frame(self.live_batch_rows_frame)
            ttk.Entry(q2_frame, textvariable=q2_away, width=3).pack(side=tk.LEFT)
            ttk.Label(q2_frame, text="-").pack(side=tk.LEFT)
            ttk.Entry(q2_frame, textvariable=q2_home, width=3).pack(side=tk.LEFT)
            q2_frame.grid(row=row, column=2, padx=2, pady=2)
            ttk.Entry(self.live_batch_rows_frame, textvariable=spread, width=7).grid(
                row=row, column=3, padx=2, pady=2
            )
            ttk.Combobox(
                self.live_batch_rows_frame,
                textvariable=status,
                values=["NOT_AT_HALFTIME", "READY", "INCLUDED", "EXCLUDED", "ERROR"],
                state="readonly",
                width=17,
            ).grid(row=row, column=4, padx=2, pady=2)
            self.live_batch_row_widgets[entry.game_id] = fields
        self._update_live_batch_completeness()

    def _batch_field_changed(self, entry: BatchGameInput, values: dict[str, tk.StringVar]) -> None:
        entry.q1_away = values["q1_away"].get().strip()
        entry.q1_home = values["q1_home"].get().strip()
        entry.q2_away = values["q2_away"].get().strip()
        entry.q2_home = values["q2_home"].get().strip()
        entry.spread_away = values["spread_away"].get().strip()
        current_status = values["status"].get().strip().upper()
        if current_status == "INCLUDED":
            current_status = "READY"
            values["status"].set(current_status)
        if current_status in {"NOT_AT_HALFTIME", "ERROR"} and all(
            [entry.q1_away, entry.q1_home, entry.q2_away, entry.q2_home]
        ):
            current_status = "READY"
            values["status"].set(current_status)
        entry.status = current_status
        entry.updated_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        entry.error = ""
        self.live_batch_output_dirty = True
        self._update_live_batch_completeness()

    def _update_live_batch_completeness(self) -> None:
        if not hasattr(self, "live_batch_status_var"):
            return
        entries = self._batch_current_entries()
        if not entries:
            self.live_batch_status_var.set("Wybierz kickoff block.")
            return
        summary = completeness(entries)
        self.live_batch_status_var.set(
            "\n".join(
                [
                    f"Wybrany blok: {summary.total} meczow",
                    f"Gotowe: {summary.ready} | Wlaczone: {summary.included} | "
                    f"Nie w przerwie: {summary.not_at_halftime} | Wykluczone: {summary.excluded}",
                    f"Bledy: {summary.errors} | Nieuzupelnione/niesklasyfikowane: {summary.unclassified}",
                    (
                        f"Zrodlo: {(self.live_batch_metadata or {}).get('schedule_source', 'MISSING')} | "
                        f"timestamp: {(self.live_batch_metadata or {}).get('schedule_timestamp_utc') or 'MISSING'}"
                    ),
                ]
            )
        )

    def _generate_live_batch_post(self) -> None:
        self._generate_live_batch(allow_partial=False)

    def _generate_live_batch_partial(self) -> None:
        self._generate_live_batch(allow_partial=True)

    def _generate_live_batch(self, *, allow_partial: bool) -> None:
        entries = self._batch_current_entries()
        if not entries:
            messagebox.showerror("Empty batch", "Najpierw odswiez liste i wybierz blok kickoff.")
            return
        try:
            season = int(self.live_batch_season_var.get())
            week = int(self.live_batch_week_var.get())
        except ValueError:
            messagebox.showerror("Invalid batch", "Season i Week musza byc liczbami.")
            return
        validations = [validate_entry(entry) for entry in entries]
        for validation in validations:
            entry = self.live_batch_entries[validation.game_id]
            entry.error = validation.error
            if validation.status == "ERROR":
                entry.status = "ERROR"
                row_fields = self.live_batch_row_widgets.get(validation.game_id, {})
                status_var = row_fields.get("status")
                if isinstance(status_var, tk.StringVar):
                    status_var.set("ERROR")
        issues = {
            validation.game_id: validation.error or validation.status
            for validation in validations
            if validation.status not in {"READY", "INCLUDED", "NOT_AT_HALFTIME", "EXCLUDED"}
        }
        if issues and not allow_partial:
            self._update_live_batch_completeness()
            messagebox.showerror(
                "Batch niekompletny",
                "Nie mozna wygenerowac kompletnego posta.\n\n"
                + "\n".join(f"{game_id}: {reason}" for game_id, reason in issues.items()),
            )
            return
        if not LIVE_SCENARIO_PROCESSED.exists():
            messagebox.showerror("Missing dataset", f"Brak pliku: {LIVE_SCENARIO_PROCESSED}")
            return
        try:
            historical_rows = pd.read_parquet(LIVE_SCENARIO_PROCESSED)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            result = generate_batch_post(
                entries,
                historical_rows,
                season=season,
                week=week,
                block=self.live_batch_block_var.get(),
                data_cutoff_utc=now,
                generated_at_utc=now,
                tie_policy="TIE_AS_PUSH" if self.live_settlement_var.get() == "TIE_IS_PUSH" else "TIE_AS_LOSS",
                allow_partial=allow_partial,
            )
        except BatchValidationError as exc:
            messagebox.showerror("Batch error", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Batch calculation error", str(exc))
            return
        for game_id in result.included_game_ids:
            self.live_batch_entries[game_id].status = "INCLUDED"
            row_fields = self.live_batch_row_widgets.get(game_id, {})
            status_var = row_fields.get("status")
            if isinstance(status_var, tk.StringVar):
                status_var.set("INCLUDED")
        self._set_live_batch_output(result.text)
        self.live_batch_output_dirty = False
        self._update_live_batch_completeness()
        mode = "czesciowy" if result.partial else "kompletny"
        self.live_batch_status_var.set(
            f"Wygenerowano {mode} post: {len(result.included_game_ids)} z {len(entries)} meczow."
        )

    def _set_live_batch_output(self, text: str) -> None:
        self.live_batch_output.configure(state=tk.NORMAL)
        self.live_batch_output.delete("1.0", tk.END)
        self.live_batch_output.insert(tk.END, text)
        self.live_batch_output.configure(state=tk.DISABLED)

    def _copy_live_batch_post(self) -> None:
        if self.live_batch_output_dirty:
            messagebox.showerror("Output nieaktualny", "Zmieniono dane. Wygeneruj zbiorczy post ponownie.")
            return
        text = self.live_batch_output.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Pusty post", "Najpierw wygeneruj zbiorczy post.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        included = sum(entry.status == "INCLUDED" for entry in self._batch_current_entries())
        self.live_batch_status_var.set(f"Skopiowano zbiorczy post: {included} meczow.")

    def _day_label(self, day: str) -> str:
        return dict(DAY_OPTIONS).get(day, "")

    def _effective_day(self) -> str:
        selected = self.day_var.get()
        if selected != "auto":
            return selected
        weekday_map = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday",
        }
        return weekday_map[datetime.now().astimezone().weekday()]

    def _update_clock(self) -> None:
        now = datetime.now().astimezone()
        day = self._effective_day()
        day_label = DAY_LABELS_PL.get(day, day)
        self.now_var.set(f"Dzisiaj: {now:%Y-%m-%d %H:%M} | {day_label} | auto => {day}")
        self.after(60_000, self._update_clock)

    def _refresh_day_plan(self) -> None:
        selected = self.day_var.get()
        day = self._effective_day()
        self.day_help_var.set(self._day_label(selected))
        days = self.bot_config.get("days", {})
        day_config = days.get(day, {})
        self._sync_snapshot_type_for_day(day_config)
        self.plan_text.configure(state=tk.NORMAL)
        self.plan_text.delete("1.0", tk.END)
        if not day_config:
            self.plan_text.insert(tk.END, f"Brak planu dla dnia: {day}\n")
            self.plan_text.configure(state=tk.DISABLED)
            return
        if selected == "auto":
            self.plan_text.insert(tk.END, f"Auto resolved day: {day}\n\n")
        self.plan_text.insert(tk.END, f"{day_config.get('label', day)}\n\n")
        self.plan_text.insert(tk.END, "Cel:\n")
        self.plan_text.insert(tk.END, f"{day_config.get('objective', '')}\n\n")
        self.plan_text.insert(tk.END, "Zadania:\n")
        for idx, task in enumerate(day_config.get("tasks", []), start=1):
            task_type = task.get("type", "unknown")
            label = task.get("label", "")
            self.plan_text.insert(tk.END, f"{idx}. [{task_type}] {label}\n")
            if task_type == "command":
                self.plan_text.insert(tk.END, f"   command: {task.get('command', '')}\n")
            elif task_type == "manual":
                self.plan_text.insert(tk.END, f"   input: {task.get('input', '')}\n")
            elif task_type == "check_path":
                self.plan_text.insert(tk.END, f"   path: {task.get('path', '')}\n")
        self.plan_text.configure(state=tk.DISABLED)
        self._generate_gpt_prompt()

    def _sync_snapshot_type_for_day(self, day_config: dict) -> None:
        prompt_type = str(day_config.get("gpt_prompt_type", "delta_refresh"))
        expected_type = "full_19_points" if prompt_type == "full_19_points" else "delta_refresh"
        if self.gpt_snapshot_type_var.get() != expected_type:
            self.gpt_snapshot_type_var.set(expected_type)

    def _validate(self) -> tuple[int, int] | None:
        try:
            season = int(self.season_var.get())
            week = int(self.week_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Season i Week musza byc liczbami.")
            return None
        if season <= 0 or week <= 0:
            messagebox.showerror("Invalid input", "Season i Week musza byc dodatnie.")
            return None
        return season, week

    def _picks_path(self) -> Path | None:
        values = self._validate()
        if values is None:
            return None
        season, week = values
        variant = str(self.bot_config.get("variant", "variant_m"))
        return REPO_ROOT / "data" / f"picks_{variant}" / str(season) / f"week_{week:02d}.jsonl"

    def _load_model_picks(self) -> None:
        path = self._picks_path()
        if path is None:
            return
        self.model_pick_records = {}
        self.watch_records = {}
        if not path.exists():
            self.pick_box.configure(values=[])
            self.watch_box.configure(values=[])
            self.pick_var.set("")
            self.watch_var.set("")
            self.pick_summary_var.set(f"Pick file missing: {path}")
            self.watch_summary_var.set("Watchlist unavailable.")
            return
        records = []
        watch_records = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tag = str(record.get("tag") or "").upper()
                if tag in ACTION_TAGS:
                    records.append(record)
                elif is_watchlist_record(record):
                    watch_records.append(record)
        watch_records.sort(
            key=lambda record: abs(float(record.get("edge_vs_line") or 0)),
            reverse=True,
        )
        labels = []
        for record in records:
            label = self._pick_label(record)
            labels.append(label)
            self.model_pick_records[label] = record
        watch_labels = []
        for record in watch_records:
            label = self._pick_label(record, prefix="WATCH")
            watch_labels.append(label)
            self.watch_records[label] = record
        self.pick_box.configure(values=labels)
        self.watch_box.configure(values=watch_labels)
        if labels:
            self.pick_var.set(labels[0])
            self._select_model_pick()
            self.pick_summary_var.set(f"Loaded {len(labels)} action pick(s) from {path.name}.")
        else:
            self.pick_var.set("")
            self.pick_summary_var.set(f"No VP/GOW/GOM/GOY found in {path.name}.")
        if watch_labels:
            self.watch_var.set(watch_labels[0])
            self.watch_summary_var.set(
                f"Loaded {len(watch_labels)} watchlist candidate(s), min abs edge {WATCHLIST_MIN_ABS_EDGE}."
            )
        else:
            self.watch_var.set("")
            self.watch_summary_var.set("No neutral watchlist candidates found.")

    def _live_picks_path_for_week(self, season: int, week: int) -> Path:
        variant = str(self.bot_config.get("variant", "variant_m"))
        return REPO_ROOT / "data" / f"picks_{variant}" / str(season) / f"week_{week:02d}.jsonl"

    def _log_live_week_games_exception(self, season: int, week: int, exc: BaseException) -> None:
        LIVE_WEEK_GAMES_DIAGNOSTIC_LOG.parent.mkdir(parents=True, exist_ok=True)
        with LIVE_WEEK_GAMES_DIAGNOSTIC_LOG.open("a", encoding="utf-8") as handle:
            handle.write("\n===== LOAD WEEK GAMES ERROR =====\n")
            handle.write(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}\n")
            handle.write(f"season={season} week={week}\n")
            handle.write(f"error={exc}\n")
            handle.write(traceback.format_exc())
            handle.write("\n")

    def _load_live_week_games(self) -> None:
        try:
            season = int(self.live_game_season_var.get().strip())
            week = int(self.live_game_week_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid week games input", "Season i Week musza byc liczbami.")
            return
        try:
            games, metadata = load_week_games(
                data_root=REPO_ROOT / "data",
                season=season,
                week=week,
                picks_path=self._live_picks_path_for_week(season, week),
            )
        except ScheduleLoadError as exc:
            self._log_live_week_games_exception(season, week, exc)
            self.live_week_games = {}
            self.live_active_game = None
            self.live_week_games_metadata = None
            self.live_game_box.configure(values=[])
            self.live_perspective_box.configure(values=[])
            self.live_game_var.set("")
            self.live_perspective_var.set("")
            self.live_game_status_var.set(f"Schedule refresh failed: {exc}")
            self.live_status_var.set("WEEK GAMES FAILED")
            return
        except Exception as exc:
            self._log_live_week_games_exception(season, week, exc)
            self.live_game_status_var.set(f"Schedule refresh failed: {exc}")
            self.live_status_var.set("WEEK GAMES FAILED")
            return
        self.live_week_games = {game.label: game for game in games}
        self.live_week_games_metadata = metadata
        labels = [game.label for game in games]
        self.live_game_box.configure(values=labels)
        if not games:
            self.live_game_var.set("")
            self.live_perspective_box.configure(values=[])
            self.live_perspective_var.set("")
            diagnostics = metadata.get("diagnostics", {})
            sources = diagnostics.get("sources_checked", []) if isinstance(diagnostics, dict) else []
            season_seen = any(season in set(source.get("seasons") or []) for source in sources)
            status = (
                f"Schedule source does not contain season {season}."
                if sources and not season_seen
                else f"No games found for {season} Week {week}."
            )
            self.live_game_status_var.set(
                "\n".join(
                    [
                        status,
                        f"Schedule source: {metadata['schedule_source']}",
                        f"Dataset timestamp: {metadata.get('schedule_timestamp_utc') or 'MISSING'}",
                    ]
                )
            )
            self.live_status_var.set("WEEK GAMES MISSING")
            return
        self.live_game_status_var.set(
            "\n".join(
                [
                    f"Loaded {len(games)} games for {season} Week {week}.",
                    f"Schedule source: {metadata['schedule_source']}",
                    f"Dataset timestamp: {metadata.get('schedule_timestamp_utc') or 'MISSING'}",
                    f"Combobox values: {len(labels)}",
                ]
            )
        )
        self.live_status_var.set("WEEK GAMES LOADED")
        self.live_game_var.set(labels[0])
        self._select_live_week_game()

    def _select_live_week_game(self) -> None:
        game = self.live_week_games.get(self.live_game_var.get())
        if game is None:
            return
        self.live_active_game = game
        self.game_id_var.set(game.game_id)
        self.live_perspective_box.configure(values=[game.away, game.home])
        current = self.live_perspective_var.get().strip().upper()
        if current not in {game.away, game.home}:
            self.live_perspective_var.set(game.away)
        self._apply_live_game_perspective(game, self.live_perspective_var.get(), swap_scores=False)

    def _select_live_perspective(self) -> None:
        game = self.live_active_game
        if game is None:
            return
        new_team = self.live_perspective_var.get().strip().upper()
        swap_scores = self.live_current_perspective in {game.away, game.home} and new_team != self.live_current_perspective
        self._apply_live_game_perspective(game, new_team, swap_scores=swap_scores)

    def _apply_live_game_perspective(self, game: WeekGame, team: str, *, swap_scores: bool) -> None:
        try:
            perspective = game.perspective(team)
        except ValueError:
            return
        if swap_scores:
            self._invert_live_quarter_scores()
        self.live_current_perspective = perspective.team
        self.live_team_var.set(perspective.team)
        self.live_opponent_var.set(perspective.opponent)
        self.live_side_var.set(perspective.side)
        self.live_role_var.set(perspective.role)
        self.live_spread_bucket_var.set(
            self._spread_bucket(abs(perspective.spread)) if perspective.spread is not None else ""
        )
        status_lines = [
            (
                f"Loaded {self.live_week_games_metadata.get('games_found')} games for "
                f"{game.season} Week {game.week}."
                if self.live_week_games_metadata
                else ""
            ),
            f"{game.label} | perspective={perspective.team}",
            f"{game.model_status}",
            f"date={game.game_date} {game.game_time} | neutral={game.neutral_site}",
            (
                f"spread={perspective.spread if perspective.spread is not None else 'MISSING'} "
                f"| source={game.spread_source} | status={game.spread_status}"
            ),
        ]
        if game.model_edge is not None or game.model_margin is not None:
            status_lines.append(f"model edge={game.model_edge} | model margin={game.model_margin}")
        self.live_game_status_var.set("\n".join(line for line in status_lines if line))
        self._update_live_active_summary()

    def _invert_live_quarter_scores(self) -> None:
        self.live_q1_var.set(invert_score_pair(self.live_q1_var.get()))
        self.live_q2_var.set(invert_score_pair(self.live_q2_var.get()))
        self.live_q3_var.set(invert_score_pair(self.live_q3_var.get()))

    def _use_active_pick_for_live(self) -> None:
        record = self.selected_pick_record
        if not record:
            messagebox.showerror("No active pick", "Najpierw wybierz aktywny pick po lewej stronie.")
            return
        try:
            season = int(record.get("season") or self.season_var.get())
            week = int(record.get("week") or self.week_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid active pick", "Aktywny pick nie ma poprawnego season/week.")
            return
        self.live_game_season_var.set(str(season))
        self.live_game_week_var.set(str(week))
        if not self.live_week_games:
            self._load_live_week_games()
        away = str(record.get("away") or "").upper()
        home = str(record.get("home") or "").upper()
        label = label_for_active_pick(record, self.live_week_games) or f"{away} @ {home}"
        if label not in self.live_week_games:
            self._load_live_week_games()
        if label not in self.live_week_games:
            messagebox.showerror("Game not found", f"Nie znaleziono meczu w lokalnym schedule: {label}")
            return
        self.live_game_var.set(label)
        self._select_live_week_game()
        selected = str(record.get("model_winner") or away).upper()
        if selected in {away, home}:
            self.live_perspective_var.set(selected)
            self._select_live_perspective()

    def _pick_label(self, record: dict, *, prefix: str | None = None) -> str:
        game_id = build_game_id(record)
        away = str(record.get("away") or "").upper()
        home = str(record.get("home") or "").upper()
        tag = str(record.get("tag") or "").upper()
        selected = str(record.get("model_winner") or "").upper()
        edge = record.get("edge_vs_line")
        line = record.get("handicap", record.get("line"))
        price = record.get("price")
        lead = f"{prefix} | " if prefix else ""
        return (
            f"{lead}{game_id} | {away} at {home} | {selected} | {tag} | "
            f"edge {edge} | line {line} | price {price}"
        )

    def _select_model_pick(self) -> None:
        record = self.model_pick_records.get(self.pick_var.get())
        if not record:
            return
        self._select_pick_record(record)

    def _select_watchlist_pick(self) -> None:
        record = self.watch_records.get(self.watch_var.get())
        if not record:
            return
        self._select_pick_record(record, watchlist=True)

    def _select_pick_record(self, record: dict, *, watchlist: bool = False) -> None:
        self.selected_pick_record = record
        game_id = build_game_id(record)
        self.game_id_var.set(game_id)
        tag = str(record.get("tag") or "").upper()
        selected = str(record.get("model_winner") or "").upper()
        edge = record.get("edge_vs_line")
        line = record.get("handicap", record.get("line"))
        price = record.get("price")
        book = record.get("book") or record.get("odds_source") or "UNKNOWN"
        target = self.watch_summary_var if watchlist else self.pick_summary_var
        target.set(f"Selected {game_id}: {selected} {tag}, edge={edge}, line={line}.")
        self.active_match_var.set(
            f"{game_id} | pick: {selected} {line} | tag: {tag} | edge: {edge} | "
            f"price: {price} | source: {book} | quote status: {self.quote_status_var.get()}"
        )
        self._populate_live_from_pick(record)
        self._populate_quote_from_pick(record)
        self._generate_gpt_prompt()

    def _populate_quote_from_pick(self, record: dict) -> None:
        self.quote_book_var.set(str(record.get("book") or ""))
        self.quote_spread_var.set(str(record.get("handicap", record.get("line", ""))))
        self.quote_price_var.set(str(record.get("price") or ""))
        self.quote_timestamp_var.set("")
        self.quote_status_var.set("DISPLAYED_UNVERIFIED")

    def _set_quote_timestamp_now(self) -> None:
        self.quote_timestamp_var.set(datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))

    def _save_market_quote(self) -> None:
        values = self._validate()
        record = self.selected_pick_record
        if values is None or record is None:
            messagebox.showerror("No pick selected", "Najpierw wybierz pick z listy.")
            return
        try:
            spread = float(self.quote_spread_var.get().strip())
            price = int(self.quote_price_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid quote", "Spread musi byc liczba, a Price liczba calkowita, np. -110.")
            return
        book = self.quote_book_var.get().strip()
        timestamp = self.quote_timestamp_var.get().strip()
        if not book or not timestamp:
            messagebox.showerror("Missing quote data", "Podaj book i UTC timestamp (mozna kliknac Use current UTC).")
            return
        season, week = values
        away = str(record.get("away") or "").upper()
        home = str(record.get("home") or "").upper()
        selected = str(record.get("model_winner") or "").upper()
        path = REPO_ROOT / "data" / "market_quotes" / str(season) / f"week_{week:02d}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        if path.exists():
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        quote = {
            "season": season, "week": week, "away": away, "home": home, "selected_team": selected,
            "market": "full-game spread", "spread": spread, "line": spread, "price": price,
            "book": book, "quote_timestamp_utc": timestamp,
            "quote_id": f"{season}_w{week:02d}_{away}_at_{home}_{selected}_{timestamp.replace(':', '').replace('-', '')}",
            "executable_status": self.quote_status_var.get(), "target_stake": 100,
            "source_type": "DIRECT_BOOK", "market_scope": "FULL_GAME", "house_rules_checked": False,
            "betslip_verified_at_utc": timestamp if self.quote_status_var.get() == "BETSLIP_CONFIRMED_AT_TARGET_STAKE" else "",
            "odds_source": "gui_market_quote", "odds_snapshot_type": "decision",
        }
        rows = [row for row in rows if not (row.get("away") == away and row.get("home") == home and row.get("selected_team") == selected)]
        rows.append(quote)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        self._write_line(f"Saved market quote: {path} ({selected} {spread} {price}, {book})")
        self.active_match_var.set(
            f"{season}_w{week:02d}_{away}_at_{home} | pick: {selected} {spread} | "
            f"price: {price} | source: {book} | quote status: {self.quote_status_var.get()} | saved"
        )

    def _populate_live_from_pick(self, record: dict) -> None:
        away = str(record.get("away") or "").upper()
        home = str(record.get("home") or "").upper()
        selected = str(record.get("model_winner") or "").upper()
        if selected not in {away, home}:
            return
        opponent = home if selected == away else away
        self.live_sample_mode_var.set("TEAM_A_HISTORY")
        self.live_lookup_path_var.set("WIN-WIN")
        self.live_event_var.set("TEAM_A_WIN_FINAL")
        self.live_team_var.set(selected)
        self.live_opponent_var.set(opponent)
        self.live_side_var.set("away" if selected == away else "home")
        line = record.get("handicap", record.get("line"))
        try:
            spread = float(line)
        except (TypeError, ValueError):
            spread = 0.0
        if spread < 0:
            self.live_role_var.set("FAVORITE")
        elif spread > 0:
            self.live_role_var.set("UNDERDOG")
        else:
            self.live_role_var.set("PICKEM_OR_UNKNOWN")
        self.live_spread_bucket_var.set(self._spread_bucket(abs(spread)))
        week = record.get("week")
        try:
            week_num = int(week)
        except (TypeError, ValueError):
            week_num = 1
        if week_num <= 5:
            self.live_phase_var.set("EARLY")
        elif week_num <= 11:
            self.live_phase_var.set("MIDDLE")
        else:
            self.live_phase_var.set("LATE")
        self._update_live_active_summary()

    def _on_live_mode_changed(self) -> None:
        if not hasattr(self, "live_settings_notebook"):
            return
        current = self.live_settings_notebook.index("current")
        self.live_mode_var.set("BASIC_AFTER_Q2" if current == 0 else "MANUAL_LOOKUP")
        self.live_settings_notebook.configure(height=420 if current == 0 else 445)
        self._sync_live_run_buttons()
        self._update_live_active_summary()
        if hasattr(self, "live_canvas"):
            self.after_idle(lambda: self.live_canvas.configure(scrollregion=self.live_canvas.bbox("all")))

    def _sync_live_run_buttons(self) -> None:
        if not hasattr(self, "live_run_button") or not hasattr(self, "live_compare_button"):
            return
        self.live_run_button.pack_forget()
        self.live_compare_button.pack_forget()
        if self.live_mode_var.get() == "MANUAL_LOOKUP":
            self.live_run_button.pack(fill=tk.X, ipady=8, pady=(0, 8), before=self.live_summary_frame)
            return
        self.live_compare_button.pack(fill=tk.X, ipady=7, pady=(0, 8), before=self.live_summary_frame)

    def _toggle_live_settings(self) -> None:
        if self.live_settings_visible:
            self.live_settings_notebook.pack_forget()
            self.live_settings_button.configure(text="Pokaz Scenario Settings")
            self.live_settings_visible = False
            return
        self.live_settings_notebook.pack(fill=tk.X, pady=(0, 8), after=self.live_settings_button.master)
        self.live_settings_button.configure(text="Ukryj Scenario Settings")
        self.live_settings_visible = True

    def _live_manifest(self) -> dict | None:
        if not LIVE_SCENARIO_MANIFEST.exists():
            return None
        try:
            return json.loads(LIVE_SCENARIO_MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _live_dataset_ready(self) -> bool:
        manifest = self._live_manifest()
        if not manifest or not LIVE_SCENARIO_PROCESSED.exists():
            return False
        if manifest.get("validation_status") != "READY":
            return False
        missing = manifest.get("missing_seasons") or []
        if missing:
            return False
        return int(manifest.get("team_game_observations") or 0) >= 1000

    def _live_dataset_status_text(self) -> str:
        manifest = self._live_manifest()
        if not manifest:
            return (
                "DATASET: NOT READY\n"
                "Run: .\\.venv\\Scripts\\python.exe scripts\\sync_live_scenario_data.py --bootstrap"
            )
        status = "READY" if self._live_dataset_ready() else "FAILED"
        seasons = manifest.get("seasons_present") or []
        season_text = f"{min(seasons)}-{max(seasons)}" if seasons else "UNKNOWN"
        return (
            f"DATASET: {season_text}\n"
            f"{manifest.get('unique_processed_games', 'UNKNOWN')} games | "
            f"{manifest.get('team_game_observations', 'UNKNOWN')} team-game observations\n"
            f"Updated: {manifest.get('build_timestamp_utc', 'UNKNOWN')} | Status: {status}"
        )

    def _update_live_active_summary(self) -> None:
        if not hasattr(self, "live_active_var"):
            return
        if self.live_mode_var.get() == "BASIC_AFTER_Q2":
            self.live_active_var.set(self._basic_after_q2_active_summary())
            return
        team_a = self.live_team_var.get().strip().upper() or "TEAM_A"
        opponent = self.live_opponent_var.get().strip().upper() or "TEAM_B"
        self.live_active_var.set(
            "\n".join(
                [
                    f"{team_a} vs {opponent}",
                    f"Path: {self.live_lookup_path_var.get() or 'UNKNOWN'}",
                    f"Event: {self.live_event_var.get() or 'UNKNOWN'}",
                    f"Sample: {self.live_sample_mode_var.get() or 'UNKNOWN'}",
                    (
                        f"Role/side/spread/phase: {self.live_role_var.get() or 'ANY'} / "
                        f"{self.live_side_var.get() or 'ANY'} / "
                        f"{self.live_spread_bucket_var.get() or 'ANY'} / "
                        f"{self.live_phase_var.get() or 'ANY'}"
                    ),
                ]
            )
        )

    def _parse_live_score_pair(self, raw: str) -> tuple[int, int] | None:
        match = re.match(r"^\s*(-?\d+)\s*[-:]\s*(-?\d+)\s*$", raw or "")
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    def _live_quarter_result(self, team_points: int, opponent_points: int) -> str:
        if team_points > opponent_points:
            return "WIN"
        if team_points < opponent_points:
            return "LOSS"
        return "TIE"

    def _live_cumulative_state(self, margin: int) -> str:
        if margin > 0:
            return "LEAD"
        if margin < 0:
            return "TRAIL"
        return "TIE"

    def _live_margin_bucket(self, margin: int | None) -> str:
        if margin is None:
            return "UNKNOWN"
        if margin == 0:
            return "TIED"
        prefix = "LEADING" if margin > 0 else "TRAILING"
        value = abs(margin)
        if value <= 7:
            return f"{prefix}_1_TO_7"
        if value <= 14:
            return f"{prefix}_8_TO_14"
        return f"{prefix}_15_PLUS"

    def _basic_after_q2_active_summary(self) -> str:
        payload = self.live_basic_payload if isinstance(self.live_basic_payload, dict) else None
        state = payload.get("current_state", {}) if payload else {}
        pregame = payload.get("pregame_spread_context", {}) if payload else {}
        team_a = str(state.get("team_a") or self.live_team_var.get().strip().upper() or "TEAM_A")
        opponent = str(state.get("opponent") or self.live_opponent_var.get().strip().upper() or "TEAM_B")
        q1_text = self.live_q1_var.get().strip() or "MISSING"
        q2_text = self.live_q2_var.get().strip() or "MISSING"
        q3_text = self.live_q3_var.get().strip()
        quarter_path = state.get("team_a_quarter_result_path")
        cumulative_path = state.get("team_a_cumulative_state_path")
        margin = state.get("margin")
        margin_bucket = state.get("margin_bucket")
        team_score = state.get("team_a_score")
        opponent_score = state.get("opponent_score")

        if not quarter_path or not cumulative_path:
            scores = [
                self._parse_live_score_pair(q1_text),
                self._parse_live_score_pair(q2_text),
            ]
            if q3_text:
                scores.append(self._parse_live_score_pair(q3_text))
            if scores and all(score is not None for score in scores):
                team_total = 0
                opponent_total = 0
                quarter_parts = []
                cumulative_parts = []
                for team_points, opp_points in scores:  # type: ignore[misc]
                    team_total += team_points
                    opponent_total += opp_points
                    quarter_parts.append(self._live_quarter_result(team_points, opp_points))
                    cumulative_parts.append(self._live_cumulative_state(team_total - opponent_total))
                quarter_path = "-".join(quarter_parts)
                cumulative_path = "-".join(cumulative_parts)
                team_score = team_total
                opponent_score = opponent_total
                margin = team_total - opponent_total
                margin_bucket = self._live_margin_bucket(margin)

        halftime = "UNKNOWN"
        q1_pair = self._parse_live_score_pair(q1_text)
        q2_pair = self._parse_live_score_pair(q2_text)
        if q1_pair and q2_pair:
            halftime = f"{team_a} {q1_pair[0] + q2_pair[0]}-{q1_pair[1] + q2_pair[1]} {opponent}"
        elif team_score is not None and opponent_score is not None:
            halftime = f"{team_a} {team_score}-{opponent_score} {opponent}"

        spread = pregame.get("team_a_closing_spread")
        active_game = self.live_active_game
        if spread is None and active_game is not None and team_a in {active_game.away, active_game.home}:
            spread = active_game.perspective(team_a).spread
        if spread is None and active_game is None and self.selected_pick_record:
            spread = self.selected_pick_record.get("handicap", self.selected_pick_record.get("line"))
        try:
            numeric_spread = float(spread)
        except (TypeError, ValueError):
            numeric_spread = None
        if pregame.get("team_a_role"):
            derived_role = pregame.get("team_a_role")
        elif numeric_spread is None:
            derived_role = "UNKNOWN"
        elif numeric_spread < 0:
            derived_role = "FAVORITE"
        elif numeric_spread > 0:
            derived_role = "UNDERDOG"
        else:
            derived_role = "PICKEM_OR_UNKNOWN"

        lines = [
            f"{team_a} vs {opponent}",
            f"Q1 score: {q1_text}",
            f"Q2 score: {q2_text}",
            f"Halftime: {halftime}",
            f"Quarter Path: {quarter_path or 'UNKNOWN'}",
            f"Cumulative Path: {cumulative_path or 'UNKNOWN'}",
            f"Margin: {margin if margin is not None else 'UNKNOWN'}",
            f"Margin Bucket: {margin_bucket or 'UNKNOWN'}",
            f"Pregame spread: {spread if spread is not None else 'UNKNOWN'}",
            f"Derived role: {derived_role}",
        ]
        if active_game is not None:
            lines.extend(
                [
                    f"Game date: {active_game.game_date} {active_game.game_time}",
                    f"Neutral: {active_game.neutral_site}",
                    f"Model status: {active_game.model_status}",
                    f"Spread source/status: {active_game.spread_source} / {active_game.spread_status}",
                ]
            )
        return "\n".join(lines)

    def _write_live_raw(self, text: str) -> None:
        if not hasattr(self, "live_raw_text"):
            return
        self.live_raw_text.insert(tk.END, text + "\n")
        self.live_raw_text.see(tk.END)

    def _set_live_summary(self, text: str) -> None:
        self.live_result_var.set(text)
        if not hasattr(self, "live_summary_text"):
            return
        self.live_summary_text.delete("1.0", tk.END)
        self.live_summary_text.insert(tk.END, text)
        self.live_summary_text.see("1.0")

    def _set_forum_post(self, text: str) -> None:
        if not hasattr(self, "live_forum_text"):
            return
        self.live_forum_text.delete("1.0", tk.END)
        self.live_forum_text.insert(tk.END, text)

    def _copy_forum_post(self) -> None:
        if not hasattr(self, "live_forum_text"):
            return
        text = self.live_forum_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Empty forum post", "Najpierw uruchom BASIC AFTER Q2.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.status_var.set("STATUS: FORUM POST copied to clipboard")

    def _spread_bucket(self, spread: float) -> str:
        if spread <= 1.5:
            return "0.5-1.5"
        if spread <= 3:
            return "2-3"
        if spread <= 4.5:
            return "3.5-4.5"
        if spread <= 6:
            return "5-6"
        if spread <= 7:
            return "6.5-7"
        if spread <= 9.5:
            return "7.5-9.5"
        if spread <= 13.5:
            return "10-13.5"
        return "14+"

    def _safe_game_id(self) -> str | None:
        raw = self.game_id_var.get().strip()
        if not raw:
            messagebox.showerror("Missing game id", "Wpisz game_id, np. 2026_w01_SF_at_LA.")
            return None
        safe = re.sub(r"[^A-Za-z0-9_@.-]+", "_", raw).strip("_")
        if not safe:
            messagebox.showerror("Invalid game id", "Nieprawidlowy game_id.")
            return None
        return safe

    def _gpt_folder(self) -> Path | None:
        values = self._validate()
        game_id = self._safe_game_id()
        if values is None or game_id is None:
            return None
        season, week = values
        return REPO_ROOT / "research" / "gpt_snapshots" / str(season) / f"week_{week:02d}" / game_id

    def _save_gpt_snapshot(self) -> None:
        folder = self._gpt_folder()
        if folder is None:
            return
        body = self.gpt_paste_text.get("1.0", tk.END).strip()
        if not body:
            messagebox.showerror("Empty GPT output", "Wklej odpowiedz GPT przed zapisem.")
            return
        values = self._validate()
        if values is None:
            return
        season, week = values
        day = self._effective_day()
        snapshot_type = self.gpt_snapshot_type_var.get()
        run_date = datetime.now().astimezone().date().isoformat()
        if snapshot_type == "full_19_points":
            filename = "full_19_points.md"
        else:
            filename = f"delta_{run_date}_{day}.md"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        if path.exists() and not messagebox.askyesno(
            "Overwrite?",
            f"Plik juz istnieje:\n{path}\n\nNadpisac?",
        ):
            timestamp = datetime.now().strftime("%H%M%S")
            path = folder / f"{path.stem}_{timestamp}{path.suffix}"
        content = "\n".join(
            [
                "# GPT Snapshot",
                "",
                f"season: {season}",
                f"week: {week}",
                f"game_id: {folder.name}",
                f"snapshot_type: {snapshot_type}",
                f"created_at_local: {datetime.now().astimezone().isoformat()}",
                f"source_thread: {self.gpt_source_var.get().strip() or 'GPT'}",
                "",
                "## GPT Output",
                "",
                body,
                "",
            ]
        )
        path.write_text(content, encoding="utf-8")
        self._write_line(f"Saved GPT snapshot: {path}")
        self.gpt_paste_text.delete("1.0", tk.END)
        self.last_report = None

    def _extract_yaml_from_paste(self, text: str) -> str:
        fenced = re.findall(r"```(?:yaml|yml)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        for block in fenced:
            if "book_snapshot:" in block:
                return block.strip()
        return text.strip()

    def _save_book_snapshot_from_paste(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        body = self.gpt_paste_text.get("1.0", tk.END).strip()
        if not body:
            messagebox.showerror("Empty paste", "Wklej YAML book_snapshot do pola GPT Paste.")
            return
        yaml_text = self._extract_yaml_from_paste(body)
        try:
            payload = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            messagebox.showerror("Invalid YAML", f"Nie moge sparsowac YAML:\n{exc}")
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("book_snapshot"), dict):
            messagebox.showerror("Invalid snapshot", "YAML musi miec top-level `book_snapshot`.")
            return
        if not isinstance(payload.get("games"), list):
            messagebox.showerror("Invalid snapshot", "YAML musi miec top-level `games` jako lista.")
            return
        meta = payload["book_snapshot"]
        if int(meta.get("season") or 0) != season or int(meta.get("week") or 0) != week:
            messagebox.showerror(
                "Season/week mismatch",
                f"YAML ma season/week {meta.get('season')}/{meta.get('week')}, a bot ma {season}/{week}.",
            )
            return
        path = REPO_ROOT / "data" / "book_snapshots" / str(season) / f"week_{week:02d}_screen_snapshot.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
        self._write_line(f"Saved book snapshot: {path} ({len(payload['games'])} games)")
        self.status_var.set("STATUS: SAVED - book snapshot")

    def _convert_book_snapshot_to_lines(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        input_path = REPO_ROOT / "data" / "book_snapshots" / str(season) / f"week_{week:02d}_screen_snapshot.yaml"
        output_path = REPO_ROOT / "config" / "lines" / str(season) / f"week{week}_lines.yaml"
        if not input_path.exists():
            messagebox.showerror("Missing snapshot", f"Najpierw zapisz book snapshot:\n{input_path}")
            return
        cmd = [
            str(PYTHON_EXE),
            str(REPO_ROOT / "scripts" / "book_snapshot_to_week_lines.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
        self._set_running(True, "CONVERT SNAPSHOT")
        self.output.delete("1.0", tk.END)
        self._write_line("Running book snapshot conversion")
        self._write_line("Command:")
        self._write_line(" ".join(cmd))
        self._write_line("")
        thread = threading.Thread(
            target=self._run_subprocess,
            args=(cmd,),
            kwargs={"detect_daily_report": False},
            daemon=True,
        )
        thread.start()

    def _open_simulation_file(self) -> None:
        path = REPO_ROOT / "research" / "simulations" / "2026_week1_full_training_simulation.md"
        if not path.exists():
            messagebox.showinfo("Missing simulation", f"Nie znaleziono pliku:\n{path}")
            return
        os.startfile(path)

    def _open_gpt_folder(self) -> None:
        folder = self._gpt_folder()
        if folder is None:
            return
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _generate_gpt_prompt(self) -> None:
        values = self._validate()
        game_id = self.game_id_var.get().strip() or "[GAME_ID]"
        if values is None:
            return
        season, week = values
        day = self._effective_day()
        day_config = self.bot_config.get("days", {}).get(day, {})
        prompt_type = day_config.get("gpt_prompt_type", "delta_refresh")
        snapshot_type = self.gpt_snapshot_type_var.get()
        prompt = self._build_gpt_prompt(
            season=season,
            week=week,
            day=day,
            game_id=game_id,
            prompt_type=prompt_type,
            snapshot_type=snapshot_type,
            objective=day_config.get("objective", ""),
            pick_record=self.selected_pick_record,
        )
        self.gpt_prompt_text.delete("1.0", tk.END)
        self.gpt_prompt_text.insert(tk.END, prompt)

    def _line_context_for_pick(self, pick_record: dict | None) -> dict:
        if not pick_record:
            return {}
        try:
            season = int(pick_record.get("season") or 0)
            week = int(pick_record.get("week") or 0)
        except (TypeError, ValueError):
            return {}
        if not season or not week:
            return {}
        lines_path = REPO_ROOT / "config" / "lines" / str(season) / f"week{week}_lines.yaml"
        if not lines_path.exists():
            return {}
        try:
            payload = yaml.safe_load(lines_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
        away = str(pick_record.get("away") or "").upper()
        home = str(pick_record.get("home") or "").upper()
        for matchup in payload.get("matchups", []):
            if not isinstance(matchup, dict):
                continue
            if str(matchup.get("away") or "").upper() == away and str(matchup.get("home") or "").upper() == home:
                return matchup
        return {}

    def _is_tnf_scope_pick(self, pick_record: dict | None) -> bool:
        context = self._line_context_for_pick(pick_record)
        game_date = str(context.get("source_game_date_local") or "")
        try:
            weekday = datetime.fromisoformat(game_date).weekday()
        except ValueError:
            return bool(pick_record and pick_record.get("prime_time"))
        # Local screenshots can show US Thursday night as Wed/Thu/Fri depending
        # on timezone conventions, so treat early-week non-Sunday games as TNF scope.
        return weekday in {2, 3, 4}

    def _copy_gpt_prompt(self) -> None:
        prompt = self.gpt_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showinfo("No prompt", "Brak promptu do skopiowania.")
            return
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self.status_var.set("STATUS: COPIED - GPT prompt")

    def _copy_book_snapshot_prompt(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        prompt = self._build_book_snapshot_prompt(season=season, week=week)
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self.gpt_prompt_text.delete("1.0", tk.END)
        self.gpt_prompt_text.insert(tk.END, prompt)
        self.status_var.set("STATUS: COPIED - book snapshot prompt")

    def _copy_codex_save_instruction(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        prompt = self._build_codex_save_instruction(season=season, week=week)
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self.gpt_prompt_text.delete("1.0", tk.END)
        self.gpt_prompt_text.insert(tk.END, prompt)
        self.status_var.set("STATUS: COPIED - Codex save instruction")

    def _build_codex_save_instruction(self, *, season: int, week: int) -> str:
        return "\n".join(
            [
                f"Zapisz ponizszy YAML jako book snapshot dla season={season}, week={week}.",
                "",
                "Zadania dla Codex:",
                "1. Sprawdz, czy YAML ma strukture book_snapshot + games.",
                "2. Nie zgaduj brakujacych danych; zostaw UNKNOWN/null, jesli GPT ich nie podal.",
                "3. Popraw tylko format techniczny YAML, typy liczbowe i oczywiste parsing issues z linii typu pk, +1½-118, o44½.",
                "4. Zapisz wynik do:",
                f"   data/book_snapshots/{season}/week_{week:02d}_screen_snapshot.yaml",
                "5. Jesli istnieje skrypt konwersji/walidacji quote snapshotu, uruchom go albo powiedz, czego brakuje.",
                "6. Po zapisie napisz, jaki jest nastepny krok w bocie.",
                "",
                "YAML od GPT:",
                "",
            ]
        )

    def _build_book_snapshot_prompt(self, *, season: int, week: int) -> str:
        return "\n".join(
            [
                "Przerob screeny linii NFL na poprawny YAML book_snapshot.",
                "",
                "Wymagania:",
                "- Nie zgaduj brakujacych danych.",
                "- Jesli book/source nie jest podany, ustaw book: PREGAME_COM.",
                "- Jesli timestamp nie jest podany, ustaw captured_at_utc: UNKNOWN.",
                f"- Zachowaj season: {season} i week: {week}.",
                "- Druzyny zapisuj kodami NFL: SF, LA, NE, SEA itd.",
                "- Spread zapisuj liczbowo z perspektywy kazdej druzyny.",
                "- Jesli spread/total ma cene przy sobie, rozdziel value i price.",
                "- Jesli cena nie jest pokazana, uzyj -110.",
                "- Jesli widzisz rozjazd typu jedna strona pk, druga +1.5, oznacz game_line_quality: INCONSISTENT_DISPLAY i dodaj note.",
                "- Nie tworz finalnych pickow.",
                "- Zwroc tylko YAML.",
                "",
                "Format:",
                "",
                "book_snapshot:",
                "  book: PREGAME_COM",
                f"  season: {season}",
                f"  week: {week}",
                "  captured_at_utc: UNKNOWN",
                "  executable_status: displayed_unverified",
                "  target_stake: 100",
                "  house_rules_checked: false",
                "",
                "games:",
                "  - game_date_local:",
                "    game_time_local:",
                "    away:",
                "    home:",
                "    away_moneyline:",
                "    home_moneyline:",
                "    away_spread:",
                "    away_spread_price:",
                "    home_spread:",
                "    home_spread_price:",
                "    total_over:",
                "    total_over_price:",
                "    total_under:",
                "    total_under_price:",
                "    game_line_quality:",
                "    notes:",
            ]
        )

    def _build_gpt_prompt(
        self,
        *,
        season: int,
        week: int,
        day: str,
        game_id: str,
        prompt_type: str,
        snapshot_type: str,
        objective: str,
        pick_record: dict | None,
    ) -> str:
        pick = pick_record or {}
        away = str(pick.get("away") or "[AWAY]").upper()
        home = str(pick.get("home") or "[HOME]").upper()
        selected_team = str(pick.get("model_winner") or "[SELECTED_TEAM]").upper()
        tag = str(pick.get("tag") or "[TAG]").upper()
        spread = pick.get("handicap", pick.get("line", "[CURRENT_SPREAD]"))
        price = pick.get("price", "[CURRENT_PRICE]")
        book = pick.get("book") or pick.get("odds_source") or "[BOOK_SOURCE]"
        quote_ts = pick.get("decision_ts_utc") or "[QUOTE_TIMESTAMP_OR_UNKNOWN]"
        edge = pick.get("edge_vs_line", "[EDGE]")
        model_margin = pick.get("model_margin", "[MODEL_MARGIN]")
        market_margin = pick.get("market_margin", "[MARKET_MARGIN]")
        total = pick.get("total", "[TOTAL]")
        neutral_site = pick.get("neutral_site", "[NEUTRAL_SITE]")
        current_spread = f"{selected_team} {spread}" if spread != "[CURRENT_SPREAD]" else str(spread)
        if str(prompt_type).startswith("delta_tnf") and pick_record and not self._is_tnf_scope_pick(pick_record):
            return "\n".join(
                [
                    "Sroda - TNF delta refresh.",
                    "",
                    "Status:",
                    f"- Aktualnie zaznaczony pick: {game_id}",
                    "- Ten pick nie jest w zakresie TNF / early-week games.",
                    "- Nie wysylaj tego promptu do GPT dla zaznaczonego meczu.",
                    "",
                    "Co robic:",
                    "1. Jesli TNF nie ma na liscie VP/GOW/GOM/GOY, sroda nie wymaga GPT delta refresh.",
                    "2. Kliknij Execute, zeby zapisac raport dnia.",
                    "3. Przejdz do czwartku, gdy bedziemy robic final TNF + zrzuty Sunday/MNF.",
                ]
            )
        if prompt_type == "full_19_points" or snapshot_type == "full_19_points":
            return "\n".join(
                [
                    "Uzyj zalaczonego pliku docs/variant_b_final_gpt_research_prompt.md jako glownej instrukcji dla frameworka Variant B.",
                    "",
                    "Mecz do analizy:",
                    f"- Season: {season}",
                    f"- Week: {week}",
                    f"- Game ID: {game_id}",
                    f"- Away: {away}",
                    f"- Home: {home}",
                    "- Market: full-game spread",
                    f"- Selected team: {selected_team}",
                    f"- Current spread: {current_spread}",
                    f"- Current price: {price}",
                    f"- Book/source: {book}",
                    f"- Quote timestamp UTC: {quote_ts}",
                    f"- Model tag: {tag}",
                    f"- Model edge_vs_line: {edge}",
                    f"- Model margin: {model_margin}",
                    f"- Market margin: {market_margin}",
                    f"- Total: {total}",
                    f"- Neutral site: {neutral_site}",
                    "- Venue: znajdz i potwierdz zrodlem",
                    "- Date: znajdz i potwierdz zrodlem",
                    "",
                    "Uwaga metodologiczna:",
                    "Dane Selected team / spread / price / book pochodza z naszego modelowego pick file albo manualnego quote snapshotu.",
                    "Jesli book/source nie jest market-grade albo timestamp/executable status jest slaby, oznacz to jako ograniczenie procesu.",
                    "",
                    "Zadanie:",
                    "Zwroc pelny wynik w strukturze Variant B: audit_metadata, points 1-19 oraz final_summary.",
                    "Nie dawaj finalnego picka. Oznacz braki jako MISSING / UNKNOWN / PENDING_NOT_DUE.",
                    "Nie rekonstruuj brakujacych quote i nie nazywaj ruchu sharp/public bez zrodla.",
                    "Dla kazdego istotnego twierdzenia podaj zrodlo.",
                ]
            )
        scope_lines = self._prompt_scope_lines(prompt_type)
        return "\n".join(
            [
                "Zrob delta refresh dla istniejacego audytu Variant B.",
                "",
                "Kontekst:",
                f"- Season: {season}",
                f"- Week: {week}",
                f"- Game ID: {game_id}",
                f"- Away: {away}",
                f"- Home: {home}",
                f"- Selected team: {selected_team}",
                f"- Current spread: {current_spread}",
                f"- Current price: {price}",
                f"- Book/source: {book}",
                f"- Quote timestamp UTC: {quote_ts}",
                f"- Model tag: {tag}",
                f"- Model edge_vs_line: {edge}",
                f"- Day: {day}",
                f"- Prompt type: {prompt_type}",
                f"- Objective: {objective}",
                "",
                *scope_lines,
                "",
                "Sprawdz tylko zmiany od poprzedniego snapshotu:",
                "- quote / line movement",
                "- injury report / inactives, jesli due",
                "- roster moves",
                "- weather / venue",
                "- schedule spot",
                "- matchup_specific_risk",
                "- game_script_risk",
                "",
                "Zwroc:",
                "1. co sie zmienilo",
                "2. co pozostaje bez zmian",
                "3. jakie pola Variant B trzeba zaktualizowac",
                "4. missing_data / pending_not_due",
                "5. czy status powinien byc WATCH / HOLD / READY_FOR_FINAL_CHECK / NO_BET_REVIEW",
                "",
                "Nie licz finalnego EV i nie rekonstruuj brakujacych quote.",
            ]
        )

    def _prompt_scope_lines(self, prompt_type: str) -> list[str]:
        scopes = {
            "delta_tnf": [
                "Zakres dnia: SRODA / TNF DELTA",
                "- skup sie na meczu czwartkowym, jesli jest kandydatem VP/GOW/GOM/GOY",
                "- sprawdz zmiany quote / line movement od wtorku",
                "- sprawdz injury report, roster moves, weather, venue i travel",
                "- nie analizuj pelnych 19 punktow od nowa",
            ],
            "final_tnf_plus_sunday_mnf_delta": [
                "Zakres dnia: CZWARTEK / FINAL TNF + SUNDAY/MNF DELTA",
                "- dla TNF zrob final/pre-kickoff delta check",
                "- dla Sunday/MNF zrob tylko swiezy zrzut zmian, jesli sa kandydatami",
                "- rozdziel TNF final check od Sunday/MNF watchlist",
                "- zwroc late blockers: inactives, quote, weather, no-chase, stale info",
            ],
            "sunday_mnf_delta": [
                "Zakres dnia: PIATEK / SUNDAY-MNF REFRESH",
                "- skup sie na niedzielnych i poniedzialkowych kandydatach",
                "- sprawdz injury reports, roster moves, market movement, weather",
                "- oznacz co wymaga sobotniego albo niedzielnego final checku",
            ],
            "prefinal_sunday_mnf_delta": [
                "Zakres dnia: SOBOTA / PRE-FINAL SUNDAY-MNF",
                "- przygotuj liste brakow przed niedziela",
                "- sprawdz key number movement, no-chase risk, late injury/weather/roster updates",
                "- oznacz READY_FOR_SUNDAY_CHECK / READY_FOR_MNF_CHECK / WATCH / HOLD",
            ],
            "final_sunday_plus_mnf_delta": [
                "Zakres dnia: NIEDZIELA / FINAL SUNDAY + MNF DELTA",
                "- dla niedzielnych kandydatow zrob final pre-kickoff delta check",
                "- sprawdz final inactives, quote, no-chase, weather i late news",
                "- dla MNF zrob oddzielny zrzut delta, nie final unless due",
                "- nie mieszaj live tracking z pregame tracking",
            ],
            "final_delta_mnf": [
                "Zakres dnia: PONIEDZIALEK / FINAL MNF",
                "- skup sie tylko na MNF, jesli jest kandydatem",
                "- sprawdz final quote, inactives, weather, late news i no-chase",
                "- zwroc czy pozostaje READY / WATCH / HOLD / NO_BET_REVIEW",
            ],
        }
        return scopes.get(
            prompt_type,
            [
                "Zakres dnia: DELTA REFRESH",
                "- sprawdz tylko zmiany od poprzedniego snapshotu",
            ],
        )

    def _build_command(self, execute: bool) -> list[str] | None:
        return self._build_command_for_day(execute=execute, day=self.day_var.get())

    def _build_command_for_day(self, *, execute: bool, day: str) -> list[str] | None:
        values = self._validate()
        if values is None:
            return None
        season, week = values
        cmd = [str(PYTHON_EXE), str(BOT_SCRIPT), "--season", str(season), "--week", str(week)]
        if day != "auto":
            cmd.extend(["--day", day])
        if execute:
            cmd.append("--execute")
        return cmd

    def _confirm_execute(self) -> None:
        ok = messagebox.askyesno(
            "Confirm execute",
            "Execute odpali komendy z harmonogramu dla wybranego dnia. Kontynuowac?",
        )
        if ok:
            self._run_bot(True)

    def _run_bot(self, execute: bool) -> None:
        cmd = self._build_command(execute)
        if not cmd:
            return
        self._set_running(True, f"{'EXECUTE' if execute else 'DRY RUN'}")
        self.output.delete("1.0", tk.END)
        self._write_line(f"Running mode: {'EXECUTE' if execute else 'DRY_RUN'}")
        self._write_line("Command:")
        self._write_line(" ".join(cmd))
        self._write_line("")
        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
        thread.start()

    def _run_week_dry_run(self) -> None:
        commands = [
            self._build_command_for_day(execute=False, day=day)
            for day in WEEK_TEST_DAYS
        ]
        if any(command is None for command in commands):
            return
        self._set_running(True, "WEEK DRY RUN")
        self.output.delete("1.0", tk.END)
        self._write_line("Running mode: WEEK DRY RUN Tue-Mon")
        self._write_line("Week 1 note: Tuesday previous-week tasks should be SKIPPED.")
        self._write_line("")
        thread = threading.Thread(
            target=self._run_subprocess_sequence,
            args=([command for command in commands if command is not None],),
            daemon=True,
        )
        thread.start()

    def _run_subprocess_sequence(self, commands: list[list[str]]) -> None:
        started = datetime.now()
        chunks = []
        returncode = 0
        try:
            for day, cmd in zip(WEEK_TEST_DAYS, commands):
                header = f"=== {day.upper()} ==="
                command_text = " ".join(cmd)
                chunks.append(header)
                chunks.append("Command:")
                chunks.append(command_text)
                result = subprocess.run(
                    cmd,
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                output = "\n".join(part for part in [result.stdout, result.stderr] if part).rstrip()
                if output:
                    chunks.append(output)
                exit_line = f"Exit code: {result.returncode}"
                chunks.append(exit_line)
                chunks.append("")
                if result.returncode != 0 and returncode == 0:
                    returncode = result.returncode
        except Exception as exc:
            returncode = 1
            chunks.append(f"ERROR: {type(exc).__name__}: {exc}")
        elapsed = (datetime.now() - started).total_seconds()
        self.after(
            0,
            lambda: self._finish_week_dry_run("\n".join(chunks), elapsed, returncode),
        )

    def _finish_week_dry_run(self, output: str, elapsed: float, returncode: int) -> None:
        if output.strip():
            self._write_line(output)
        self._write_line(f"Week dry run elapsed: {elapsed:.1f}s")
        self._write_line(f"Week dry run exit code: {returncode}")
        self.last_report = self._detect_last_report()
        if self.last_report:
            self._write_line(f"Last report: {self.last_report}")
        self._finish_status(returncode, elapsed)
        self._set_running(False)

    def _live_base_command(self) -> list[str] | None:
        try:
            start_season = int(self.live_start_season_var.get())
            end_season = int(self.live_end_season_var.get())
        except ValueError:
            messagebox.showerror("Invalid live input", "Live start/end season musza byc liczbami.")
            return None
        if start_season <= 0 or end_season < start_season:
            messagebox.showerror("Invalid live input", "Live season range jest nieprawidlowy.")
            return None

        cmd = [
            str(PYTHON_EXE),
            str(LIVE_SCENARIO_SCRIPT),
            "--start-season",
            str(start_season),
            "--end-season",
            str(end_season),
            "--sample-mode",
            self.live_sample_mode_var.get(),
        ]
        optional_args = [
            ("--team", self.live_team_var.get().strip().upper()),
            ("--opponent", self.live_opponent_var.get().strip().upper()),
            ("--role", self.live_role_var.get().strip()),
            ("--side", self.live_side_var.get().strip()),
            ("--spread-bucket", self.live_spread_bucket_var.get().strip()),
            ("--season-phase", self.live_phase_var.get().strip()),
        ]
        for flag, value in optional_args:
            if value:
                cmd.extend([flag, value])
        return cmd

    def _run_live_scenario(self, *, rebuild_only: bool) -> None:
        self.live_mode_var.set("MANUAL_LOOKUP")
        if hasattr(self, "live_settings_notebook"):
            self.live_settings_notebook.select(self.live_manual_tab)
        cmd = self._live_base_command()
        if cmd is None:
            return
        if not rebuild_only:
            lookup_path = self.live_lookup_path_var.get().strip().upper()
            if not lookup_path:
                messagebox.showerror("Missing live path", "Wybierz path, np. WIN albo WIN-LOSS.")
                return
            cmd.extend(
                [
                    "--lookup-path",
                    lookup_path,
                    "--event",
                    self.live_event_var.get(),
                    "--settlement",
                    self.live_settlement_var.get(),
                ]
            )
            live_decimal = self.live_decimal_var.get().strip()
            live_ml = self.live_ml_var.get().strip()
            if live_decimal:
                cmd.extend(["--live-decimal", live_decimal])
            elif live_ml:
                cmd.extend(["--live-ml", live_ml])

        self._set_running(True, f"LIVE {'REBUILD' if rebuild_only else 'LOOKUP'}")
        self.live_status_var.set("RUNNING REBUILD" if rebuild_only else "RUNNING LOOKUP")
        self._update_live_active_summary()
        if not rebuild_only:
            self._set_live_summary("LIVE LOOKUP running... czekam na wynik historyczny.")
        self.live_raw_text.delete("1.0", tk.END)
        self._write_live_raw(f"Running live scenario: {'REBUILD' if rebuild_only else 'LOOKUP'}")
        self._write_live_raw("Command:")
        self._write_live_raw(" ".join(cmd))
        self._write_live_raw("")
        thread = threading.Thread(
            target=self._run_subprocess,
            args=(cmd,),
            kwargs={"detect_daily_report": False},
            daemon=True,
        )
        thread.start()

    def _mirror_live_path(self, path: str) -> str:
        swap = {"WIN": "LOSS", "LOSS": "WIN", "TIE": "TIE"}
        parts = [part.strip().upper() for part in path.replace(">", "-").split("-") if part.strip()]
        return "-".join(swap.get(part, part) for part in parts) if parts else "START"

    def _team_history_command(self, *, team: str, path: str, output_dir: Path) -> list[str] | None:
        try:
            start_season = int(self.live_start_season_var.get())
            end_season = int(self.live_end_season_var.get())
        except ValueError:
            messagebox.showerror("Invalid live input", "Live start/end season musza byc liczbami.")
            return None
        if start_season <= 0 or end_season < start_season:
            messagebox.showerror("Invalid live input", "Live season range jest nieprawidlowy.")
            return None
        return [
            str(PYTHON_EXE),
            str(LIVE_SCENARIO_SCRIPT),
            "--start-season",
            str(start_season),
            "--end-season",
            str(end_season),
            "--sample-mode",
            "TEAM_A_HISTORY",
            "--team",
            team,
            "--lookup-path",
            path,
            "--event",
            "TEAM_A_WIN_FINAL",
            "--settlement",
            self.live_settlement_var.get(),
            "--output-dir",
            str(output_dir),
        ]

    def _run_team_history_compare(self) -> None:
        self.live_mode_var.set("BASIC_AFTER_Q2")
        if hasattr(self, "live_settings_notebook"):
            self.live_settings_notebook.select(self.live_basic_tab)
        if not self._live_dataset_ready():
            cmd = ".\\.venv\\Scripts\\python.exe scripts\\sync_live_scenario_data.py --bootstrap"
            messagebox.showerror(
                "DATASET NOT READY",
                "Live Scenario processed dataset nie jest gotowy.\n\n"
                f"Uruchom:\n{cmd}",
            )
            self.live_status_var.set("DATASET NOT READY")
            self._set_live_summary(f"DATASET NOT READY\nRun: {cmd}")
            self.live_dataset_status_var.set(self._live_dataset_status_text())
            return
        team_a = self.live_team_var.get().strip().upper()
        team_b = self.live_opponent_var.get().strip().upper()
        if not team_a or not team_b:
            messagebox.showerror("Missing teams", "Podaj Team A i Opponent.")
            return
        try:
            start_season = int(self.live_start_season_var.get())
            end_season = int(self.live_end_season_var.get())
        except ValueError:
            messagebox.showerror("Invalid live input", "Live start/end season musza byc liczbami.")
            return
        q1 = self.live_q1_var.get().strip()
        q2 = self.live_q2_var.get().strip()
        q3 = self.live_q3_var.get().strip()
        if not q1 or not q2:
            messagebox.showerror("Missing quarter scores", "RUN BASIC AFTER Q2 wymaga Q1 i Q2, np. 7-3.")
            return

        output_path = (
            REPO_ROOT
            / "research"
            / "live_scenario_v2"
            / "gui"
            / f"{start_season}_{end_season}_{team_a}_vs_{team_b}_after_q{3 if q3 else 2}.json"
        )
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        cmd = [
            str(PYTHON_EXE),
            str(LIVE_SCENARIO_V2_SCRIPT),
            "--team-a",
            team_a,
            "--opponent",
            team_b,
            "--q1",
            q1,
            "--q2",
            q2,
            "--data-root",
            str(REPO_ROOT / "data"),
            "--data-cutoff-utc",
            generated_at,
            "--generated-at-utc",
            generated_at,
            "--tie-policy",
            "TIE_AS_PUSH" if self.live_settlement_var.get() == "TIE_IS_PUSH" else "TIE_AS_LOSS",
            "--output",
            str(output_path),
        ]
        if q3:
            cmd.extend(["--q3", q3])
        active_game = self.live_active_game
        if active_game is not None and team_a in {active_game.away, active_game.home}:
            perspective_spread = active_game.perspective(team_a).spread
            if perspective_spread is not None:
                cmd.extend(
                    [
                        "--team-a-closing-spread",
                        str(perspective_spread),
                        "--spread-source",
                        active_game.spread_source,
                        "--spread-quality",
                        active_game.spread_status,
                    ]
                )
                if active_game.schedule_timestamp_utc:
                    cmd.extend(["--spread-captured-at-utc", active_game.schedule_timestamp_utc])
        live_decimal = self.live_decimal_var.get().strip()
        if live_decimal:
            cmd.extend(["--team-a-live-decimal", live_decimal])

        self._set_running(True, "LIVE BASIC AFTER Q2")
        self.live_status_var.set("RUNNING BASIC AFTER Q2")
        self.live_basic_payload = None
        self._update_live_active_summary()
        self._set_forum_post("")
        self._set_live_summary(f"Running Live Scenario V2: {team_a} vs {team_b}.")
        self.live_raw_text.delete("1.0", tk.END)
        self.live_calculations_text.delete("1.0", tk.END)
        self._write_live_raw("Running Live Scenario V2 basic after Q2")
        self._write_live_raw("Quarter scores are converted to path/margin by V2.")
        self._write_live_raw("Legacy RUN LIVE LOOKUP remains available as fallback.")
        self._write_live_raw(f"Dataset: {LIVE_SCENARIO_PROCESSED}")
        self._write_live_raw("V2 command:")
        self._write_live_raw(" ".join(cmd))
        self._write_live_raw("")

        thread = threading.Thread(
            target=self._run_live_scenario_v2_worker,
            args=([], cmd, LIVE_SCENARIO_PROCESSED),
            daemon=True,
        )
        thread.start()

    def _run_live_scenario_v2_worker(
        self,
        ensure_cmd: list[str],
        cmd: list[str],
        historical_rows: Path,
    ) -> None:
        started = datetime.now()
        chunks = []
        returncode = 0
        if not historical_rows.exists():
            if ensure_cmd:
                ensure = subprocess.run(
                    ensure_cmd,
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                ensure_output = "\n".join(part for part in [ensure.stdout, ensure.stderr] if part)
                chunks.append(f"===== BUILD LEAGUE-WIDE HISTORY =====\n{ensure_output}")
                if ensure.returncode != 0:
                    returncode = ensure.returncode
            else:
                chunks.append(f"Processed dataset missing: {historical_rows}")
                returncode = 1
        payload = None
        if returncode == 0:
            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            combined = "\n".join(part for part in [result.stdout, result.stderr] if part)
            chunks.append(f"===== LIVE SCENARIO V2 =====\n{combined}")
            returncode = result.returncode
            payload = self._extract_json_payload(combined)
        elapsed = (datetime.now() - started).total_seconds()
        self.after(
            0,
            lambda: self._finish_live_scenario_v2(
                "\n\n".join(chunks),
                payload,
                elapsed,
                returncode,
            ),
        )

    def _finish_live_scenario_v2(
        self,
        output: str,
        payload: dict | None,
        elapsed: float,
        returncode: int,
    ) -> None:
        if output.strip():
            self._write_live_raw(output.rstrip())
        self._write_live_raw("")
        self._write_live_raw(f"Elapsed: {elapsed:.1f}s")
        self._write_live_raw(f"Exit code: {returncode}")

        self.live_basic_payload = payload if isinstance(payload, dict) else None
        self._update_live_active_summary()
        summary = self._format_live_scenario_v2_report(payload)
        forum_post = build_forum_post(payload, language="pl") if isinstance(payload, dict) else ""
        self._set_forum_post(forum_post)
        self._set_live_summary(summary)
        self.live_calculations_text.delete("1.0", tk.END)
        self.live_calculations_text.insert(tk.END, summary)
        self.live_calculations_text.insert(tk.END, "\n\nJSON payload:\n")
        self.live_calculations_text.insert(tk.END, json.dumps(payload or {}, indent=2, ensure_ascii=False))

        if returncode == 0:
            self.live_status_var.set("DONE - BASIC AFTER Q2")
            self.status_var.set(f"STATUS: DONE - {self.run_label} after {elapsed:.1f}s")
            self._write_live_raw(f"FINISHED OK: {self.run_label} after {elapsed:.1f}s")
        else:
            self.live_status_var.set("FAILED - BASIC AFTER Q2")
            self.status_var.set(f"STATUS: FAILED - {self.run_label} after {elapsed:.1f}s")
            self._write_live_raw(f"FINISHED WITH ERRORS: {self.run_label} after {elapsed:.1f}s")
        self._set_running(False)

    def _format_live_scenario_v2_report(self, payload: dict | None) -> str:
        if not payload:
            return "BASIC AFTER Q2 V2 failed: no JSON payload was returned."
        state = payload.get("current_state", {})
        league = payload.get("league_baseline", {})
        broad_game_state = payload.get("broad_league_game_state_baseline", {})
        quarter_context = payload.get("quarter_path_context", {})
        exact_combined = payload.get("exact_combined_match", {})
        play_events = payload.get("play_level_events", {})
        team = payload.get("team_a_history", {})
        opponent = payload.get("opponent_recovery_history", {})
        market = payload.get("market_comparison", {})
        reliability = payload.get("sample_and_reliability", {})
        stability = payload.get("historical_window_stability", {})
        forum = payload.get("forum_content_summary", {})
        warnings = payload.get("warnings", [])
        spread_context_lines = self._format_spread_context_levels(payload)
        return "\n".join(
            [
                "BASIC AFTER Q2 - V2",
                (
                    f"{state.get('team_a', 'TEAM_A')} {state.get('team_a_score', '?')}-"
                    f"{state.get('opponent_score', '?')} {state.get('opponent', 'OPP')}"
                ),
                (
                    "Quarter path: "
                    f"{state.get('team_a_quarter_result_path') or state.get('team_a_path')} | "
                    f"Opp: {state.get('opponent_quarter_result_path') or state.get('opponent_path')}"
                ),
                (
                    "Cumulative path: "
                    f"{state.get('team_a_cumulative_state_path', 'UNKNOWN')} | "
                    f"Opp: {state.get('opponent_cumulative_state_path', 'UNKNOWN')}"
                ),
                f"Margin: {state.get('margin')} | Bucket: {state.get('margin_bucket')}",
                "",
                "A. BROAD LEAGUE GAME-STATE BASELINE",
                (
                    f"Sample: {broad_game_state.get('sample_size', league.get('sample_size'))} | "
                    f"Quality: {broad_game_state.get('sample_quality', league.get('sample_quality'))} | "
                    "Raw final win: "
                    f"{self._fmt_pct(broad_game_state.get('raw_probability', league.get('raw_probability')))}"
                ),
                "",
                "B. SPREAD-CONDITIONED GAME-STATE BASELINE",
                *spread_context_lines,
                "",
                "C. QUARTER-PATH CONTEXT",
                (
                    f"Sample: {quarter_context.get('sample_size')} | "
                    f"Quality: {quarter_context.get('sample_quality')} | "
                    f"Raw final win: {self._fmt_pct(quarter_context.get('raw_probability'))}"
                ),
                "",
                "D. EXACT COMBINED MATCH",
                (
                    f"Sample: {exact_combined.get('sample_size')} | "
                    f"Quality: {exact_combined.get('sample_quality')} | "
                    f"Raw final win: {self._fmt_pct(exact_combined.get('raw_probability'))}"
                ),
                (
                    "Window stability: "
                    f"{stability.get('status', 'UNKNOWN')} | "
                    f"Max diff: {stability.get('max_difference_pp', 'UNKNOWN')} pp"
                ),
                "",
                "E. TEAM A HISTORY",
                (
                    f"Sample: {team.get('sample_size')} | Quality: {team.get('sample_quality')} | "
                    f"Raw: {self._fmt_pct(team.get('raw_probability'))} "
                    f"({team.get('raw_delta_vs_league_pp')} pp) | "
                    f"Adjusted: {self._fmt_pct(team.get('adjusted_probability'))} "
                    f"({team.get('adjusted_delta_vs_league_pp')} pp)"
                ),
                "",
                "F. OPPONENT RECOVERY HISTORY",
                (
                    f"Sample: {opponent.get('sample_size')} | Quality: {opponent.get('sample_quality')} | "
                    f"Raw: {self._fmt_pct(opponent.get('raw_probability'))} "
                    f"({opponent.get('raw_delta_vs_opponent_league_pp', opponent.get('raw_delta_vs_league_pp'))} pp) | "
                    f"Adjusted: {self._fmt_pct(opponent.get('adjusted_probability'))} "
                    f"({opponent.get('adjusted_delta_vs_opponent_league_pp', opponent.get('adjusted_delta_vs_league_pp'))} pp)"
                ),
                "",
                "G. PLAY-LEVEL EVENTS",
                (
                    f"Eligible: {play_events.get('eligible_sample')} | "
                    f"Excluded: {play_events.get('excluded_sample')} | "
                    f"Reasons: {play_events.get('reason_for_exclusions')}"
                ),
                "",
                "MARKET COMPARISON",
                (
                    f"Tie policy: {market.get('tie_policy')} | "
                    f"Historical break-even: {self._fmt_decimal(market.get('historical_break_even_price'))}"
                ),
                (
                    f"Edge vs market: {market.get('edge_vs_market_pp')} pp | "
                    f"Estimated EV: {self._fmt_pct(market.get('estimated_ev'))}"
                ),
                "",
                "SAMPLE LEVELS",
                f"Exact: {reliability.get('exact_filtered_match', {}).get('sample_size')}",
                f"Expanded team: {reliability.get('expanded_team_match', {}).get('sample_size')}",
                f"Contextual league: {reliability.get('contextual_league_match', {}).get('sample_size')}",
                f"Broad league: {reliability.get('broad_league_baseline', {}).get('sample_size')}",
                "",
                "FORUM SUMMARY",
                (
                    f"Broad: {self._fmt_pct(forum.get('broad_final_win_probability'))} "
                    f"(n={forum.get('broad_sample_size')})"
                ),
                (
                    "Spread-conditioned: "
                    f"{self._fmt_pct(forum.get('spread_conditioned_final_win_probability'))} "
                    f"(n={forum.get('spread_conditioned_sample_size')}, "
                    f"{forum.get('spread_conditioned_level', 'UNKNOWN')})"
                ),
                f"Diff vs broad: {forum.get('difference_vs_broad_pp', 'UNKNOWN')} pp",
                f"Forum warning: {forum.get('warning', 'UNKNOWN')}",
                "",
                "WARNINGS",
                *[str(warning) for warning in warnings],
            ]
        )

    def _format_spread_context_levels(self, payload: dict) -> list[str]:
        reliability = payload.get("sample_and_reliability", {})
        levels = reliability.get("spread_filter_levels", {})
        selected = payload.get("spread_conditioned_game_state_baseline", {})
        if not isinstance(levels, dict):
            return [
                (
                    f"Sample: {selected.get('sample_size')} | "
                    f"Quality: {selected.get('sample_quality')} | "
                    f"Raw final win: {self._fmt_pct(selected.get('raw_probability'))}"
                )
            ]

        ordered = [
            ("exact_spread_match", "Exact spread match"),
            ("spread_bucket_match", "Spread bucket match"),
            ("role_only_match", "Role-only match"),
            ("no_spread_baseline", "No-spread baseline"),
        ]
        exact = levels.get("exact_spread_match", {})
        lines: list[str] = []
        if int(exact.get("sample_size") or 0) == 0:
            lines.append("No exact spread-context matches found.")
            missing = exact.get("missing_columns") or []
            if missing:
                lines.append(f"Exact unavailable because missing: {', '.join(map(str, missing))}.")
        selected_level = selected.get("selected_level")
        if selected_level:
            lines.append(f"Selected displayed level: {selected_level}.")
        for key, label in ordered:
            node = levels.get(key, {})
            if not isinstance(node, dict):
                continue
            lines.append(
                (
                    f"- {label}: sample {node.get('sample_size', 'UNKNOWN')} | "
                    f"quality {node.get('sample_quality', 'UNKNOWN')} | "
                    f"raw final win {self._fmt_pct(node.get('raw_probability'))}"
                )
            )
        return lines

    def _format_team_history_compare(
        self,
        payloads: dict[str, dict | None],
        team_a: str,
        team_b: str,
        path_a: str,
        path_b: str,
    ) -> str:
        def block(team: str, path: str) -> list[str]:
            payload = payloads.get(team) or {}
            sample = payload.get("sample_size", "UNKNOWN")
            quality = payload.get("sample_quality", "UNKNOWN")
            node = self._load_live_lookup_node_from_output(team, path)
            q3 = (node or {}).get("next_quarter_distribution", {})
            return [
                f"{team} history after {path}",
                f"Sample: {sample} | Quality: {quality}",
                (
                    "Q3 win/loss/tie: "
                    f"{self._fmt_pct(q3.get('win_probability'))} / "
                    f"{self._fmt_pct(q3.get('loss_probability'))} / "
                    f"{self._fmt_pct(q3.get('tie_probability'))}"
                ),
                (
                    "Final win/loss/tie: "
                    f"{self._fmt_pct(payload.get('win_probability'))} / "
                    f"{self._fmt_pct(payload.get('loss_probability'))} / "
                    f"{self._fmt_pct(payload.get('tie_probability'))}"
                ),
                f"Fair decimal: {self._fmt_decimal(payload.get('fair_decimal'))}",
            ]

        lines = [
            "BASIC AFTER Q2",
            "Uses each team's own history. Pregame spread/role/side/phase filters are ignored.",
            "",
            *block(team_a, path_a),
            "",
            *block(team_b, path_b),
        ]
        qualities = {
            str((payloads.get(team_a) or {}).get("sample_quality", "")).upper(),
            str((payloads.get(team_b) or {}).get("sample_quality", "")).upper(),
        }
        if qualities & {"NO_DATA", "VERY_LOW", "LOW"}:
            lines.append("")
            lines.append("WARNING: one or both samples are small; use as context, not standalone signal.")
        return "\n".join(lines)

    def _load_live_lookup_node_from_output(self, team: str, path: str) -> dict | None:
        try:
            start_season = int(self.live_start_season_var.get())
            end_season = int(self.live_end_season_var.get())
        except ValueError:
            return None
        team_a = self.live_team_var.get().strip().upper()
        team_b = self.live_opponent_var.get().strip().upper()
        base_dir = (
            REPO_ROOT
            / "research"
            / "live_quarter_scenario_matrix"
            / "gui_team_history_compare"
            / f"{start_season}_{end_season}_{team_a}_vs_{team_b}_{self.live_lookup_path_var.get().strip().upper()}"
            / team
        )
        lookup_path = base_dir / "scenario_lookup.json"
        if not lookup_path.exists():
            return None
        try:
            payload = json.loads(lookup_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        node = payload.get(path)
        return node if isinstance(node, dict) else None

    def _run_subprocess(self, cmd: list[str], *, detect_daily_report: bool = True) -> None:
        started = datetime.now()
        try:
            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        except Exception as exc:
            error = str(exc)
            self.after(0, lambda: self._finish_run(f"ERROR: {error}", None, 1, detect_daily_report))
            return
        elapsed = (datetime.now() - started).total_seconds()
        combined = "\n".join(part for part in [result.stdout, result.stderr] if part)
        self.after(
            0,
            lambda: self._finish_run(combined, elapsed, result.returncode, detect_daily_report),
        )

    def _finish_run(
        self,
        output: str,
        elapsed: float | None,
        returncode: int,
        detect_daily_report: bool = True,
    ) -> None:
        if not detect_daily_report and self.run_label.startswith("LIVE"):
            if output.strip():
                self._write_live_raw(output.rstrip())
            if elapsed is not None:
                self._write_live_raw("")
                self._write_live_raw(f"Elapsed: {elapsed:.1f}s")
            self._write_live_raw(f"Exit code: {returncode}")
            if "LIVE LOOKUP" in self.run_label and returncode == 0:
                self._update_live_result_panel(output)
            elif returncode == 0:
                self.live_status_var.set("DONE - REBUILD")
            else:
                self.live_status_var.set("FAILED")
            elapsed_text = f" after {elapsed:.1f}s" if elapsed is not None else ""
            if returncode == 0:
                self.status_var.set(f"STATUS: DONE - {self.run_label}{elapsed_text}")
                self._write_live_raw(f"FINISHED OK: {self.run_label}{elapsed_text}")
            else:
                self.status_var.set(f"STATUS: FAILED - {self.run_label}{elapsed_text}")
                self._write_live_raw(f"FINISHED WITH ERRORS: {self.run_label}{elapsed_text}")
            self._set_running(False)
            return
        if output.strip():
            self._write_line(output.rstrip())
        if elapsed is not None:
            self._write_line("")
            self._write_line(f"Elapsed: {elapsed:.1f}s")
        self._write_line(f"Exit code: {returncode}")
        if not detect_daily_report and "LIVE LOOKUP" in self.run_label and returncode == 0:
            self._update_live_result_panel(output)
        if detect_daily_report:
            self.last_report = self._detect_last_report()
            if self.last_report:
                self._write_line(f"Last report: {self.last_report}")
                self._write_checklist(self.last_report.with_suffix(".json"))
        self._finish_status(returncode, elapsed)
        self._set_running(False)

    def _extract_json_payload(self, output: str) -> dict | None:
        for start in [idx for idx, char in enumerate(output) if char == "{"][::-1]:
            raw = output[start:].strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            return payload if isinstance(payload, dict) else None
        return None

    def _fmt_pct(self, value: object) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "UNKNOWN"
        if math.isnan(number):
            return "UNKNOWN"
        return f"{number * 100:.2f}%"

    def _fmt_decimal(self, value: object) -> str:
        if value is None:
            return "UNKNOWN"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if math.isnan(number):
            return "UNKNOWN"
        return f"{number:.4f}".rstrip("0").rstrip(".")

    def _fmt_odds(self, value: object) -> str:
        if value is None:
            return "UNKNOWN"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if math.isnan(number):
            return "UNKNOWN"
        return f"{number:+.0f}" if abs(number) >= 100 else f"{number:.3f}"

    def _update_live_result_panel(self, output: str) -> None:
        self.live_mode_var.set("MANUAL_LOOKUP")
        if hasattr(self, "live_settings_notebook"):
            self.live_settings_notebook.select(self.live_manual_tab)
        self.live_basic_payload = None
        self._update_live_active_summary()
        payload = self._extract_json_payload(output)
        if not payload:
            message = "Live lookup zakonczony, ale nie udalo sie odczytac JSON wyniku z outputu."
            self.live_status_var.set("DONE - JSON NOT FOUND")
            self._set_live_summary(message)
            self.live_calculations_text.delete("1.0", tk.END)
            self.live_calculations_text.insert(tk.END, message)
            return
        team_a = self.live_team_var.get().strip().upper() or "TEAM_A"
        team_b = self.live_opponent_var.get().strip().upper() or "TEAM_B"
        path = str(payload.get("path") or self.live_lookup_path_var.get()).upper()
        sample = payload.get("sample_size", "UNKNOWN")
        quality = payload.get("sample_quality", "UNKNOWN")
        event = payload.get("event", self.live_event_var.get())
        settlement = payload.get("settlement", self.live_settlement_var.get())
        win_p = payload.get("win_probability")
        loss_p = payload.get("loss_probability")
        tie_p = payload.get("tie_probability")
        fair_decimal = payload.get("fair_decimal")
        fair_american = payload.get("fair_american")
        live_decimal = payload.get("live_decimal")
        live_american = payload.get("live_american")
        ev = payload.get("ev")

        node = self._load_live_lookup_node(path)
        q3_block = (node or {}).get("next_quarter_distribution", {})
        q3_win = q3_block.get("win_probability")
        q3_loss = q3_block.get("loss_probability")
        q3_tie = q3_block.get("tie_probability")
        warning = ""
        if str(quality).upper() in {"NO_DATA", "VERY_LOW", "LOW"}:
            warning = f"\nWARNING: sample quality {quality}; traktuj jako kontekst, nie samodzielny sygnal."

        summary = "\n".join(
            [
                f"Path: {path} | Event: {event} | Settlement: {settlement}",
                f"Sample: {sample} | Quality: {quality}",
                "",
                f"{team_a} after {path}:",
                f"Q3 win/loss/tie: {self._fmt_pct(q3_win)} / {self._fmt_pct(q3_loss)} / {self._fmt_pct(q3_tie)}",
                f"Final win/loss/tie: {self._fmt_pct(win_p)} / {self._fmt_pct(loss_p)} / {self._fmt_pct(tie_p)}",
                "",
                f"{team_b} mirror:",
                f"Q3 win/loss/tie: {self._fmt_pct(q3_loss)} / {self._fmt_pct(q3_win)} / {self._fmt_pct(q3_tie)}",
                f"Final win/loss/tie: {self._fmt_pct(loss_p)} / {self._fmt_pct(win_p)} / {self._fmt_pct(tie_p)}",
                "",
                f"Fair decimal: {self._fmt_decimal(fair_decimal)} | Fair American: {self._fmt_odds(fair_american)}",
                f"Live decimal: {self._fmt_decimal(live_decimal)} | Live American: {self._fmt_odds(live_american)}",
                f"EV: {self._fmt_pct(ev) if ev is not None else 'not calculated'}{warning}",
            ]
        )
        self.live_status_var.set(f"DONE - sample {sample}, quality {quality}")
        self._set_live_summary(summary)
        self.live_calculations_text.delete("1.0", tk.END)
        self.live_calculations_text.insert(tk.END, summary)
        self.live_calculations_text.insert(tk.END, "\n\nJSON payload:\n")
        self.live_calculations_text.insert(tk.END, json.dumps(payload, indent=2, ensure_ascii=False))

    def _load_live_lookup_node(self, path: str) -> dict | None:
        folder = self._live_output_folder()
        if folder is None:
            return None
        lookup_path = folder / "scenario_lookup.json"
        if not lookup_path.exists():
            return None
        try:
            payload = json.loads(lookup_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        node = payload.get(path)
        return node if isinstance(node, dict) else None

    def _write_checklist(self, json_path: Path) -> None:
        if not json_path.exists():
            return
        try:
            rows = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._write_line("")
            self._write_line(f"Checklist unavailable: {exc}")
            return
        if not isinstance(rows, list):
            return
        self._write_line("")
        self._write_line("Checklist:")
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = str(row.get("status") or "UNKNOWN")
            marker = self._status_marker(status)
            label = row.get("label") or row.get("id") or "unknown task"
            detail = (
                row.get("command")
                or row.get("expected_path")
                or row.get("expected_glob")
                or row.get("path")
                or row.get("reason")
                or ""
            )
            line = f"{marker} {status}: {label}"
            if detail:
                line += f" [{detail}]"
            self._write_line(line)

    def _status_marker(self, status: str) -> str:
        if status in {"PASS", "READY", "DRY_RUN", "SKIPPED"}:
            return "[x]"
        if status in {"NEEDS_OPERATOR", "MISSING", "FAIL"}:
            return "[ ]"
        return "[-]"

    def _detect_last_report(self) -> Path | None:
        values = self._validate()
        if values is None:
            return None
        season, week = values
        folder = REPO_ROOT / "research" / "daily_bot" / str(season) / f"week_{week:02d}"
        if not folder.exists():
            return None
        reports = sorted(folder.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
        return reports[0] if reports else None

    def _open_last_report(self) -> None:
        report = self.last_report or self._detect_last_report()
        if not report or not report.exists():
            messagebox.showinfo("No report", "Nie znaleziono raportu.")
            return
        subprocess.Popen(["notepad.exe", str(report)])

    def _open_report_folder(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        folder = REPO_ROOT / "research" / "daily_bot" / str(season) / f"week_{week:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _central_ledger_command(self, command: str) -> subprocess.CompletedProcess[str]:
        values = self._validate()
        if values is None:
            raise ValueError("season/week are invalid")
        season, week = values
        return subprocess.run(
            [
                str(PYTHON_EXE),
                "-m",
                "pregame.weekly_cli",
                "--root",
                str(PREGAME_DATA_ROOT),
                "--season",
                str(season),
                "--week",
                str(week),
                command,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def _refresh_central_ledger(self) -> None:
        try:
            result = self._central_ledger_command("status")
        except Exception as exc:
            messagebox.showerror("Ledger", f"Nie udalo sie odczytac ledgeru:\n{exc}")
            return
        self.ledger_status_text.configure(state=tk.NORMAL)
        self.ledger_status_text.delete("1.0", tk.END)
        self.ledger_status_text.insert(tk.END, result.stdout or result.stderr)
        self.ledger_status_text.configure(state=tk.DISABLED)

    def _open_central_ledger_report(self) -> None:
        try:
            result = self._central_ledger_command("report")
        except Exception as exc:
            messagebox.showerror("Ledger", f"Nie udalo sie wygenerowac raportu:\n{exc}")
            return
        if result.returncode != 0:
            messagebox.showerror("Ledger", result.stderr or result.stdout)
            return
        try:
            payload = json.loads(result.stdout)
            report = Path(payload["report_markdown"])
            if not report.is_absolute():
                report = REPO_ROOT / report
            if report.exists():
                subprocess.Popen(["notepad.exe", str(report)])
                return
        except (KeyError, TypeError, json.JSONDecodeError):
            pass
        messagebox.showerror("Ledger", result.stderr or "Raport ledgeru nie zostal utworzony.")

    def _live_output_folder(self) -> Path | None:
        try:
            start_season = int(self.live_start_season_var.get())
            end_season = int(self.live_end_season_var.get())
        except ValueError:
            messagebox.showerror("Invalid live input", "Live start/end season musza byc liczbami.")
            return None
        sample_mode = self.live_sample_mode_var.get().lower()
        return (
            REPO_ROOT
            / "research"
            / "live_quarter_scenario_matrix"
            / f"{start_season}_{end_season}_{sample_mode}"
        )

    def _open_live_scenario_folder(self) -> None:
        folder = self._live_output_folder()
        if folder is None:
            return
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _week_artifact_paths(self, season: int, week: int) -> list[Path]:
        variant = str(self.bot_config.get("variant", "variant_m"))
        return week_generated_artifact_paths(REPO_ROOT, season, week, variant)

    def _reset_week_test_data(self) -> None:
        values = self._validate()
        if values is None:
            return
        season, week = values
        existing = [path for path in self._week_artifact_paths(season, week) if path.exists()]
        if not existing:
            messagebox.showinfo("Nothing to reset", "Nie znaleziono artefaktow dla tego tygodnia.")
            return
        preview = "\n".join(str(path.relative_to(REPO_ROOT)) for path in existing[:20])
        if len(existing) > 20:
            preview += f"\n... oraz {len(existing) - 20} wiecej"
        ok = messagebox.askyesno(
            "Reset week test data",
            (
                f"Usunac artefakty testowe dla season={season}, week={week}?\n\n"
                f"{preview}\n\n"
                "Reczne wejscia (book/market/GPT/closing snapshots), dane historyczne "
                "i cache nfl_data_py zostana zachowane."
            ),
        )
        if not ok:
            return
        removed = []
        for path in existing:
            resolved = path.resolve()
            if not resolved.is_relative_to(REPO_ROOT):
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(path)
        self.output.delete("1.0", tk.END)
        self._write_line("Reset week test data:")
        for path in removed:
            self._write_line(f"[x] removed {path.relative_to(REPO_ROOT)}")
        self.model_pick_records = {}
        self.watch_records = {}
        self.selected_pick_record = None
        self.pick_box.configure(values=[])
        self.watch_box.configure(values=[])
        self.pick_var.set("")
        self.watch_var.set("")
        self.pick_summary_var.set("No model picks loaded.")
        self.watch_summary_var.set("No watchlist loaded.")

    def _finish_status(self, returncode: int, elapsed: float | None) -> None:
        elapsed_text = f" after {elapsed:.1f}s" if elapsed is not None else ""
        if returncode == 0:
            self.status_var.set(f"STATUS: DONE - {self.run_label}{elapsed_text}")
            self._write_line(f"FINISHED OK: {self.run_label}{elapsed_text}")
        else:
            self.status_var.set(f"STATUS: FAILED - {self.run_label}{elapsed_text}")
            self._write_line(f"FINISHED WITH ERRORS: {self.run_label}{elapsed_text}")

    def _refresh_run_timer(self) -> None:
        if self.run_started_at is None:
            return
        elapsed = (datetime.now().astimezone() - self.run_started_at).total_seconds()
        self.status_var.set(f"STATUS: RUNNING - {self.run_label} - {elapsed:.0f}s")
        self.after(1000, self._refresh_run_timer)

    def _set_running(self, running: bool, label: str | None = None) -> None:
        state = tk.DISABLED if running else tk.NORMAL
        self.dry_button.configure(state=state)
        self.execute_button.configure(state=state)
        self.week_dry_button.configure(state=state)
        self.reset_button.configure(state=state)
        for button in self.live_buttons:
            button.configure(state=state)
        if running:
            self.run_started_at = datetime.now().astimezone()
            self.run_label = label or "RUN"
            self.status_var.set(f"STATUS: RUNNING - {self.run_label} - 0s")
            self._refresh_run_timer()
        else:
            self.run_started_at = None

    def _write_line(self, text: str) -> None:
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)


def main() -> None:
    app = DailyBotGui()
    app.mainloop()


if __name__ == "__main__":
    main()
