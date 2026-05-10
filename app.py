"""
app.py — Blind-75 Tracker
Main application window with sidebar navigation and four views:
  Dashboard · Add Problem · Problem List · Random Practice
"""
from __future__ import annotations

import webbrowser
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

import database as db
from ui_components import (
    COLORS, TOPICS, DIFFICULTIES, DIFFICULTY_COLORS,
    FONT_TITLE, FONT_HEADER, FONT_BODY, FONT_SMALL, FONT_MONO,
    make_card, make_label, make_button, make_danger_button,
    make_entry, make_textbox, make_combo,
    difficulty_badge_color, confirm_delete, StatusBar,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ── Tiny helpers ──────────────────────────────────────────────────────────────

def _fmt_date(iso: str | None) -> str:
    """Return a human-readable date string from an ISO datetime string."""
    if not iso:
        return "Never"
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %Y")
    except ValueError:
        return iso[:10]


def _scrollable(parent, **kw) -> ctk.CTkScrollableFrame:
    """Return a styled scrollable frame."""
    defaults = dict(
        fg_color=COLORS["bg_main"],
        corner_radius=0,
        scrollbar_button_color=COLORS["border"],
        scrollbar_button_hover_color=COLORS["primary"],
    )
    defaults.update(kw)
    return ctk.CTkScrollableFrame(parent, **defaults)


# ── Base view ─────────────────────────────────────────────────────────────────

class _BaseView(ctk.CTkFrame):
    def __init__(self, parent, app: "NeonCodeRecallApp"):
        super().__init__(parent, fg_color=COLORS["bg_main"], corner_radius=0)
        self._app = app
        self.grid_columnconfigure(0, weight=1)

    def on_show(self, **kwargs) -> None:  # noqa: B027
        pass


# ── Main Application ──────────────────────────────────────────────────────────

class NeonCodeRecallApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.create_tables()

        self.title("Blind-75 Tracker")
        self.geometry("1100x680")
        self.minsize(950, 620)
        self.configure(fg_color=COLORS["bg_main"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._nav_btns: dict = {}
        self._animating: bool = False   # prevents queuing overlapping fades
        self._build_sidebar()
        self._build_content()
        self.navigate_to("dashboard")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        sb = ctk.CTkFrame(
            self, width=235, corner_radius=0,
            fg_color=COLORS["bg_sidebar"],
        )
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(7, weight=1)   # pushes version to bottom

        # Logo
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, padx=22, pady=(30, 4), sticky="w")
        ctk.CTkLabel(
            logo, text="⬡  NeonCode",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS["primary"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo, text="    Recall",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, sticky="ew", padx=18, pady=(16, 18),
        )

        # Nav items
        nav_items = [
            ("dashboard",       "⊞",  "Dashboard"),
            ("add_problem",     "+",  "Add Problem"),
            ("problem_list",    "≡",  "Problem List"),
            ("random_practice", "⚄", "Random Practice"),
        ]
        for i, (vid, icon, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                sb,
                text=f"  {icon}   {label}",
                anchor="w",
                font=("Segoe UI", 14),
                fg_color="transparent",
                text_color=COLORS["muted"],
                hover_color=COLORS["hover"],
                corner_radius=10,
                height=46,
                command=lambda v=vid: self.navigate_to(v),
            )
            btn.grid(row=i, column=0, padx=10, pady=2, sticky="ew")
            self._nav_btns[vid] = btn

        # Version footer
        ctk.CTkLabel(
            sb,
            text="v1.0  ·  NeetCode Blind 75",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
        ).grid(row=8, column=0, pady=18)

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self) -> None:
        content = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORS["bg_main"],
        )
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self._views: dict = {
            "dashboard":       DashboardView(content, self),
            "add_problem":     AddProblemView(content, self),
            "problem_list":    ProblemListView(content, self),
            "random_practice": RandomPracticeView(content, self),
        }
        for v in self._views.values():
            v.grid(row=0, column=0, sticky="nsew")

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to(self, view_id: str, **kwargs) -> None:
        if self._animating:
            return

        # Update sidebar highlight immediately so it feels responsive
        for vid, btn in self._nav_btns.items():
            active = vid == view_id
            btn.configure(
                fg_color=COLORS["hover"] if active else "transparent",
                text_color=COLORS["primary"] if active else COLORS["muted"],
                font=("Segoe UI", 14, "bold") if active else ("Segoe UI", 14),
            )

        view = self._views[view_id]
        view.on_show(**kwargs)
        self._fade_transition(view)

    def _fade_transition(self, new_view: "_BaseView") -> None:
        """Smooth fade-out → swap → fade-in transition (~160 ms total)."""
        STEPS    = 8        # steps per direction
        MIN_A    = 0.88     # how far we dim (0 = black, 1 = opaque)
        INTERVAL = 10       # ms between each step

        self._animating = True

        def step(n: int) -> None:
            if n <= STEPS:
                # Fade out
                alpha = 1.0 - (1.0 - MIN_A) * (n / STEPS)
                self.attributes("-alpha", alpha)
                if n == STEPS:
                    new_view.tkraise()   # swap at the darkest point
                self.after(INTERVAL, lambda: step(n + 1))
            elif n <= STEPS * 2:
                # Fade in
                alpha = MIN_A + (1.0 - MIN_A) * ((n - STEPS) / STEPS)
                self.attributes("-alpha", alpha)
                if n < STEPS * 2:
                    self.after(INTERVAL, lambda: step(n + 1))
                else:
                    self.attributes("-alpha", 1.0)
                    self._animating = False

        step(0)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardView(_BaseView):
    def __init__(self, parent, app: NeonCodeRecallApp):
        super().__init__(parent, app)
        self.grid_rowconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        scroll = _scrollable(self)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self._scroll = scroll

        # ── Header row ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(30, 0))
        hdr.grid_columnconfigure(0, weight=1)

        make_label(hdr, "Dashboard", font=FONT_TITLE).grid(
            row=0, column=0, sticky="w",
        )
        make_button(
            hdr,
            "⚄  Random Practice",
            width=162, height=54,
            command=lambda: self._app.navigate_to("random_practice"),
        ).grid(row=0, column=1, sticky="e")

        make_label(
            scroll,
            "Your NeetCode Blind 75 practice at a glance.",
            color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(4, 24))

        # ── Stats row (rebuilt on refresh) ────────────────────────────────────
        self._stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        self._stats_row.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 30))

        # ── Recent activity ───────────────────────────────────────────────────
        make_label(
            scroll, "Recently Practiced",
            font=FONT_HEADER, color=COLORS["accent"],
        ).grid(row=3, column=0, sticky="w", padx=32, pady=(0, 10))

        self._recent_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._recent_frame.grid(
            row=4, column=0, sticky="ew", padx=32, pady=(0, 24),
        )
        self._recent_frame.grid_columnconfigure(0, weight=1)

    def on_show(self, **kwargs) -> None:
        self._refresh()

    def _refresh(self) -> None:
        stats = db.get_stats()

        # Rebuild stat cards
        for w in self._stats_row.winfo_children():
            w.destroy()

        for label, value, color in [
            ("Total Problems", str(stats["total"]),  COLORS["primary"]),
            ("Easy",           str(stats["easy"]),   COLORS["easy"]),
            ("Medium",         str(stats["medium"]), COLORS["medium"]),
            ("Hard",           str(stats["hard"]),   COLORS["hard"]),
        ]:
            card = make_card(self._stats_row, width=152, height=100)
            card.pack(side="left", padx=(0, 14))
            card.pack_propagate(False)
            ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI", 38, "bold"),
                text_color=color,
            ).pack(pady=(14, 2))
            make_label(card, label, color=COLORS["muted"], font=("Segoe UI", 12)).pack()

        # Rebuild recent list
        for w in self._recent_frame.winfo_children():
            w.destroy()

        if not stats["recent"]:
            make_label(
                self._recent_frame,
                "No problems practiced yet — hit  ⚄ Random Practice  to get started!",
                color=COLORS["muted"],
            ).grid(row=0, column=0, sticky="w", pady=12)
            return

        for i, p in enumerate(stats["recent"]):
            self._make_recent_row(p, i)

    def _make_recent_row(self, p: dict, idx: int) -> None:
        card = make_card(self._recent_frame)
        card.grid(row=idx, column=0, sticky="ew", pady=3)
        card.grid_columnconfigure(1, weight=1)

        # Difficulty badge
        dc = difficulty_badge_color(p["difficulty"])
        ctk.CTkLabel(
            card,
            text=p["difficulty"],
            font=("Segoe UI", 11, "bold"),
            text_color=COLORS["bg_main"],
            fg_color=dc,
            corner_radius=8,
            width=66,
            height=26,
        ).grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=12, sticky="ns")

        make_label(
            card, p["name"], font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=1, sticky="w")

        make_label(
            card,
            f"{p['topic']}  ·  {p['practice_count']}× practiced  ·  Last: {_fmt_date(p['last_practiced'])}",
            color=COLORS["muted"],
            font=FONT_SMALL,
        ).grid(row=1, column=1, sticky="w")

        make_button(
            card, "Practice Again", width=114, height=48,
            command=lambda: self._app.navigate_to("random_practice"),
        ).grid(row=0, column=2, rowspan=2, padx=14)


