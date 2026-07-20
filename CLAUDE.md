# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Offline PyQt5 desktop app: an interactive Elden Ring map with per-user profiles, progress
tracking, multiple map layers (surface / underground / dlc), a user waypoint system, and a
separate item database browser. Primary UI language is Russian (`ru`), with English (`en`) as
a secondary locale — most in-code comments and default strings are Russian.

There is no build system, package manifest, or test suite in this repo. It's a small, flat
Python/Qt codebase run directly with the interpreter.

## Running the app

```bash
pip install PyQt5
python main.py
```

`main.py` is the dev entry point — it imports the other modules directly. There's no
`requirements.txt`; PyQt5 is the only third-party dependency.

Runtime assets are gitignored and not present in a fresh checkout — `/maps`, `/icons`,
`/saves`, and `/icons/waypoint_icons` must exist alongside the `.py` files for the app to
render anything (map backgrounds, marker icons, save data). If those are missing, widgets
still construct but images fail silently (`QPixmap(...).isNull()` checks throughout, mostly
just printed and skipped).

There are no linter/formatter/test commands configured — nothing to run before committing
beyond manually exercising the app.

## Distribution / packaging flow

The shipped (Nexus/itch.io) build does not run `main.py` directly. Instead:

1. `pack.core.py` zips `main.py`, `interface.py`, `components.py`, `config.py` into
   `core/data.dat` (a zip file with a non-`.zip` extension).
2. `launcher.py` is the real shipped entry point: it `sys.path.insert(0, core/data.dat)` and
   imports `MainWindow` straight out of the zip (Python's zipimport), then runs the app.

When changing any of those four core modules, re-run `pack.core.py` if you need to test the
packaged/launcher flow — `python main.py` alone only exercises the unpacked source.

Every module that needs a filesystem base path repeats the same pattern (frozen-exe vs.
source-run):
```python
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))  # or __file__ in launcher.py
```
Keep new file I/O consistent with this — don't assume `os.getcwd()`.

## Module map

- **`config.py`** — all static configuration, no UI/Qt widgets beyond none. This is the file
  to edit when adding a new marker category or locale string:
  - `REGISTRY`: the central wiring table. Each key (e.g. `"grace"`, `"bird"`, `"grace_dlc"`)
    describes one marker category — its icon, which `DATA_MANIFEST` source it reads from,
    which top-level JSON keys to pull (`json_keys`), whether it's `is_regional` (nested by map
    layer) and its display label(s).
  - `DATA_MANIFEST`: maps an internal source key (e.g. `"grace_data"`) to a JSON *base
    filename* (e.g. `"graces"`), resolved against whatever is actually found under `DATA/`.
  - `CATEGORIES_BASE` / `CATEGORIES_DLC`: sidebar grouping structure for `MapScreen`. Keys here
    must line up with `REGISTRY` keys and with `lbl_<key>` entries in `LOCALES`.
  - `LOCALES`: `ru`/`en` string tables for static UI chrome and generated checkbox labels.
  - `get_img(filename)` / `IMAGE_CACHE`: lazily walks `icons/` once and caches a flat
    `filename -> full path` map. Icon filenames must be unique across the whole `icons/` tree.
- **`main.py`** — `MainWindow`, the app controller. Loads both data vaults, builds map markers
  from `REGISTRY` + JSON data, wires the menu/map/items screens together, and resolves loot
  item references. See "Data loading" below.
- **`interface.py`** — the Qt screens/dialogs: `MainMenu` (profile picker + lang toggle),
  `MapScreen` (sidebar with collapsible category filters, search, progress counters),
  `ItemsScreen` (two-tree item database browser with a details pane), `MarkerInfoWindow`
  (popup shown on marker click), `ItemTooltip` (renders a full item stat card), plus small
  reusable dialogs (`CollapsibleSection`, `CustomInputDialog`).
- **`components.py`** — the `QGraphicsScene`/`QGraphicsView` layer: `MapMarker` /
  `RegionMarker` (static data-driven markers, double-click to toggle "completed"),
  `UserWaypoint` (user-placed pins, right-click to add/remove), `InteractiveMapViewer`
  (pan/zoom viewport, layer switching, waypoint persistence).

