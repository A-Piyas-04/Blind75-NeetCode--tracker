"""ui_components.py — Shared palette, fonts, and widget factory helpers."""
from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

# ── Palette ───────────────────────────────────────────────────────────────────

COLORS: dict = {
    # ── Surfaces ──────────────────────────────────────────────────────────────
    "bg_main":    "#06141B",   # deep ocean base
    "bg_card":    "#0B1E2D",   # elevated card surface
    "bg_sidebar": "#050E16",   # sidebar panel (slightly deeper)
    "bg_input":   "#0C2030",   # input / textbox background

    # ── Brand ─────────────────────────────────────────────────────────────────
    "primary":    "#38BDD4",   # soft cyan   (was #00E5FF — too neon)
    "accent":     "#26A294",   # muted teal  (was #14F1D9 — too neon)

    # ── Text ──────────────────────────────────────────────────────────────────
    "text":       "#BADDE8",   # comfortable reading white (was #E6FBFF)
    "muted":      "#567E8E",   # subdued label text

    # ── Semantic ──────────────────────────────────────────────────────────────
    "danger":     "#C04EA0",   # soft magenta  (was #FF4FD8)
    "success":    "#20A878",   # soft seafoam  (was #00FFA3)
    "easy":       "#20A878",
    "medium":     "#C48A18",   # warm amber    (was #FFB800)
    "hard":       "#C04EA0",

    # ── Chrome ────────────────────────────────────────────────────────────────
    "border":     "#1C3244",   # subtle card border
    "hover":      "#122438",   # interactive hover tint
}

DIFFICULTY_COLORS: dict = {
    "Easy":   COLORS["easy"],
    "Medium": COLORS["medium"],
    "Hard":   COLORS["hard"],
}

TOPICS: list = [
    "Array", "Hash Map", "Two Pointers", "Sliding Window", "Stack",
    "Binary Search", "Linked List", "Tree", "Trie", "Heap",
    "Graph", "Dynamic Programming", "Greedy", "Backtracking",
    "Bit Manipulation", "Math", "Other",
]

DIFFICULTIES: list = ["Easy", "Medium", "Hard"]

# ── Fonts ─────────────────────────────────────────────────────────────────────

FONT_TITLE  = ("Segoe UI", 26, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_BODY   = ("Segoe UI", 14)
FONT_SMALL  = ("Segoe UI", 12)
FONT_MONO   = ("Consolas", 13)

# ── Widget factories ──────────────────────────────────────────────────────────

def make_card(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(
        fg_color=COLORS["bg_card"],
        corner_radius=14,
        border_width=1,
        border_color=COLORS["border"],
    )
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def make_label(
    parent,
    text: str = "",
    font=None,
    color: str | None = None,
    **kw,
) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent,
        text=text,
        font=font or FONT_BODY,
        text_color=color or COLORS["text"],
        **kw,
    )


def make_button(
    parent,
    text: str,
    command=None,
    color: str | None = None,
    hover: str | None = None,
    width: int = 120,
    **kw,
) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=color or COLORS["primary"],
        hover_color=hover or COLORS["accent"],
        text_color=COLORS["bg_main"],
        font=("Segoe UI", 14, "bold"),
        corner_radius=8,
        width=width,
        **kw,
    )


def make_danger_button(
    parent,
    text: str,
    command=None,
    width: int = 100,
    **kw,
) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=COLORS["danger"],
        hover_color="#A83E8A",
        text_color=COLORS["bg_main"],
        font=("Segoe UI", 14, "bold"),
        corner_radius=8,
        width=width,
        **kw,
    )


def make_entry(
    parent,
    placeholder: str = "",
    width: int = 360,
    **kw,
) -> ctk.CTkEntry:
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        placeholder_text_color=COLORS["muted"],
        fg_color=COLORS["bg_input"],
        text_color=COLORS["text"],
        border_color=COLORS["border"],
        border_width=1,
        corner_radius=8,
        font=FONT_BODY,
        width=width,
        **kw,
    )


def make_textbox(
    parent,
    width: int = 460,
    height: int = 140,
    **kw,
) -> ctk.CTkTextbox:
    return ctk.CTkTextbox(
        parent,
        fg_color=COLORS["bg_input"],
        text_color=COLORS["text"],
        border_color=COLORS["border"],
        border_width=1,
        corner_radius=8,
        font=FONT_MONO,
        width=width,
        height=height,
        wrap="word",
        **kw,
    )


def make_combo(
    parent,
    values: list,
    width: int = 230,
    **kw,
) -> ctk.CTkComboBox:
    defaults = dict(
        fg_color=COLORS["bg_input"],
        text_color=COLORS["text"],
        button_color=COLORS["primary"],
        button_hover_color=COLORS["accent"],
        border_color=COLORS["border"],
        dropdown_fg_color=COLORS["bg_card"],
        dropdown_text_color=COLORS["text"],
        dropdown_hover_color=COLORS["hover"],
        font=FONT_BODY,
        width=width,
    )
    defaults.update(kw)
    return ctk.CTkComboBox(parent, values=values, **defaults)


def difficulty_badge_color(difficulty: str) -> str:
    return DIFFICULTY_COLORS.get(difficulty, COLORS["muted"])


def confirm_delete(name: str) -> bool:
    return messagebox.askyesno(
        "Confirm Delete",
        f'Delete "{name}"?\n\nThis action cannot be undone.',
        icon="warning",
    )


# ── Status bar ────────────────────────────────────────────────────────────────

class StatusBar:
    """Inline status label that auto-clears after a delay."""

    def __init__(self, parent):
        self._lbl = ctk.CTkLabel(
            parent,
            text="",
            font=FONT_SMALL,
            text_color=COLORS["success"],
            anchor="w",
        )
        self._job: str | None = None

    def pack(self, **kw) -> None:
        self._lbl.pack(**kw)

    def grid(self, **kw) -> None:
        self._lbl.grid(**kw)

    def show(self, message: str, kind: str = "success", ms: int = 3500) -> None:
        if self._job:
            self._lbl.after_cancel(self._job)
        color = COLORS["success"] if kind == "success" else COLORS["danger"]
        self._lbl.configure(text=message, text_color=color)
        self._job = self._lbl.after(ms, lambda: self._lbl.configure(text=""))