# ── Add / Edit Problem ────────────────────────────────────────────────────────

class AddProblemView(_BaseView):
    def __init__(self, parent, app: NeonCodeRecallApp):
        super().__init__(parent, app)
        self.grid_rowconfigure(0, weight=1)
        self._edit_id: int | None = None
        self._build()

    def _build(self) -> None:
        scroll = _scrollable(self)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(scroll, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="ew", padx=44, pady=30)
        outer.grid_columnconfigure(0, weight=1)

        # Dynamic title / subtitle
        self._title_lbl = make_label(outer, "Add Problem", font=FONT_TITLE)
        self._title_lbl.grid(row=0, column=0, sticky="w", pady=(0, 3))

        self._sub_lbl = make_label(
            outer,
            "Save a new coding problem to your collection.",
            color=COLORS["muted"],
        )
        self._sub_lbl.grid(row=1, column=0, sticky="w", pady=(0, 22))

        # ── Form card ─────────────────────────────────────────────────────────
        form = make_card(outer)
        form.grid(row=2, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        def field_label(text: str, row: int) -> None:
            make_label(
                form, text, color=COLORS["muted"], font=("Segoe UI", 12),
            ).grid(row=row, column=0, sticky="nw", padx=22, pady=(20, 0))

        field_label("Problem Name *", 0)
        self._name_entry = make_entry(form, "e.g.  Two Sum")
        self._name_entry.grid(
            row=0, column=1, sticky="ew", padx=(12, 22), pady=(20, 0),
        )

        field_label("Difficulty *", 1)
        self._diff_combo = make_combo(form, DIFFICULTIES, width=210)
        self._diff_combo.set("Medium")
        self._diff_combo.grid(
            row=1, column=1, sticky="w", padx=(12, 22), pady=(14, 0),
        )

        field_label("Topic / Category *", 2)
        self._topic_combo = make_combo(form, TOPICS, width=255)
        self._topic_combo.set(TOPICS[0])
        self._topic_combo.grid(
            row=2, column=1, sticky="w", padx=(12, 22), pady=(14, 0),
        )

        field_label("Problem Link", 3)
        self._link_entry = make_entry(
            form, "https://leetcode.com/problems/...",
        )
        self._link_entry.grid(
            row=3, column=1, sticky="ew", padx=(12, 22), pady=(14, 0),
        )

        field_label("Notes", 4)
        make_label(
            form,
            "Patterns, edge cases, time complexity, mistakes…",
            color=COLORS["muted"],
            font=("Segoe UI", 10),
        ).grid(row=4, column=1, sticky="w", padx=(12, 22), pady=(14, 0))
        self._notes_box = make_textbox(form, height=210)
        self._notes_box.grid(
            row=5, column=1, sticky="ew", padx=(12, 22), pady=(6, 22),
        )

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="w", pady=(18, 0))

        self._save_btn = make_button(
            btn_row, "Save Problem", width=126, height=54, command=self._save,
        )
        self._save_btn.pack(side="left", padx=(0, 12))

        make_button(
            btn_row, "Cancel",
            color=COLORS["bg_card"],
            hover=COLORS["hover"],
            width=90, height=54,
            command=lambda: self._app.navigate_to("problem_list"),
        ).pack(side="left")

        self._status = StatusBar(outer)
        self._status.grid(row=4, column=0, sticky="w", pady=(10, 0))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self, problem_id: int | None = None, **kwargs) -> None:
        self._edit_id = problem_id
        if problem_id is not None:
            p = db.get_problem_by_id(problem_id)
            if not p:
                return
            self._title_lbl.configure(text="Edit Problem")
            self._sub_lbl.configure(text="Update the details for this problem.")
            self._save_btn.configure(text="Update Problem")
            self._name_entry.delete(0, "end")
            self._name_entry.insert(0, p["name"])
            self._diff_combo.set(p["difficulty"])
            self._topic_combo.set(p["topic"] or TOPICS[0])
            self._link_entry.delete(0, "end")
            self._link_entry.insert(0, p["link"] or "")
            self._notes_box.delete("1.0", "end")
            if p["notes"]:
                self._notes_box.insert("1.0", p["notes"])
        else:
            self._title_lbl.configure(text="Add Problem")
            self._sub_lbl.configure(
                text="Save a new coding problem to your collection.",
            )
            self._save_btn.configure(text="Save Problem")
            self._clear_form()

    def _clear_form(self) -> None:
        self._name_entry.delete(0, "end")
        self._diff_combo.set("Medium")
        self._topic_combo.set(TOPICS[0])
        self._link_entry.delete(0, "end")
        self._notes_box.delete("1.0", "end")

    def _save(self) -> None:
        name  = self._name_entry.get().strip()
        diff  = self._diff_combo.get().strip()
        topic = self._topic_combo.get().strip()
        link  = self._link_entry.get().strip()
        notes = self._notes_box.get("1.0", "end").strip()

        if not name:
            self._status.show("Problem name is required.", kind="error")
            return
        if diff not in DIFFICULTIES:
            self._status.show("Please select a valid difficulty.", kind="error")
            return

        if self._edit_id is not None:
            db.update_problem(self._edit_id, name, diff, topic, link, notes)
            self._status.show("Problem updated successfully!")
        else:
            db.add_problem(name, diff, topic, link, notes)
            self._status.show(
                "Problem saved!  Add another or browse Problem List.",
            )
            self._clear_form()


