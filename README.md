# NeonCode Recall

A personal desktop flashcard / randomizer app for practicing **NeetCode Blind 75** problems.  
Built with Python · CustomTkinter · SQLite — runs fully offline, no login required.

---

## Features

| View | What it does |
|---|---|
| **Dashboard** | Stats (total, easy, medium, hard), recently practiced problems, quick Random Practice button |
| **Add Problem** | Save a problem with name, difficulty, topic, optional link, and multiline notes |
| **Problem List** | Browse all problems, search by name, filter by difficulty and topic, edit or delete |
| **Random Practice** | Generate a random problem (with optional filters), mark as practiced, edit notes inline |

---

## Getting started

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### 2 — Run the app

```bash
python app.py
```

The SQLite database (`neetcode_flashcards.db`) is created automatically in the same folder on first run.

---

## Building a Windows `.exe`

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```

The executable will be placed in the `dist/` folder.

> **Tip:** If the `.exe` can't find `customtkinter` assets, use the following instead:
>
> ```bash
> pyinstaller --onefile --windowed --collect-data customtkinter app.py
> ```

---

## Project structure

```
blind-75-tracker/
├── app.py               # Main window, sidebar navigation, all four views
├── database.py          # SQLite connection, schema, CRUD helpers
├── ui_components.py     # Colour palette, fonts, widget factories, StatusBar
├── requirements.txt
├── README.md
└── neetcode_flashcards.db   # Created automatically on first run
```

---

## Database schema

```sql
CREATE TABLE problems (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    difficulty     TEXT    NOT NULL,   -- Easy | Medium | Hard
    topic          TEXT,               -- Array, DP, Graph, …
    link           TEXT,               -- Optional LeetCode URL
    notes          TEXT,               -- Multiline freeform notes
    practice_count INTEGER DEFAULT 0,
    last_practiced TEXT,               -- ISO 8601 datetime
    created_at     TEXT,
    updated_at     TEXT
);
```

---

## UI theme

| Role | Hex |
|---|---|
| Main background | `#06141B` |
| Card background | `#0B2530` |
| Primary cyan | `#00E5FF` |
| Accent teal | `#14F1D9` |
| Text | `#E6FBFF` |
| Muted text | `#7FAAB5` |
| Danger / delete | `#FF4FD8` |
| Success / easy | `#00FFA3` |
| Medium | `#FFB800` |

---

## Requirements

- Python 3.10 or later
- Windows 10 / 11 (CustomTkinter works on macOS and Linux too)
