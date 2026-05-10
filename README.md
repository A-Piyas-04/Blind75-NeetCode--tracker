# Blind75 Tracker

A personal desktop flashcard / randomizer app for practicing **NeetCode Blind 75** problems.  
Built with Python · CustomTkinter · SQLite — runs fully offline, no login or internet required.

---

## Features

| View | What it does |
|---|---|
| **Dashboard** | Live stats (total, easy, medium, hard counts), recently practiced problems, one-click Random Practice |
| **Add Problem** | Save a problem with name, difficulty, topic, optional LeetCode link, and multiline notes |
| **Problem List** | Browse all saved problems; search by name; filter by difficulty and topic; edit or delete any entry |
| **Random Practice** | Generate a random problem (with optional difficulty / topic filters), mark as practiced, edit notes inline |

### UX highlights
- Smooth **fade transition** between views (~160 ms)
- **Toast popup** confirmation for every Save, Update, and Delete action (visible 3 s, then fades out)
- **Practice count** and **last-practiced date** tracked automatically
- Friendly empty states and inline status messages throughout
- Confirm dialog before any destructive delete

---

## Demo Screenshots

![Screenshot 1](Demo%20Screenshots/1.png)

![Screenshot 2](Demo%20Screenshots/2.png)

![Screenshot 3](Demo%20Screenshots/3.png)

![Screenshot 4](Demo%20Screenshots/4.png)

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

The SQLite database (`neetcode_flashcards.db`) is created automatically in the project folder on first run.

---

## Building a Windows `.exe`

Always use `--collect-data customtkinter` so the UI assets are bundled correctly:

```bash
pyinstaller --onefile --windowed --collect-data customtkinter app.py
```

The executable is placed in `dist/app.exe`.

### Data persistence for the `.exe`

The app detects whether it is running as a frozen executable and stores the database **next to `app.exe`** (inside `dist/`), not in a temporary extraction folder. This means your data survives every relaunch.

If you already have data from running `python app.py`, copy it across once:

```
neetcode_flashcards.db  →  dist\neetcode_flashcards.db
```

After that both run modes maintain their own independent databases.

---

## Project structure

```
blind-75-tracker/
├── app.py               # Main window, sidebar navigation, all four views, fade transitions
├── database.py          # SQLite connection, schema, CRUD helpers, exe-aware DB path
├── ui_components.py     # Colour palette, fonts, widget factories, StatusBar, Toast
├── requirements.txt
├── README.md
├── neetcode_flashcards.db        # Created automatically (python app.py)
└── dist/
    ├── app.exe
    └── neetcode_flashcards.db    # Created automatically (app.exe)
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

Dark ocean-cyan palette — refined for reduced eye strain and a professional look.

| Role | Hex |
|---|---|
| Main background | `#06141B` |
| Card background | `#0B1E2D` |
| Sidebar | `#050E16` |
| Input background | `#0C2030` |
| Primary cyan | `#38BDD4` |
| Accent teal | `#26A294` |
| Body text | `#BADDE8` |
| Muted text | `#567E8E` |
| Easy / success | `#20A878` |
| Medium | `#C48A18` |
| Hard / danger | `#C04EA0` |
| Subtle border | `#1C3244` |

---

## Requirements

- Python 3.10 or later
- Windows 10 / 11  
  *(CustomTkinter also runs on macOS and Linux, though the `.exe` packaging targets Windows)*