# ── Problem List ──────────────────────────────────────────────────────────────

class ProblemListView(_BaseView):
    def __init__(self, parent, app: NeonCodeRecallApp):
        super().__init__(parent, app)
        self.grid_rowconfigure(3, weight=1)   # scrollable list expands
        self._build()

    def _build(self) -> None:
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(30, 0))
        hdr.grid_columnconfigure(0, weight=1)

        make_label(hdr, "Problem List", font=FONT_TITLE).grid(
            row=0, column=0, sticky="w",
        )
        make_button(
            hdr, "+  Add Problem", width=126, height=54,
            command=lambda: self._app.navigate_to("add_problem"),
        ).grid(row=0, column=1, sticky="e")

        make_label(
            self,
            "Browse, search, and manage your saved problems.",
            color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(4, 14))

        # ── Filter bar ────────────────────────────────────────────────────────
        fbar = make_card(self)
        fbar.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 12))

        fi = ctk.CTkFrame(fbar, fg_color="transparent")
        fi.pack(fill="x", padx=16, pady=11)

        make_label(fi, "Search:", color=COLORS["muted"], font=FONT_SMALL).pack(
            side="left", padx=(0, 6),
        )
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh())
        s = make_entry(fi, "Search by name…", width=220)
        s.configure(textvariable=self._search_var)
        s.pack(side="left", padx=(0, 22))

        make_label(fi, "Difficulty:", color=COLORS["muted"], font=FONT_SMALL).pack(
            side="left", padx=(0, 6),
        )
        self._diff_combo = make_combo(
            fi, ["All"] + DIFFICULTIES, width=130,
            command=lambda _: self._refresh(),
        )
        self._diff_combo.set("All")
        self._diff_combo.pack(side="left", padx=(0, 22))

        make_label(fi, "Topic:", color=COLORS["muted"], font=FONT_SMALL).pack(
            side="left", padx=(0, 6),
        )
        self._topic_combo = make_combo(
            fi, ["All"] + TOPICS, width=185,
            command=lambda _: self._refresh(),
        )
        self._topic_combo.set("All")
        self._topic_combo.pack(side="left", padx=(0, 22))

        self._count_lbl = make_label(fi, "", color=COLORS["muted"], font=FONT_SMALL)
        self._count_lbl.pack(side="right")

        # ── Scrollable list ───────────────────────────────────────────────────
        self._list = _scrollable(self)
        self._list.grid(
            row=3, column=0, sticky="nsew", padx=32, pady=(0, 12),
        )
        self._list.grid_columnconfigure(0, weight=1)

    def on_show(self, **kwargs) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for w in self._list.winfo_children():
            w.destroy()

        problems = db.get_all_problems(
            search=self._search_var.get(),
            difficulty=self._diff_combo.get(),
            topic=self._topic_combo.get(),
        )
        n = len(problems)
        self._count_lbl.configure(
            text=f"{n} problem{'s' if n != 1 else ''}",
        )

        if not problems:
            empty = ctk.CTkFrame(self._list, fg_color="transparent")
            empty.pack(pady=50)
            make_label(
                empty, "No problems found.",
                font=("Segoe UI", 15), color=COLORS["muted"],
            ).pack()
            make_label(
                empty,
                "Try different filters, or add a new problem via  +  Add Problem.",
                color=COLORS["muted"], font=FONT_SMALL,
            ).pack(pady=4)
            return

        for p in problems:
            self._make_card(p)

    def _make_card(self, p: dict) -> None:
        card = make_card(self._list)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        # Difficulty badge
        dc = difficulty_badge_color(p["difficulty"])
        ctk.CTkLabel(
            card,
            text=p["difficulty"],
            font=("Segoe UI", 11, "bold"),
            text_color=COLORS["bg_main"],
            fg_color=dc,
            corner_radius=8,
            width=66,
            height=26,
        ).grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=13, sticky="ns")

        make_label(
            card, p["name"], font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=1, sticky="w")

        last = _fmt_date(p["last_practiced"])
        make_label(
            card,
            f"{p['topic']}  ·  Practiced {p['practice_count']}×  ·  Last: {last}",
            color=COLORS["muted"],
            font=FONT_SMALL,
        ).grid(row=1, column=1, sticky="w")

        # Edit / Delete buttons
        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.grid(row=0, column=2, rowspan=2, padx=14)

        make_button(
            bf, "Edit", width=72, height=48,
            command=lambda pid=p["id"]: self._app.navigate_to(
                "add_problem", problem_id=pid,
            ),
        ).pack(side="left", padx=(0, 8))

        make_danger_button(
            bf, "Delete", width=72, height=48,
            command=lambda pid=p["id"], nm=p["name"]: self._delete(pid, nm),
        ).pack(side="left")

    def _delete(self, pid: int, name: str) -> None:
        if confirm_delete(name):
            db.delete_problem(pid)
            self._refresh()


