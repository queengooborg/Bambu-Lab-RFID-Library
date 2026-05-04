# Bambu Lab RFID Library

> [!NOTE]
> If you enjoy this project and want to help with its maintenance, please consider supporting me via Ko-Fi!
>
> <a href='https://ko-fi.com/queengooborg' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi4.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

This repository contains a collection of RFID tag scans from Bambu Lab filament spools. The data can be used to create cloned tags for Bambu Lab printers or for research purposes.

For more information about Bambu Lab RFID tags and their format, see https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide.

## Tools

A collection of Python scripts is included in this repository to help scan, manage, and maintain the library. All scripts require **Python 3.6 or higher**.

> [!NOTE]
> Scripts that communicate with a Proxmark3 (`scanTag.py`, `writeTag.py`, `menu.py`) also require a Proxmark3 running the [Iceman firmware](https://github.com/RfidResearchGroup/proxmark3) (v4.21128 or higher). Set the `PROXMARK3_DIR` environment variable to your Proxmark3 installation directory (e.g. `D:\Proxmark3` on Windows).

---

### `menu.py` — Interactive menu (recommended entry point)

A text-based interactive menu that brings together all the common workflows in one place. No need to remember individual script names or arguments.

```
python menu.py
```

**Menu options:**

| Option | Description |
|--------|-------------|
| **1 — Read tag** | Poll for a tag, display all parsed fields (material, colour hex + name, variant ID, UID) and show its library location if already scanned. |
| **2 — Scan tag to database** | Full scan-and-add workflow: reads the tag, looks up the official colour name, prompts for confirmation, and saves to the library. |
| **3 — Write tag from database** | Browse the library by category → material → colour → UID and write the selected dump to a blank writable tag. |
| **4 — Fix database** | Check the library for misplaced entries, wrong colour folder names, and duplicate UIDs; review and apply fixes interactively; optionally update the README. |
| **5 — Sync from upstream** | Fetch new tag UIDs from the upstream repository ([queengooborg/Bambu-Lab-RFID-Library](https://github.com/queengooborg/Bambu-Lab-RFID-Library)), preview what's new, import with one confirmation, then optionally run Fix Database and update the README. |
| **6 — Contribute to upstream** | Find local UIDs not yet in upstream and create or update a single persistent PR (`contribute/pending`). The branch is rooted on `upstream/main` so no local naming changes bleed in. Re-run after each new scan to keep the PR current; a new PR is opened automatically once the previous one is merged or closed. |
| **7 — Exit** | Quit. |

The colour database is loaded once at startup and shared across all operations. The Proxmark3 is auto-detected on first use.

---

### `scanTag.py` — Scan a tag and add it to the library

Reads a Bambu Lab RFID tag using a Proxmark3 and adds the data to the library in the correct location.

```
python scanTag.py
```

**What it does:**

1. Waits for you to present a spool to the Proxmark3 (shows a spinner while searching).
2. Checks whether the tag's UID is already in the library and shows where, if so.
3. Derives the tag's sector keys from the UID (no sniffing required) and dumps all sectors.
4. Parses the dump and displays the material, colour hex, colour count, and variant ID.
5. Looks up the **official colour name** from Bambu Lab's colour database — fetched live from the [BambuStudio GitHub repository](https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/filament/filaments_color_codes.json) if available, with a fallback to a locally installed Bambu Studio copy.
6. Presents the official name as the default; warns if you type something different.
7. Saves the dump to the correct `Category/Material/Colour/UID/` folder and generates additional file formats (JSON, NFC).
8. Optionally updates the README status table.

---

### `writeTag.py` — Write a library dump to a blank tag

Writes an existing dump from the library to a blank writable RFID tag, allowing third-party spools to be recognised by Bambu Lab printers just like genuine spools.

```
python writeTag.py [path/to/uid/directory | path/to/dump.bin] [path/to/key.bin]
```

If no arguments are given the script will prompt for the paths. It displays the filament data that will be written and requires explicit confirmation before permanently write-locking the tag.

**Path arguments** are flexible — you can pass:
- A **UID directory** (e.g. `PLA/PLA Basic/Pink/47D3072A`) — the script finds the dump and key files inside automatically.
- A **dump file** path — the key file is found alongside it automatically.
- Both a dump file and a key file explicitly.

Both relative and absolute paths are accepted.

**Compatible blank tags:** Gen 2 FUID, Gen 4 FUID, Gen 4 UFUID. The script detects which type is on the reader and uses the appropriate write command.

---

### `parse.py` — Parse and display tag data

Parses a tag dump file (`.bin` or `.json`) and prints its contents in a human-readable format. Also writes a `.json` sidecar file alongside the dump.

```
python parse.py path/to/tag-dump.bin
```

---

### `fix_library.py` — Find and fix library issues

Scans all dump files and reports entries where the folder path doesn't match the material/category recorded in the tag data, colour folder names that don't match the official Bambu Lab name, and duplicate UIDs (the same physical tag filed in more than one location). With `--fix`, applies all approved changes automatically.

```
python fix_library.py [library_root] [--fix] [--quarantine] [--no-color-check]
```

| Flag | Effect |
|------|--------|
| *(none)* | Report all issues — nothing is moved. |
| `--fix` | Move misplaced folders, rename wrong colour folders, and remove duplicate copies. Colour renames are presented interactively for approval before anything is changed. |
| `--fix --quarantine` | Same as `--fix`, but entries with suspicious/corrupt tag data are moved to `_quarantine/` with a note instead of being placed in the main library. |
| `--no-color-check` | Skip the colour folder name validation (location fixes only). |

**What it checks:**

- **Location mismatches** — tag filed under the wrong category or material folder (e.g. a PETG HF tag under PETG Translucent).
- **Colour name mismatches** — colour folder name doesn't match the official Bambu Studio colour name for that hex code and material type. Cross-type tags (e.g. a "Silver" folder containing a PLA Silk+ tag when Silver is also valid for PLA Basic) are flagged with an explanatory note.
- **Duplicate UIDs** — the same UID appears in more than one library location. The duplicate copy is reported (and removed with `--fix`).

**One-pass location + colour fix:** when a tag needs both a location move *and* a colour rename, both changes are applied in a single `--fix` run. The colour rename destination is calculated relative to the post-move path, so the library is fully consistent after a single pass.

---

### `colordb.py` — Shared Bambu Studio colour database helper

Internal module used by `menu.py`, `scanTag.py`, and `fix_library.py` to look up official colour names from the Bambu Lab filament colour database.

Not normally run directly. The database is fetched live from the [BambuStudio GitHub repository](https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/filament/filaments_color_codes.json) on each run (5-second timeout), with an automatic fallback to a locally installed Bambu Studio copy.

**Key functions available to other scripts:**

| Function | Description |
|----------|-------------|
| `load_color_database()` | Fetch/load the colour database; returns a list of entries. |
| `lookup_color_name(tag_data, db)` | Return the official English colour name for a tag's hex colour + material type. Returns `(exact_name, candidates)` where `exact_name` is set only when both type and colour match precisely. |
| `find_nearest_color(tag_data, db)` | Find the closest colour by Euclidean RGBA distance when no exact hex match exists. |
| `distance_label(dist)` | Human-readable qualifier for a colour distance value. |

---

### `library_checker.py` — Check for errors and colour mismatches

Scans the library and reports:

- Tags that appear to be stored in the wrong category or material folder.
- Colour directories that contain tags with more than one distinct hex colour code.

```
python library_checker.py [--color_list] [--dump_colors]
```

---

### `sync_from_upstream.py` — Import new tags from the upstream repository

Compares the upstream repository ([queengooborg/Bambu-Lab-RFID-Library](https://github.com/queengooborg/Bambu-Lab-RFID-Library)) against your local library and imports any UID directories that are present upstream but absent locally. UIDs are matched by their 8-character hex name regardless of which colour/material folder they sit in, so tags that have been moved or renamed in your library are correctly recognised as already present.

```
python sync_from_upstream.py              # fetch upstream + preview new UIDs
python sync_from_upstream.py --apply      # fetch + import
python sync_from_upstream.py --no-fetch   # preview without re-fetching
python sync_from_upstream.py --no-fetch --apply   # import without re-fetching
```

The upstream remote is added automatically on first run. After importing, run the standard pipeline to normalise locations, names, and README status:

```
python fix_library.py --fix    # move imported files to correct location/name
python update_readme.py        # update ✅/❌ status icons
git add -A && git commit -m "Import N new tags from upstream" && git push
```

> [!NOTE]
> Imported files land at the upstream folder paths, which may differ from your naming conventions (e.g. `Blue Grey` vs `Blue Gray`, `Green` vs `Glow Green`). `fix_library.py` handles the correction automatically. Suspicious or corrupt tags reported by `fix_library` should be reviewed before committing.

---

### `contribute_to_upstream.py` — Contribute new tag scans back to the upstream repository

Finds UID directories that are in your local library but absent from the upstream repository ([queengooborg/Bambu-Lab-RFID-Library](https://github.com/queengooborg/Bambu-Lab-RFID-Library)), then creates or updates a single persistent pull-request branch containing all those new files. The branch is rooted on `upstream/main`, so none of your local naming convention changes are included in the PR.

```
python contribute_to_upstream.py              # fetch + preview what would be contributed
python contribute_to_upstream.py --apply      # fetch + create/update PR branch
python contribute_to_upstream.py --no-fetch   # preview without re-fetching
python contribute_to_upstream.py --no-fetch --apply
```

**Prerequisites:**

- [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated (`gh auth login`)
- Your fork pushed to `origin` on GitHub (standard setup)

**What it does (with `--apply`):**

1. Identifies all local UIDs not present in `upstream/main`.
2. Rebuilds the fixed branch `contribute/pending` from `upstream/main` in a temporary git worktree, leaving your working tree untouched.
3. Copies all new UID directories into the worktree and commits them.
4. Force-pushes the branch to your `origin` fork (`--force-with-lease`).
5. **If a PR is already open** from `contribute/pending`: updates its title and body to reflect the current UID count via `gh pr edit`.  
   **If no PR is open**: creates one against `queengooborg/Bambu-Lab-RFID-Library` via `gh pr create`.

Run it again after scanning more tags — the open PR accumulates everything until the upstream author merges or closes it, at which point the next run opens a fresh PR.

```
gh pr view --repo queengooborg/Bambu-Lab-RFID-Library
```

> [!NOTE]
> UIDs that have been quarantined by `fix_library.py` are automatically excluded from contributions.

---

### `update_readme.py` — Sync README status from actual library data

Scans the library and updates the ✅/❌ status icons and variant ID columns in this README to reflect what is actually on disk. Rows marked ⚠️ or ⏳ are left untouched (those statuses are set manually). Also warns if any ✅ row links to a colour folder that no longer exists on disk (e.g. after a rename).

```
python update_readme.py [library_root] [--dry-run]
```

---

### `convert.py` — Convert dump files to additional formats

Converts dumps in a UID directory to JSON and NFC formats, and normalises any non-standard filenames to the `hf-mf-<UID>-dump.bin` convention.

```
python convert.py path/to/uid/directory
```

---

### `repair.py` — Restore missing sector-trailer keys in a dump

Repairs dump files where the sector trailer keys have been zeroed out (which can happen when dumping with certain tools). Re-derives the correct keys from the UID using the Bambu KDF and writes them back in place.

```
python repair.py path/to/dump.bin
```

---

### `deriveKeys.py` — Derive sector keys for a given UID

Prints the 32 Bambu Lab sector keys (16 Key-A + 16 Key-B) for a tag UID. Useful for scripting or manual Proxmark3 operations.

```
python deriveKeys.py <UID in hex>
```

---

### `scrape_filaments.py` — Discover new filaments from the Bambu store

Scrapes the Bambu Lab online store to find filament types and colours not yet listed in this README, and generates the stub table rows ready for the next `update_readme.py` run.

```
python scrape_filaments.py
```

---

## Contributing

The best way to contribute is to scan tags and submit a Pull Request. The easiest workflow is:

1. Clone this repository.
2. Run `python menu.py` with a Proxmark3 attached and choose **2 — Scan tag to database**.
   - Alternatively, run `python scanTag.py` directly for a non-interactive scan.
3. Present each spool — the script scans the tag, looks up the official colour name, and saves the data in the right place automatically.
4. Run `python menu.py` and choose **6 — Contribute to upstream** (or run `python contribute_to_upstream.py --apply` directly).
   - This creates or updates a single persistent PR branch (`contribute/pending`) rooted on `upstream/main`, then opens or updates a pull request against this repository automatically via the GitHub CLI.
   - Run it again after scanning more spools — the PR accumulates all your un-merged tags in one place. A new PR is opened automatically once the previous one is merged or closed.
   - Requires the [GitHub CLI](https://cli.github.com/) (`gh auth login`).

Not sure how to set up a Proxmark3? See the [Bambu Lab RFID Tag Guide](https://github.com/NickWaterton/Bambu-Lab-RFID-Tag-Guide/blob/main/docs/ReadTags.md) for detailed instructions.

Tags are stored in the following folder structure: `Material Category` > `Material Name` > `Color Name` > `Tag UID` > `Tag Files`

## List of Bambu Lab Materials + Colors

Status Icon Legend:

- ✅: Have tag data
- ❌: No tag scanned
- ⚠️: See notes
- ⏳: Tag data is for an older version of material

### [PLA](./PLA)

#### [PLA Basic](./PLA/PLA%20Basic)

| Color                                                    | Filament Code | Variant ID            | Status |
| -------------------------------------------------------- | ------------- | --------------------- | ------ |
| [Orange](./PLA/PLA%20Basic/Orange)                       | 10300         | A00-A0/A00-A00/A00-A1 | ✅     |
| [Pumpkin Orange](./PLA/PLA%20Basic/Pumpkin%20Orange)     | 10301         | A00-A1                | ✅     |
| [Blue Gray](./PLA/PLA%20Basic/Blue%20Gray)               | 10602         | A00-B01/A00-B1        | ✅     |
| [Cobalt Blue](./PLA/PLA%20Basic/Cobalt%20Blue)           | 10604         | A00-B3                | ✅     |
| [Turquoise](./PLA/PLA%20Basic/Turquoise)                 | 10605         | A00-B5                | ✅     |
| [Cyan](./PLA/PLA%20Basic/Cyan)                           | 10603         | A00-B08/A00-B8        | ✅     |
| [Blue](./PLA/PLA%20Basic/Blue)                           | 10601         | A00-B09/A00-B9        | ✅     |
| [Gray](./PLA/PLA%20Basic/Gray)                           | 10103         | A00-D0/A00-D00        | ✅     |
| [Silver](./PLA/PLA%20Basic/Silver)                       | 10102         | A00-D01/A00-D1        | ✅     |
| [Light Gray](./PLA/PLA%20Basic/Light%20Gray)             | 10104         | A00-D02/A00-D2        | ✅     |
| [Dark Gray](./PLA/PLA%20Basic/Dark%20Gray)               | 10105         | A00-D03/A00-D3        | ✅     |
| [Green](./PLA/PLA%20Basic/Green)                         | 10500         | A00-G0                | ✅     |
| [Mistletoe Green](./PLA/PLA%20Basic/Mistletoe%20Green)   | 10502         | A00-G02/A00-G2        | ✅     |
| [Bright Green](./PLA/PLA%20Basic/Bright%20Green)         | 10503         | A00-G3                | ✅     |
| [Bambu Green](./PLA/PLA%20Basic/Bambu%20Green)           | 10501         | A00-G06/A00-G1/A00-G6 | ✅     |
| [Black](./PLA/PLA%20Basic/Black)                         | 10101         | A00-K0/A00-K00        | ✅     |
| [Brown](./PLA/PLA%20Basic/Brown)                         | 10800         | A00-N0                | ✅     |
| [Cocoa Brown](./PLA/PLA%20Basic/Cocoa%20Brown)           | 10802         | A00-N1                | ✅     |
| [Beige](./PLA/PLA%20Basic/Beige)                         | 10201         | A00-P0/A00-P00        | ✅     |
| [Pink](./PLA/PLA%20Basic/Pink)                           | 10203         | A00-A0/A00-P01/A00-P1 | ✅     |
| [Indigo Purple](./PLA/PLA%20Basic/Indigo%20Purple)       | 10701         | A00-P2                | ✅     |
| [Purple](./PLA/PLA%20Basic/Purple)                       | 10700         | A00-P05/A00-P5        | ✅     |
| [Magenta](./PLA/PLA%20Basic/Magenta)                     | 10202         | A00-P06/A00-P6        | ✅     |
| [Red](./PLA/PLA%20Basic/Red)                             | 10200         | A00-R0/A00-R00        | ✅     |
| [Maroon Red](./PLA/PLA%20Basic/Maroon%20Red)             | 10205         | A00-R2                | ✅     |
| [Hot Pink](./PLA/PLA%20Basic/Hot%20Pink)                 | 10204         | A00-R3                | ✅     |
| [Jade White](./PLA/PLA%20Basic/Jade%20White)             | 10100         | A00-W01/A00-W1        | ✅     |
| [Yellow](./PLA/PLA%20Basic/Yellow)                       | 10400         | A00-Y0/A00-Y00        | ✅     |
| [Sunflower Yellow](./PLA/PLA%20Basic/Sunflower%20Yellow) | 10402         | A00-Y2                | ✅     |
| [Bronze](./PLA/PLA%20Basic/Bronze)                       | 10801         | A00-Y03/A00-Y3        | ✅     |
| [Gold](./PLA/PLA%20Basic/Gold)                           | 10401         | A00-Y04/A00-Y4        | ✅     |

#### [PLA Lite](./PLA/PLA%20Lite)

| Color                                                   | Filament Code | Variant ID | Status |
| ------------------------------------------------------- | ------------- | ---------- | ------ |
| [Black](./PLA/PLA%20Lite/Black)                         | 16100         | A18-K0     | ✅     |
| [Yellow](./PLA/PLA%20Lite/Yellow)                       | 16400         | A18-Y0     | ✅     |
| [White](./PLA/PLA%20Lite/White)                         | 16103         | A18-W0     | ✅     |
| [Cyan](./PLA/PLA%20Lite/Cyan)                           | 16600         | A18-B0     | ✅     |
| [Red](./PLA/PLA%20Lite/Red)                             | 16200         | A18-R0     | ✅     |
| [Gray](./PLA/PLA%20Lite/Gray)                           | 16101         | A18-D0     | ✅     |
| [Blue](./PLA/PLA%20Lite/Blue)                           | 16601         | A18-B1     | ✅     |
| [Sunflower Yellow](./PLA/PLA%20Lite/Sunflower%20Yellow) | 16401         | ?          | ❌     |
| [Green](./PLA/PLA%20Lite/Green)                         | 16501         | ?          | ❌     |
| [Orange](./PLA/PLA%20Lite/Orange)                       | 16301         | ?          | ❌     |
| [Matte Beige](./PLA/PLA%20Lite/Matte%20Beige)           | 16700         | ?          | ❌     |
| [Cocoa Brown](./PLA/PLA%20Lite/Cocoa%20Brown)           | 16800         | ?          | ❌     |
| [Dark Gray](./PLA/PLA%20Lite/Dark%20Gray)               | 16102         | ?          | ❌     |

#### [PLA Matte](./PLA/PLA%20Matte)

| Color                                                  | Filament Code | Variant ID     | Status |
| ------------------------------------------------------ | ------------- | -------------- | ------ |
| [Mandarin Orange](./PLA/PLA%20Matte/Mandarin%20Orange) | 11300         | A01-A2         | ✅     |
| [Sky Blue](./PLA/PLA%20Matte/Sky%20Blue)               | 11603         | A01-B0         | ✅     |
| [Marine Blue](./PLA/PLA%20Matte/Marine%20Blue)         | 11600         | A01-B3         | ✅     |
| [Ice Blue](./PLA/PLA%20Matte/Ice%20Blue)               | 11601         | A01-B4         | ✅     |
| [Dark Blue](./PLA/PLA%20Matte/Dark%20Blue)             | 11602         | A01-B6         | ✅     |
| [Nardo Gray](./PLA/PLA%20Matte/Nardo%20Gray)           | 11104         | A01-D0         | ✅     |
| [Ash Gray](./PLA/PLA%20Matte/Ash%20Gray)               | 11102         | A01-D03/A01-D3 | ✅     |
| [Apple Green](./PLA/PLA%20Matte/Apple%20Green)         | 11502         | A01-G0         | ✅     |
| [Grass Green](./PLA/PLA%20Matte/Grass%20Green)         | 11500         | A01-G1         | ✅     |
| [Dark Green](./PLA/PLA%20Matte/Dark%20Green)           | 11501         | A01-G7         | ✅     |
| [Charcoal](./PLA/PLA%20Matte/Charcoal)                 | 11101         | A01-K01/A01-K1 | ✅     |
| [Dark Chocolate](./PLA/PLA%20Matte/Dark%20Chocolate)   | 11802         | A01-N0         | ✅     |
| [Latte Brown](./PLA/PLA%20Matte/Latte%20Brown)         | 11800         | A01-N1         | ✅     |
| [Dark Brown](./PLA/PLA%20Matte/Dark%20Brown)           | 11801         | A01-N2         | ✅     |
| [Caramel](./PLA/PLA%20Matte/Caramel)                   | 11803         | A01-N3         | ✅     |
| [Sakura Pink](./PLA/PLA%20Matte/Sakura%20Pink)         | 11201         | A01-P03/A01-P3 | ✅     |
| [Lilac Purple](./PLA/PLA%20Matte/Lilac%20Purple)       | 11700         | A01-P4         | ✅     |
| [Scarlet Red](./PLA/PLA%20Matte/Scarlet%20Red)         | 11200         | A01-R1         | ✅     |
| [Terracotta](./PLA/PLA%20Matte/Terracotta)             | 11203         | A01-R2         | ✅     |
| [Plum](./PLA/PLA%20Matte/Plum)                         | 11204         | A01-R3         | ✅     |
| [Dark Red](./PLA/PLA%20Matte/Dark%20Red)               | 11202         | A01-R4         | ✅     |
| [Ivory White](./PLA/PLA%20Matte/Ivory%20White)         | 11100         | A01-W02/A01-W2 | ✅     |
| [Bone White](./PLA/PLA%20Matte/Bone%20White)           | 11103         | A01-W3         | ✅     |
| [Lemon Yellow](./PLA/PLA%20Matte/Lemon%20Yellow)       | 11400         | A01-A2/A01-Y2  | ✅     |
| [Desert Tan](./PLA/PLA%20Matte/Desert%20Tan)           | 11401         | A01-Y3         | ✅     |

#### [PLA Basic Gradient](./PLA/PLA%20Basic%20Gradient)

| Color                                                                     | Filament Code | Variant ID | Status |
| ------------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Arctic Whisper](./PLA/PLA%20Basic%20Gradient/Arctic%20Whisper)           | 10900         | A00-M0     | ✅     |
| [Solar Breeze](./PLA/PLA%20Basic%20Gradient/Solar%20Breeze)               | 10901         | A00-M1     | ✅     |
| [Ocean to Meadow](./PLA/PLA%20Basic%20Gradient/Ocean%20to%20Meadow)       | 10902         | A00-M2     | ✅     |
| [Pink Citrus](./PLA/PLA%20Basic%20Gradient/Pink%20Citrus)                 | 10903         | A00-M3     | ✅     |
| [Mint Lime](./PLA/PLA%20Basic%20Gradient/Mint%20Lime)                     | 10904         | A00-M4     | ✅     |
| [Blueberry Bubblegum](./PLA/PLA%20Basic%20Gradient/Blueberry%20Bubblegum) | 10905         | A00-M5     | ✅     |
| [Dusk Glare](./PLA/PLA%20Basic%20Gradient/Dusk%20Glare)                   | 10906         | A00-M6     | ✅     |
| [Cotton Candy Cloud](./PLA/PLA%20Basic%20Gradient/Cotton%20Candy%20Cloud) | 10907         | A00-M7     | ✅     |

#### [PLA Glow](./PLA/PLA%20Glow)

| Color                                         | Filament Code | Variant ID | Status |
| --------------------------------------------- | ------------- | ---------- | ------ |
| [Glow Orange](./PLA/PLA%20Glow/Glow%20Orange) | 15300         | A12-A0     | ❌     |
| [Glow Blue](./PLA/PLA%20Glow/Glow%20Blue)     | 15600         | A12-B0     | ✅     |
| [Glow Green](./PLA/PLA%20Glow/Glow%20Green)   | 15500         | A12-G0     | ✅     |
| [Glow Pink](./PLA/PLA%20Glow/Glow%20Pink)     | 15200         | A12-R0     | ✅     |
| [Glow Yellow](./PLA/PLA%20Glow/Glow%20Yellow) | 15400         | A12-Y0     | ✅     |

#### [PLA Marble](./PLA/PLA%20Marble)

| Color                                             | Filament Code | Variant ID | Status |
| ------------------------------------------------- | ------------- | ---------- | ------ |
| [White Marble](./PLA/PLA%20Marble/White%20Marble) | 13103         | A07-D4     | ✅     |
| [Red Granite](./PLA/PLA%20Marble/Red%20Granite)   | 13201         | A07-R5     | ✅     |

#### [PLA Aero](./PLA/PLA%20Aero)

| Color                           | Filament Code | Variant ID | Status |
| ------------------------------- | ------------- | ---------- | ------ |
| [Gray](./PLA/PLA%20Aero/Gray)   | 14104         | ?          | ❌     |
| [Black](./PLA/PLA%20Aero/Black) | 14103         | A11-K0     | ✅     |
| [White](./PLA/PLA%20Aero/White) | 14102         | A11-W0     | ✅     |

#### [PLA Sparkle](./PLA/PLA%20Sparkle)

| Color                                                                | Filament Code | Variant ID     | Status |
| -------------------------------------------------------------------- | ------------- | -------------- | ------ |
| [Royal Purple Sparkle](./PLA/PLA%20Sparkle/Royal%20Purple%20Sparkle) | 13700         | A08-B7         | ✅     |
| [Slate Gray Sparkle](./PLA/PLA%20Sparkle/Slate%20Gray%20Sparkle)     | 13102         | A08-D5         | ✅     |
| [Alpine Green Sparkle](./PLA/PLA%20Sparkle/Alpine%20Green%20Sparkle) | 13501         | A08-G3         | ✅     |
| [Onyx Black Sparkle](./PLA/PLA%20Sparkle/Onyx%20Black%20Sparkle)     | 13101         | A08-K02/A08-K2 | ✅     |
| [Crimson Red Sparkle](./PLA/PLA%20Sparkle/Crimson%20Red%20Sparkle)   | 13200         | A08-R2         | ✅     |
| [Classic Gold Sparkle](./PLA/PLA%20Sparkle/Classic%20Gold%20Sparkle) | 13402         | A08-Y1         | ✅     |

#### [PLA Metal](./PLA/PLA%20Metal)

| Color                                                                | Filament Code | Variant ID | Status |
| -------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [Iron Gray Metallic](./PLA/PLA%20Metal/Iron%20Gray%20Metallic)       | 13100         | A02-D2     | ✅     |
| [Iridium Gold Metallic](./PLA/PLA%20Metal/Iridium%20Gold%20Metallic) | 13400         | A02-Y1     | ✅     |
| [Oxide Green Metallic](./PLA/PLA%20Metal/Oxide%20Green%20Metallic)   | 13500         | A02-G2     | ✅     |
| [Cobalt Blue Metallic](./PLA/PLA%20Metal/Cobalt%20Blue%20Metallic)   | 13600         | A02-B2     | ✅     |
| [Copper Brown Metallic](./PLA/PLA%20Metal/Copper%20Brown%20Metallic) | 13800         | A02-N3     | ✅     |

#### [PLA Translucent](./PLA/PLA%20Translucent)

| Color                                                    | Filament Code | Variant ID | Status |
| -------------------------------------------------------- | ------------- | ---------- | ------ |
| [Red](./PLA/PLA%20Translucent/Red)                       | 13210         | A17-R0     | ✅     |
| [Cherry Pink](./PLA/PLA%20Translucent/Cherry%20Pink)     | 13211         | A17-R1     | ✅     |
| [Orange](./PLA/PLA%20Translucent/Orange)                 | 13301         | A17-A0     | ✅     |
| [Mellow Yellow](./PLA/PLA%20Translucent/Mellow%20Yellow) | 13410         | A17-Y0     | ✅     |
| [Light Jade](./PLA/PLA%20Translucent/Light%20Jade)       | 13510         | A17-G0     | ✅     |
| [Ice Blue](./PLA/PLA%20Translucent/Ice%20Blue)           | 13610         | A17-B0     | ✅     |
| [Blue](./PLA/PLA%20Translucent/Blue)                     | 13611         | A17-B1     | ✅     |
| [Teal](./PLA/PLA%20Translucent/Teal)                     | 13612         | ?          | ❌     |
| [Purple](./PLA/PLA%20Translucent/Purple)                 | 13710         | A17-P0     | ✅     |
| [Lavender](./PLA/PLA%20Translucent/Lavender)             | 13711         | A17-P1     | ✅     |

#### [PLA Silk+](./PLA/PLA%20Silk%2B)

| Color                                            | Filament Code | Variant ID             | Status |
| ------------------------------------------------ | ------------- | ---------------------- | ------ |
| [Baby Blue](./PLA/PLA%20Silk%2B/Baby%20Blue)     | 13603         | A06-B0/A06-B00         | ✅     |
| [Blue](./PLA/PLA%20Silk%2B/Blue)                 | 13604         | A06-B01/A06-B1         | ✅     |
| [Titan Gray](./PLA/PLA%20Silk%2B/Titan%20Gray)   | 13108         | A06-D0/A06-D00         | ✅     |
| [Silver](./PLA/PLA%20Silk%2B/Silver)             | 13109         | A06-D00/A06-D01/A06-D1 | ✅     |
| [Candy Green](./PLA/PLA%20Silk%2B/Candy%20Green) | 13506         | A06-G0/A06-G00         | ✅     |
| [Mint](./PLA/PLA%20Silk%2B/Mint)                 | 13507         | A06-G01/A06-G1         | ✅     |
| [Purple](./PLA/PLA%20Silk%2B/Purple)             | 13702         | A06-P0/A06-P00         | ✅     |
| [Candy Red](./PLA/PLA%20Silk%2B/Candy%20Red)     | 13205         | A06-R0                 | ✅     |
| [Rose Gold](./PLA/PLA%20Silk%2B/Rose%20Gold)     | 13206         | A06-R01/A06-R1         | ✅     |
| [Pink](./PLA/PLA%20Silk%2B/Pink)                 | 13207         | A06-R2                 | ✅     |
| [White](./PLA/PLA%20Silk%2B/White)               | 13110         | A06-W0/A06-W00         | ✅     |
| [Champagne](./PLA/PLA%20Silk%2B/Champagne)       | 13404         | A06-Y0                 | ✅     |
| [Gold](./PLA/PLA%20Silk%2B/Gold)                 | 13405         | A06-Y1                 | ✅     |

#### [PLA Silk Multi-Color](./PLA/PLA%20Silk%20Multi-Color)

| Color                                                                                           | Filament Code | Variant ID    | Status |
| ----------------------------------------------------------------------------------------------- | ------------- | ------------- | ------ |
| [Gilded Rose](./PLA/PLA%20Silk%20Multi-Color/Gilded%20Rose)                                     | 13901         | A00-M1/A05-T1 | ✅     |
| [Midnight Blaze](./PLA/PLA%20Silk%20Multi-Color/Midnight%20Blaze)                               | 13902         | A05-T2/A05-T3 | ✅     |
| [Neon City](./PLA/PLA%20Silk%20Multi-Color/Neon%20City)                                         | 13903         | A05-M4/A05-T3 | ✅     |
| [Blue Hawaii](./PLA/PLA%20Silk%20Multi-Color/Blue%20Hawaii)                                     | 13904         | A05-T4        | ✅     |
| [Velvet Eclipse (Black-Red)](./PLA/PLA%20Silk%20Multi-Color/Velvet%20Eclipse%20%28Black-Red%29) | 13905         | A05-T5        | ✅     |
| [South Beach](./PLA/PLA%20Silk%20Multi-Color/South%20Beach)                                     | 13906         | A05-M1        | ✅     |
| [Aurora Purple](./PLA/PLA%20Silk%20Multi-Color/Aurora%20Purple)                                 | 13909         | A05-M4        | ✅     |
| [Dawn Radiance](./PLA/PLA%20Silk%20Multi-Color/Dawn%20Radiance)                                 | 13912         | A05-M8        | ✅     |
| [Mystic Magenta](./PLA/PLA%20Silk%20Multi-Color/Mystic%20Magenta)                               | 13913         | A05-T7        | ✅     |
| [Phantom Blue](./PLA/PLA%20Silk%20Multi-Color/Phantom%20Blue)                                   | 13916         | A05-T9        | ✅     |

#### [PLA Galaxy](./PLA/PLA%20Galaxy)

| Color                                 | Filament Code | Variant ID     | Status |
| ------------------------------------- | ------------- | -------------- | ------ |
| [Purple](./PLA/PLA%20Galaxy/Purple)   | 13602         | A15-B0         | ✅     |
| [Green](./PLA/PLA%20Galaxy/Green)     | 13503         | A15-G0         | ✅     |
| [Nebulae](./PLA/PLA%20Galaxy/Nebulae) | 13504         | A15-G01/A15-G1 | ✅     |
| [Brown](./PLA/PLA%20Galaxy/Brown)     | 13203         | A15-R0         | ✅     |

#### [PLA Wood](./PLA/PLA%20Wood)

| Color                                             | Filament Code | Variant ID    | Status |
| ------------------------------------------------- | ------------- | ------------- | ------ |
| [Classic Birch](./PLA/PLA%20Wood/Classic%20Birch) | 13505         | A16-G0        | ✅     |
| [Black Walnut](./PLA/PLA%20Wood/Black%20Walnut)   | 13107         | A16-K0/A16-R0 | ✅     |
| [Clay Brown](./PLA/PLA%20Wood/Clay%20Brown)       | 13801         | A16-N0        | ✅     |
| [Rosewood](./PLA/PLA%20Wood/Rosewood)             | 13204         | A16-R0        | ✅     |
| [White Oak](./PLA/PLA%20Wood/White%20Oak)         | 13106         | A16-W0        | ✅     |
| [Ochre Yellow](./PLA/PLA%20Wood/Ochre%20Yellow)   | 13403         | A16-Y0        | ✅     |

#### [PLA-CF](./PLA/PLA-CF)

| Color                                       | Filament Code | Variant ID | Status |
| ------------------------------------------- | ------------- | ---------- | ------ |
| [Royal Blue](./PLA/PLA-CF/Royal%20Blue)     | 14601         | A50-B6     | ❌     |
| [Jeans Blue](./PLA/PLA-CF/Jeans%20Blue)     | 14600         | ?          | ❌     |
| [Lava Gray](./PLA/PLA-CF/Lava%20Gray)       | 14101         | A50-D6     | ✅     |
| [Matcha Green](./PLA/PLA-CF/Matcha%20Green) | 14500         | ?          | ❌     |
| [Black](./PLA/PLA-CF/Black)                 | 14100         | A50-K0     | ✅     |
| [Iris Purple](./PLA/PLA-CF/Iris%20Purple)   | 14700         | ?          | ❌     |
| [Burgundy Red](./PLA/PLA-CF/Burgundy%20Red) | 14200         | ?          | ❌     |

#### [PLA Tough+](./PLA/PLA%20Tough%2B)

| Color                                 | Filament Code | Variant ID | Status |
| ------------------------------------- | ------------- | ---------- | ------ |
| [Black](./PLA/PLA%20Tough%2B/Black)   | 12104         | A10-K0     | ✅     |
| [Gray](./PLA/PLA%20Tough%2B/Gray)     | 12105         | A10-D0     | ✅     |
| [Silver](./PLA/PLA%20Tough%2B/Silver) | 12106         | A10-D1     | ✅     |
| [White](./PLA/PLA%20Tough%2B/White)   | 12107         | A10-W0     | ✅     |
| [Orange](./PLA/PLA%20Tough%2B/Orange) | 12301         | A10-A0     | ✅     |
| [Yellow](./PLA/PLA%20Tough%2B/Yellow) | 12401         | A10-Y0     | ✅     |
| [Cyan](./PLA/PLA%20Tough%2B/Cyan)     | 12601         | A10-B0     | ✅     |

#### [PLA Tough](./PLA/PLA%20Tough)

| Color                                              | Filament Code | Variant ID | Status |
| -------------------------------------------------- | ------------- | ---------- | ------ |
| [Orange](./PLA/PLA%20Tough/Orange)                 | 12300         | A09-A0     | ✅     |
| [Light Blue](./PLA/PLA%20Tough/Light%20Blue)       | 12600         | A09-B4     | ✅     |
| [Lavender Blue](./PLA/PLA%20Tough/Lavender%20Blue) | 12700         | A09-B5     | ✅     |
| [Gray](./PLA/PLA%20Tough/Gray)                     | 12102         | ?          | ❌     |
| [Silver](./PLA/PLA%20Tough/Silver)                 | 12103         | A09-D1     | ✅     |
| [Pine Green](./PLA/PLA%20Tough/Pine%20Green)       | 12500         | ?          | ❌     |
| [Black](./PLA/PLA%20Tough/Black)                   | 12101         | ?          | ❌     |
| [Vermilion Red](./PLA/PLA%20Tough/Vermilion%20Red) | 12200         | A09-R3     | ✅     |
| [White](./PLA/PLA%20Tough/White)                   | 12100         | ?          | ❌     |
| [Yellow](./PLA/PLA%20Tough/Yellow)                 | 12400         | A09-Y0     | ✅     |

### [PETG](./PETG)

#### [PETG Basic](./PETG/PETG%20Basic)

| Color                                            | Filament Code | Variant ID            | Status |
| ------------------------------------------------ | ------------- | --------------------- | ------ |
| [Black](./PETG/PETG%20Basic/Black)               | 30105         | G00-K0/G00-K00/G02-K0 | ✅     |
| [White](./PETG/PETG%20Basic/White)               | 30106         | G00-W0/G00-W00        | ✅     |
| [Gray](./PETG/PETG%20Basic/Gray)                 | 30107         | G00-D0/G00-D00        | ✅     |
| [Yellow](./PETG/PETG%20Basic/Yellow)             | 30402         | ?                     | ❌     |
| [Red](./PETG/PETG%20Basic/Red)                   | 30201         | G00-R0                | ✅     |
| [Reflex Blue](./PETG/PETG%20Basic/Reflex%20Blue) | 30603         | G00-B00               | ✅     |
| [Dark Brown](./PETG/PETG%20Basic/Dark%20Brown)   | 30800         | G00-N00               | ✅     |
| [Green](./PETG/PETG%20Basic/Green)               | 30502         | ?                     | ❌     |
| [Orange](./PETG/PETG%20Basic/Orange)             | 30301         | ?                     | ❌     |
| [Pine Green](./PETG/PETG%20Basic/Pine%20Green)   | 30503         | ?                     | ❌     |
| [Navy Blue](./PETG/PETG%20Basic/Navy%20Blue)     | 30604         | ?                     | ❌     |
| [Misty Blue](./PETG/PETG%20Basic/Misty%20Blue)   | 30108         | ?                     | ❌     |
| [Dark Beige](./PETG/PETG%20Basic/Dark%20Beige)   | 30403         | ?                     | ❌     |

#### [PETG HF](./PETG/PETG%20HF)

| Color                                           | Filament Code | Variant ID | Status |
| ----------------------------------------------- | ------------- | ---------- | ------ |
| [Orange](./PETG/PETG%20HF/Orange)               | 33300         | G02-A0     | ✅     |
| [Blue](./PETG/PETG%20HF/Blue)                   | 33600         | G02-B0     | ✅     |
| [Lake Blue](./PETG/PETG%20HF/Lake%20Blue)       | 33601         | G02-B1     | ✅     |
| [Gray](./PETG/PETG%20HF/Gray)                   | 33101         | G02-D0     | ✅     |
| [Dark Gray](./PETG/PETG%20HF/Dark%20Gray)       | 33103         | G02-D1     | ✅     |
| [Green](./PETG/PETG%20HF/Green)                 | 33500         | G02-G0     | ✅     |
| [Lime Green](./PETG/PETG%20HF/Lime%20Green)     | 33501         | G02-G1     | ✅     |
| [Forest Green](./PETG/PETG%20HF/Forest%20Green) | 33502         | G02-G2     | ✅     |
| [Black](./PETG/PETG%20HF/Black)                 | 33102         | G02-K0     | ✅     |
| [Peanut Brown](./PETG/PETG%20HF/Peanut%20Brown) | 33801         | G02-N1     | ✅     |
| [Red](./PETG/PETG%20HF/Red)                     | 33200         | G02-R0     | ✅     |
| [White](./PETG/PETG%20HF/White)                 | 33100         | G02-W0     | ✅     |
| [Yellow](./PETG/PETG%20HF/Yellow)               | 33400         | G02-Y0     | ✅     |
| [Cream](./PETG/PETG%20HF/Cream)                 | 33401         | G02-Y1     | ✅     |

#### [PETG Translucent](./PETG/PETG%20Translucent)

| Color                                                                          | Filament Code | Variant ID    | Status |
| ------------------------------------------------------------------------------ | ------------- | ------------- | ------ |
| [Translucent Orange](./PETG/PETG%20Translucent/Translucent%20Orange)           | 32300         | G01-A0/G02-A0 | ✅     |
| [Translucent Light Blue](./PETG/PETG%20Translucent/Translucent%20Light%20Blue) | 32600         | G01-B0        | ✅     |
| [Clear](./PETG/PETG%20Translucent/Clear)                                       | 32101         | G01-C0        | ✅     |
| [Translucent Gray](./PETG/PETG%20Translucent/Translucent%20Gray)               | 32100         | G01-D0        | ✅     |
| [Translucent Olive](./PETG/PETG%20Translucent/Translucent%20Olive)             | 32500         | G01-G0        | ✅     |
| [Translucent Teal](./PETG/PETG%20Translucent/Translucent%20Teal)               | 32501         | G01-G1        | ✅     |
| [Translucent Brown](./PETG/PETG%20Translucent/Translucent%20Brown)             | 32800         | G01-N0        | ✅     |
| [Translucent Purple](./PETG/PETG%20Translucent/Translucent%20Purple)           | 32700         | G01-P0        | ✅     |
| [Translucent Pink](./PETG/PETG%20Translucent/Translucent%20Pink)               | 32200         | G01-P1        | ✅     |

#### [PETG-CF](./PETG/PETG%20CF)

| Color                                                 | Filament Code | Variant ID | Status |
| ----------------------------------------------------- | ------------- | ---------- | ------ |
| [Indigo Blue](./PETG/PETG%20CF/Indigo%20Blue)         | 31600         | G50-B6     | ✅     |
| [Titan Gray](./PETG/PETG%20CF/Titan%20Gray)           | 31101         | G50-D6     | ✅     |
| [Malachite Green](./PETG/PETG%20CF/Malachite%20Green) | 31500         | G50-G7     | ✅     |
| [Black](./PETG/PETG%20CF/Black)                       | 31100         | G50-K0     | ✅     |
| [Violet Purple](./PETG/PETG%20CF/Violet%20Purple)     | 31700         | G50-P7     | ✅     |
| [Brick Red](./PETG/PETG%20CF/Brick%20Red)             | 31200         | G50-R4     | ✅     |

### [ABS](./ABS)

#### [ABS](./ABS/ABS)

| Color                                            | Filament Code | Variant ID     | Status |
| ------------------------------------------------ | ------------- | -------------- | ------ |
| [Orange](./ABS/ABS/Orange)                       | 40300         | B00-A0         | ✅     |
| [Blue](./ABS/ABS/Blue)                           | 40600         | B00-B0         | ✅     |
| [Azure](./ABS/ABS/Azure)                         | 40601         | B00-B4         | ✅     |
| [Navy Blue](./ABS/ABS/Navy%20Blue)               | 40602         | B00-B6         | ✅     |
| [Mint](./ABS/ABS/Mint)                           | 40501         | ?              | ❌     |
| [Silver](./ABS/ABS/Silver)                       | 40102         | B00-D1         | ✅     |
| [Bambu Green](./ABS/ABS/Bambu%20Green)           | 40500         | B00-G6         | ✅     |
| [Olive](./ABS/ABS/Olive)                         | 40502         | B00-G7         | ✅     |
| [Black](./ABS/ABS/Black)                         | 40101         | B00-K0         | ✅     |
| [Lavender](./ABS/ABS/Lavender)                   | 40701         | ?              | ❌     |
| [Purple](./ABS/ABS/Purple)                       | 40700         | ?              | ❌     |
| [Red](./ABS/ABS/Red)                             | 40200         | B00-R0         | ✅     |
| [White](./ABS/ABS/White)                         | 40100         | B00-W0/B00-W00 | ✅     |
| [Yellow](./ABS/ABS/Yellow)                       | 40400         | ?              | ❌     |
| [Tangerine Yellow](./ABS/ABS/Tangerine%20Yellow) | 40402         | B00-Y1         | ✅     |
| [Beige](./ABS/ABS/Beige)                         | 40401         | B00-Y0         | ✅     |

#### [ABS-GF](./ABS/ABS-GF)

| Color                         | Filament Code | Variant ID | Status |
| ----------------------------- | ------------- | ---------- | ------ |
| [Orange](./ABS/ABS-GF/Orange) | 41300         | B50-A0     | ✅     |
| [Blue](./ABS/ABS-GF/Blue)     | 41600         | ?          | ❌     |
| [Gray](./ABS/ABS-GF/Gray)     | 41102         | ?          | ❌     |
| [Green](./ABS/ABS-GF/Green)   | 41500         | ?          | ❌     |
| [Black](./ABS/ABS-GF/Black)   | 41101         | B50-K0     | ✅     |
| [Red](./ABS/ABS-GF/Red)       | 41200         | B50-R0     | ❌     |
| [White](./ABS/ABS-GF/White)   | 41100         | B50-W0     | ❌     |
| [Yellow](./ABS/ABS-GF/Yellow) | 41400         | ?          | ❌     |

### [ASA](./ASA)

#### [ASA](./ASA/ASA)

| Color                    | Filament Code | Variant ID | Status |
| ------------------------ | ------------- | ---------- | ------ |
| [Blue](./ASA/ASA/Blue)   | 45600         | B01-B0     | ✅     |
| [Gray](./ASA/ASA/Gray)   | 45102         | B01-D0     | ✅     |
| [Green](./ASA/ASA/Green) | 45500         | B01-G0     | ✅     |
| [Black](./ASA/ASA/Black) | 45101         | B01-K0     | ✅     |
| [Red](./ASA/ASA/Red)     | 45200         | B01-R0     | ✅     |
| [White](./ASA/ASA/White) | 45100         | B01-W0     | ✅     |

#### [ASA Aero](./ASA/ASA%20Aero)

| Color                           | Filament Code | Variant ID | Status |
| ------------------------------- | ------------- | ---------- | ------ |
| [White](./ASA/ASA%20Aero/White) | 46100         | B02-W0     | ✅     |

#### [ASA-CF](./ASA/ASA-CF)

| Color                       | Filament Code | Variant ID | Status |
| --------------------------- | ------------- | ---------- | ------ |
| [Black](./ASA/ASA-CF/Black) | 46101         | B51-K0     | ✅     |

### [PC](./PC)

#### [PC](./PC/PC)

| Color                                | Filament Code | Variant ID    | Status |
| ------------------------------------ | ------------- | ------------- | ------ |
| [Clear Black](./PC/PC/Clear%20Black) | 60102         | C00-C0/C00-C1 | ✅     |
| [Transparent](./PC/PC/Transparent)   | 60103         | C00-C1        | ✅     |
| [Black](./PC/PC/Black)               | 60101         | C00-K0        | ✅     |
| [White](./PC/PC/White)               | 60100         | C00-W0        | ✅     |

#### [PC FR](./PC/PC%20FR)

| Color                       | Filament Code | Variant ID | Status |
| --------------------------- | ------------- | ---------- | ------ |
| [Gray](./PC/PC%20FR/Gray)   | 63102         | C01-D0     | ✅     |
| [Black](./PC/PC%20FR/Black) | 63100         | C01-K0     | ✅     |
| [White](./PC/PC%20FR/White) | 63101         | C01-W0     | ✅     |

### [TPU](./TPU)

#### [TPU for AMS](./TPU/TPU%20for%20AMS)

| Color                                            | Filament Code | Variant ID | Status |
| ------------------------------------------------ | ------------- | ---------- | ------ |
| [Blue](./TPU/TPU%20for%20AMS/Blue)               | 53600         | U02-B0     | ✅     |
| [Gray](./TPU/TPU%20for%20AMS/Gray)               | 53102         | U02-D0     | ✅     |
| [Neon Green](./TPU/TPU%20for%20AMS/Neon%20Green) | 53500         | U02-G0     | ✅     |
| [Black](./TPU/TPU%20for%20AMS/Black)             | 53101         | U02-K0     | ✅     |
| [Red](./TPU/TPU%20for%20AMS/Red)                 | 53200         | ?          | ❌     |
| [White](./TPU/TPU%20for%20AMS/White)             | 53100         | ?          | ❌     |
| [Yellow](./TPU/TPU%20for%20AMS/Yellow)           | 53400         | ?          | ❌     |

### [PA](./PA)

#### [PAHT-CF](./PA/PAHT-CF)

| Color                       | Filament Code | Variant ID | Status |
| --------------------------- | ------------- | ---------- | ------ |
| [Black](./PA/PAHT-CF/Black) | 70100         | N04-K0     | ✅     |

#### [PA6-GF](./PA/PA6-GF)

| Color                        | Filament Code | Variant ID | Status |
| ---------------------------- | ------------- | ---------- | ------ |
| [Blue](./PA/PA6-GF/Blue)     | 72600         | ?          | ❌     |
| [White](./PA/PA6-GF/White)   | 72102         | N08-D0     | ✅     |
| [Gray](./PA/PA6-GF/Gray)     | 72103         | ?          | ❌     |
| [Lime](./PA/PA6-GF/Lime)     | 72500         | ?          | ❌     |
| [Black](./PA/PA6-GF/Black)   | 72104         | N08-K0     | ✅     |
| [Brown](./PA/PA6-GF/Brown)   | 72800         | ?          | ❌     |
| [Orange](./PA/PA6-GF/Orange) | 72200         | ?          | ❌     |
| [Yellow](./PA/PA6-GF/Yellow) | 72400         | ?          | ❌     |

### [Support Material](./Support%20Material)

#### [Support for PLA/PETG](./Support%20Material/Support%20for%20PLA-PETG)

| Color                                                          | Filament Code | Variant ID    | Status |
| -------------------------------------------------------------- | ------------- | ------------- | ------ |
| [Nature](./Support%20Material/Support%20for%20PLA-PETG/Nature) | 65102         | S05-C0        | ✅     |
| [Black](./Support%20Material/Support%20for%20PLA-PETG/Black)   | 65103         | S05-C0/S05-K0 | ✅     |

#### [Support for PLA (New Version)](./Support%20Material/Support%20for%20PLA%20%28New%20Version%29)

| Color                                                                         | Filament Code | Variant ID | Status |
| ----------------------------------------------------------------------------- | ------------- | ---------- | ------ |
| [White](./Support%20Material/Support%20for%20PLA%20%28New%20Version%29/White) | 65104         | S02-W1     | ✅     |

#### [Support for ABS](./Support%20Material/Support%20for%20ABS)

| Color                                                   | Filament Code | Variant ID | Status |
| ------------------------------------------------------- | ------------- | ---------- | ------ |
| [White](./Support%20Material/Support%20for%20ABS/White) | 66100         | S06-W0     | ✅     |

#### [Support for PA/PET](./Support%20Material/Support%20for%20PA-PET)

| Color                                                      | Filament Code | Variant ID    | Status |
| ---------------------------------------------------------- | ------------- | ------------- | ------ |
| [Green](./Support%20Material/Support%20for%20PA-PET/Green) | 65500         | S01-G1/S03-G1 | ✅     |

#### [PVA](./Support%20Material/PVA)

| Color                                   | Filament Code | Variant ID | Status |
| --------------------------------------- | ------------- | ---------- | ------ |
| [Clear](./Support%20Material/PVA/Clear) | 66400         | S04-Y0     | ✅     |

## History

When Bambu Lab released the AMS for their 3D printers, it featured an RFID reader which could read RFID tags embedded on their filament spools to automatically update details such as material type, color and amount of remaining filament. However, the RFID tags were read-protected by keys, signed with an RSA2048 signature and structured in a proprietary format, which meant that only Bambu Lab could create these particular RFID tags and they could only be used on Bambu Lab printers. This led to the start of the [Bambu Research Group and a project to reverse engineer the RFID tag format](https://github.com/queengooborg/Bambu-Lab-RFID-Tag-Guide) in order to develop an open standard for all filament manufacturers and printers.

Of course, to research the tag format, a lot of tag data was required. This led to a community effort to scan lots of tags and cross-reference the data with known details about each spool. Eventually, enough of the format was reverse engineered to be able to determine what an open standard would need. But, the tag scanning didn't stop there, as the community realized another benefit to the collection of tags: even though custom tags couldn't be created due to the signing of the data, the data could be _cloned_ onto new tags and used to tell Bambu Lab printers what material and color a spool was, just like Bambu Lab first-party spools.

Originally, the collection of scanned tags was kept private as the research group was not sure if Bambu Lab would react negatively to sniffing data transfers to obtain hidden keys. However, as time progressed and new methods were discovered to obtain tag data, the group slowly opened up the tag collection and made it easier to access, until eventually it became the consensus to create this repository.