## Data loading (two independent, differently-scoped loaders)

`DATA/` is organized by content type: `DATA/items/`, `DATA/locations/`, `DATA/enemies/`,
`DATA/key_items/`, `DATA/npc/`. Two different loaders read from it, with different scope and
different semantics — this asymmetry is a known source of bugs, be careful when touching
either:

- **`MainWindow._load_data_vault(lang)`** (marker data) — walks `DATA/` but explicitly
  `dirs.remove("items")` to skip the items folder, then resolves each `DATA_MANIFEST` entry by
  base filename (optionally with a `_<lang>` suffix) into `self.data_vault[key]`. This is what
  `REGISTRY`-driven marker placement (`_populate_markers` / `_add_markers_for_item`) reads from.
- **`MainWindow.load_items_database()`** (item lookup) — walks *all* of `DATA/` (not scoped to
  `DATA/items/`) and merges every JSON file's top-level dict into one flat `items_vault` via
  `dict.update()`. This currently pulls in non-item marker files too (their top-level keys like
  `surface`/`underground`/`dlc`/`Hub` end up as bogus "items" with no `name_ru`, showing up as
  "♦ Unknown" entries in `ItemsScreen`), and `dict.update()` silently lets same-named keys from
  different files clobber each other depending on `os.walk` order. If asked to fix or touch item
  loading, scope this loader to `DATA/items/` only (mirroring the `dirs.remove("items")` exclusion
  in the other loader) and consider warning on key collisions across files.

`items_vault` (from the second loader) is also used to resolve loot references: marker JSON can
list `loot_items: [...]` as either an item-id string (looked up in `items_vault`) or an inline
`{"ru": ..., "en": ...}` dict. See `MainWindow._resolve_loot_data` / `_resolve_item`.

### Localization field convention in JSON data

Data files store per-language fields as `<field>_<lang>` (e.g. `name_ru`, `name_en`,
`effects_ru`, `description_en`), with `_ru` typically used as the fallback when the current
language's field or the language-neutral field is missing. This resolution chain is duplicated
in `MainWindow._resolve_item` (main.py) and `ItemsScreen.on_item_clicked` (interface.py) —
when changing the fallback logic, update both.

### Marker IDs

A marker's persisted id is `pt["id"]` if present in the JSON, otherwise it's synthesized as
`f"{item_id}_{int(x)}_{int(y)}"` (or `f"wp_{int(x)}_{int(y)}"` for user waypoints). Synthesized
ids from nearby integer coordinates can collide across unrelated markers, corrupting saved
progress. Prefer adding explicit `"id"` fields in JSON over relying on the coordinate fallback
when adding new markers.

## Save data

Per-profile, JSON, written under `saves/`, keyed by a sanitized profile name
(`config.sanitize_profile_name` strips to `[A-Za-z0-9_-]`):
- `saves/settings.json` — `{"lang": "ru"|"en"}`, global (not per-profile).
- `saves/save_<profile>.json` — a JSON array (loaded as a `set`) of completed marker ids.
- `saves/waypoints_<profile>.json` — list of user-placed waypoints (`x`, `y`, `layer`, `icon`,
  `note`).

## Known issues / conventions to be aware of

- `REGISTRY` entries inconsistently use either a single `label` key or a `label_ru`/`label_en`
  pair — check which one an entry has before reading `meta["label"]` unconditionally (code
  generally does `meta.get(f"label_{lang}", meta.get("label_ru", "Unknown"))`).
- Some UI strings and heuristics in `interface.py` are hardcoded Russian rather than routed
  through `LOCALES` (e.g. profile create/delete dialog buttons, and the
  `"Cancel" if "Enter" in label_text else "Отмена"` language guess in `CustomInputDialog`).
- Each map layer is loaded as one full-resolution `QPixmap` (`InteractiveMapViewer.change_map`);
  switching layers repeatedly is memory-heavy since nothing is tiled or unloaded.
- Error handling throughout is `print(...)` plus broad `except Exception` rather than logging.