# ── Random Practice ───────────────────────────────────────────────────────────

class RandomPracticeView(_BaseView):
    def __init__(self, parent, app: NeonCodeRecallApp):
        super().__init__(parent, app)
        self.grid_rowconfigure(3, weight=1)   # content area expands
        self._current: dict | None = None
        self._editing_notes: bool = False
        self._build()

    def _build(self) -> None:
        # ── Header ────────────────────────────────────────────────────────────
        make_label(self, "Random Practice", font=FONT_TITLE).grid(
            row=0, column=0, sticky="w", padx=32, pady=(30, 0),
        )
        make_label(
            self,
            "Spin the wheel — get a problem, practice, and level up.",
            color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=32, pady=(4, 18))

        # ── Filter bar ────────────────────────────────────────────────────────
        fbar = make_card(self)
        fbar.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 16))

        fi = ctk.CTkFrame(fbar, fg_color="transparent")
        fi.pack(fill="x", padx=16, pady=14)

        make_label(fi, "Difficulty:", color=COLORS["muted"], font=FONT_SMALL).pack(
            side="left", padx=(0, 6),
        )
        self._diff_combo = make_combo(fi, ["All"] + DIFFICULTIES, width=145)
        self._diff_combo.set("All")
        self._diff_combo.pack(side="left", padx=(0, 22))

        make_label(fi, "Topic:", color=COLORS["muted"], font=FONT_SMALL).pack(
            side="left", padx=(0, 6),
        )
        self._topic_combo = make_combo(fi, ["All"] + TOPICS, width=195)
        self._topic_combo.set("All")
        self._topic_combo.pack(side="left", padx=(0, 26))

        make_button(
            fi, "⚄  Generate Random", width=162, height=48,
            command=self._generate,
        ).pack(side="left")

        # ── Scrollable content ────────────────────────────────────────────────
        self._scroll = _scrollable(self)
        self._scroll.grid(
            row=3, column=0, sticky="nsew", padx=32, pady=(0, 12),
        )
        self._scroll.grid_columnconfigure(0, weight=1)

        # Empty state (shown until first generate)
        self._empty = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._empty.grid(row=0, column=0, pady=60)
        make_label(
            self._empty,
            "Click  ⚄ Generate Random  above to get started!",
            font=("Segoe UI", 15),
            color=COLORS["muted"],
        ).pack()

        # Problem card (hidden until generated)
        self._pcard = make_card(self._scroll)
        self._pcard.grid_columnconfigure(0, weight=1)

        # Build all card interior widgets (shown/hidden as needed)
        pc = ctk.CTkFrame(self._pcard, fg_color="transparent")
        pc.pack(fill="x", padx=22, pady=20)
        pc.grid_columnconfigure(0, weight=1)

        # Name + difficulty badge
        name_row = ctk.CTkFrame(pc, fg_color="transparent")
        name_row.pack(fill="x", pady=(0, 6))

        self._p_name = make_label(name_row, "", font=("Segoe UI", 22, "bold"))
        self._p_name.pack(side="left")

        self._p_diff = ctk.CTkLabel(
            name_row,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["bg_main"],
            fg_color=COLORS["easy"],
            corner_radius=8,
            width=76,
            height=28,
        )
        self._p_diff.pack(side="left", padx=14)

        # Meta line
        self._p_meta = make_label(pc, "", color=COLORS["muted"], font=FONT_SMALL)
        self._p_meta.pack(anchor="w", pady=(0, 10))

        # Link button (shown only when link exists)
        self._p_link_btn = ctk.CTkButton(
            pc,
            text="",
            width=230,
            height=28,
            fg_color="transparent",
            text_color=COLORS["primary"],
            hover_color=COLORS["hover"],
            font=("Segoe UI", 12, "underline"),
            anchor="w",
        )

        # Divider
        ctk.CTkFrame(pc, height=1, fg_color=COLORS["border"]).pack(
            fill="x", pady=(6, 14),
        )

        # Notes header
        notes_hdr = ctk.CTkFrame(pc, fg_color="transparent")
        notes_hdr.pack(fill="x", pady=(0, 6))

        make_label(
            notes_hdr, "Notes",
            font=("Segoe UI", 14, "bold"),
            color=COLORS["accent"],
        ).pack(side="left")

        self._edit_notes_btn = ctk.CTkButton(
            notes_hdr,
            text="✎  Edit Notes",
            width=90,
            height=44,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["muted"],
            hover_color=COLORS["hover"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8,
            font=("Segoe UI", 12),
            command=self._toggle_notes_edit,
        )
        self._edit_notes_btn.pack(side="right")

        # Notes textbox — toggled between disabled (display) and normal (edit)
        self._notes_box = ctk.CTkTextbox(
            pc,
            fg_color="transparent",
            text_color=COLORS["text"],
            border_width=0,
            corner_radius=8,
            font=FONT_MONO,
            height=155,
            wrap="word",
            state="disabled",
        )
        self._notes_box.pack(fill="x")

        # Save notes button (only packed in edit mode)
        self._save_notes_btn = make_button(
            pc, "Save Notes", width=90, height=60, command=self._save_notes,
        )

        # Action buttons
        act = ctk.CTkFrame(pc, fg_color="transparent")
        act.pack(fill="x", pady=(18, 0))

        make_button(
            act, "⚄  Generate Another", width=162, height=54,
            command=self._generate,
        ).pack(side="left", padx=(0, 12))

        make_button(
            act, "✓  Mark as Practiced", width=162, height=54,
            color=COLORS["success"],
            hover="#00CC80",
            command=self._mark_practiced,
        ).pack(side="left")

        self._status = StatusBar(pc)
        self._status.pack(anchor="w", pady=(12, 0))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_show(self, **kwargs) -> None:
        pass   # preserve current problem state when switching back

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _generate(self) -> None:
        diff  = self._diff_combo.get()
        topic = self._topic_combo.get()
        p = db.get_random_problem(diff, topic)
        if not p:
            if diff == "All" and topic == "All":
                msg = "No problems saved yet.\nGo to Add Problem to add some!"
            else:
                msg = "No problems match those filters.\nTry selecting 'All' for difficulty or topic."
            messagebox.showinfo("No Problems Found", msg)
            return
        self._current = p
        self._editing_notes = False
        self._show_problem()

    def _show_problem(self) -> None:
        p = self._current
        if not p:
            return

        # Swap empty state for problem card
        self._empty.grid_forget()
        self._pcard.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._p_name.configure(text=p["name"])
        dc = difficulty_badge_color(p["difficulty"])
        self._p_diff.configure(text=p["difficulty"], fg_color=dc)

        last = _fmt_date(p["last_practiced"])
        self._p_meta.configure(
            text=f"{p['topic']}  ·  Practiced {p['practice_count']}×  ·  Last: {last}",
        )

        # Link
        link = (p.get("link") or "").strip()
        if link:
            self._p_link_btn.configure(
                text="↗  Open Problem Link",
                command=lambda url=link: webbrowser.open(url),
            )
            self._p_link_btn.pack(anchor="w", pady=(0, 6))
        else:
            self._p_link_btn.pack_forget()

        self._render_notes_display()

    def _render_notes_display(self) -> None:
        """Switch notes textbox to read-only display mode."""
        notes = (self._current or {}).get("notes") or ""
        self._save_notes_btn.pack_forget()
        self._edit_notes_btn.configure(text="✎  Edit Notes")
        self._editing_notes = False

        # Write into textbox then lock it
        self._notes_box.configure(state="normal")
        self._notes_box.delete("1.0", "end")
        if notes:
            self._notes_box.insert("1.0", notes)
            self._notes_box.configure(
                text_color=COLORS["text"],
                fg_color="transparent",
                border_width=0,
            )
        else:
            self._notes_box.insert(
                "1.0",
                "(No notes yet — click  ✎ Edit Notes  to add some.)",
            )
            self._notes_box.configure(
                text_color=COLORS["muted"],
                fg_color="transparent",
                border_width=0,
            )
        self._notes_box.configure(state="disabled")

    def _toggle_notes_edit(self) -> None:
        if self._editing_notes:
            self._render_notes_display()
        else:
            notes = (self._current or {}).get("notes") or ""
            self._notes_box.configure(
                state="normal",
                fg_color=COLORS["bg_input"],
                text_color=COLORS["text"],
                border_width=1,
                border_color=COLORS["border"],
            )
            self._notes_box.delete("1.0", "end")
            self._notes_box.insert("1.0", notes)
            self._edit_notes_btn.configure(text="✕  Cancel")
            self._save_notes_btn.pack(anchor="w", pady=(8, 2))
            self._editing_notes = True

    def _save_notes(self) -> None:
        if not self._current:
            return
        notes = self._notes_box.get("1.0", "end").strip()
        db.update_notes(self._current["id"], notes)
        self._current["notes"] = notes
        self._render_notes_display()
        self._status.show("Notes saved!")

    def _mark_practiced(self) -> None:
        if not self._current:
            return
        db.mark_as_practiced(self._current["id"])
        self._current = db.get_problem_by_id(self._current["id"])
        self._show_problem()
        count = self._current["practice_count"]
        self._status.show(f"Marked as practiced!  ({count}× total)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = NeonCodeRecallApp()
    app.mainloop()
