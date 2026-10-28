# -*- coding: utf-8 -*-

# Simple text-based menu for the Bambu Lab RFID Library tools.
# Run from the Bambu-Lab-RFID-Library directory.
#
# Usage:
#   python menu.py

import os
import re
import sys
import time
import itertools
import subprocess
import tempfile
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — ensure we can import sibling modules
# ---------------------------------------------------------------------------

LIBRARY_ROOT = Path(__file__).parent.resolve()

from lib import get_proxmark3_location, run_command
from deriveKeys import kdf
from categories import resolve_material
from parse import Tag
from colordb import load_color_database, lookup_color_name, find_nearest_color, distance_label
from update_readme import run as update_readme
import scanTag
import writeTag
import fix_library
import sync_from_upstream
import contribute_to_upstream

# ---------------------------------------------------------------------------
# Session-level state (initialised once at startup)
# ---------------------------------------------------------------------------

_pm3_location = None
_pm3_command  = "bin/pm3"
_color_db     = None   # loaded once in main()


def _get_pm3():
    global _pm3_location
    if _pm3_location is None:
        _pm3_location = get_proxmark3_location()
        if not _pm3_location:
            print("Error: Proxmark3 not found. Set PROXMARK3_DIR or install to the default path.")
            return None
    return _pm3_location


# ---------------------------------------------------------------------------
# Shared UI helpers
# ---------------------------------------------------------------------------

def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def _banner(title):
    print("=" * 56)
    print(f"  Bambu Lab RFID Library — {title}")
    print("=" * 56)
    print()


def _pause():
    input("\nPress Enter to return to the menu...")


def _pick(prompt, options, allow_back=True):
    """
    Display a numbered list and return the chosen index (0-based).
    Returns None if the user chooses 'back'.
    options: list of strings.
    """
    while True:
        for i, opt in enumerate(options, 1):
            print(f"  {i:>3}.  {opt}")
        if allow_back:
            print("    0.  Back")
        print()
        raw = input(f"{prompt} [0–{len(options)}]: ").strip()
        if allow_back and raw == '0':
            return None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        print("  Invalid choice, please try again.\n")


# ---------------------------------------------------------------------------
# Option 1 — Read a tag (display only, no library changes)
# ---------------------------------------------------------------------------

def _poll_uid_silent(pm3):
    """Try once to read a UID without printing anything. Returns UID string or None."""
    try:
        result = subprocess.run(
            [str(pm3 / _pm3_command), "-c", "hf mf info"],
            shell=(os.name == 'nt'),
            capture_output=True,
            timeout=12,
        )
        if result.returncode in (0, 1):
            output = result.stdout.decode('utf-8', errors='replace')
            m = re.search(r'\[\+\]\s+UID:\s+((?:[0-9A-Fa-f]{2}\s*)+)', output)
            if m:
                return m.group(1).replace(' ', '').strip().upper()
    except Exception:
        pass
    return None


def menu_read_tag():
    _clear()
    _banner("Read Tag")

    pm3 = _get_pm3()
    if not pm3:
        _pause()
        return

    print("Move the spool slowly over the Proxmark3 until the tag is detected.")
    print("(Ctrl+C to cancel)\n")

    # Wait for tag
    spinner = itertools.cycle('|/-\\')
    uid = None
    try:
        while True:
            print(f"\r  Searching... {next(spinner)}", end='', flush=True)
            uid = _poll_uid_silent(pm3)
            if uid:
                print(f"\r  Tag detected! UID: {uid}          ")
                break
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        _pause()
        return

    print(f"\nDeriving keys from UID {uid}...")
    uid_bytes = bytes.fromhex(uid)
    keys_a, keys_b = kdf(uid_bytes)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir    = Path(tmpdir)
        base_name = f"hf-mf-{uid}"
        key_path  = tmpdir / f"{base_name}-key.bin"
        dump_base = tmpdir / base_name

        # Write key file
        with open(key_path, 'wb') as f:
            for k in keys_a:
                f.write(k)
            for k in keys_b:
                f.write(k)

        # Dump
        print("Reading tag sectors...")
        kp       = str(key_path).replace('\\', '/')
        rel_name = base_name
        client_dir = pm3 / "client"

        run_command([pm3 / _pm3_command, "-c",
                     f"hf mf dump --1k --keys {kp} -f {rel_name}"])

        dump_file = None
        for suffix in ("-dump.bin", ".bin"):
            src = client_dir / f"{rel_name}{suffix}"
            if src.exists():
                dest = Path(str(dump_base) + suffix)
                shutil.move(str(src), dest)
                dump_file = dest
                break

        if not dump_file:
            print("\nError: could not read tag. Is it a Bambu Lab tag?")
            _pause()
            return

        # Parse
        try:
            with open(dump_file, 'rb') as f:
                tag = Tag(dump_file.name, f.read(), fail_on_warn=False)
        except Exception as e:
            print(f"\nError parsing tag: {e}")
            _pause()
            return

    # Display
    print()
    print("─" * 48)
    data = tag.data
    resolved = resolve_material(data)
    raw      = data['detailed_filament_type']
    mat_display = f"{resolved} (tag: {raw})" if resolved != raw else resolved

    # Check library for known entry
    existing = scanTag.find_existing_entries(uid, LIBRARY_ROOT)

    # --- Colour name lookup ---
    colour_label = data['filament_color']
    colour_note  = None
    if _color_db:
        exact_name, candidates = lookup_color_name(data, _color_db)
        if exact_name:
            colour_label = f"{exact_name}  ({data['filament_color']})"
        elif candidates:
            # Hex matched but under a different material type
            name, ftype = candidates[0]
            colour_label = f"{name}  ({data['filament_color']})"
            colour_note  = f"matched by hex only — database type is '{ftype}'"
        else:
            # No exact hex match — show nearest
            near_name, near_hex, near_dist, _, _ = find_nearest_color(data, _color_db)
            if near_name is not None:
                colour_label = f"~{near_name}  ({data['filament_color']})"
                colour_note  = f"nearest match: {near_hex}, distance {near_dist:.1f} — {distance_label(near_dist)}"

    print(f"  UID:        {uid}")
    print(f"  Material:   {mat_display} ({data['filament_type']})")
    print(f"  Colour:     {colour_label} ({data['filament_color_count']} colour(s))")
    if colour_note:
        print(f"              ⚠  {colour_note}")
    print(f"  Variant ID: {data['variant_id']}")
    if existing:
        rel = existing[0].relative_to(LIBRARY_ROOT)
        # Colour name is the 3rd level folder (category/material/colour/uid)
        colour_name = rel.parts[2] if len(rel.parts) >= 3 else "?"
        print(f"  Library:    {colour_name}  [{rel}]")
    else:
        print(f"  Library:    not in database")
    if tag.warnings:
        print()
        print("  Warnings:")
        for w in tag.warnings:
            print(f"    ⚠  {w}")
    print("─" * 48)

    _pause()


# ---------------------------------------------------------------------------
# Option 2 — Scan tag to database  (delegates to scanTag.main)
# ---------------------------------------------------------------------------

def menu_scan_tag():
    _clear()
    _banner("Scan Tag to Database")
    # scanTag.main() handles everything including its own prompts
    try:
        scanTag.main()
    except SystemExit:
        pass
    _pause()


# ---------------------------------------------------------------------------
# Option 3 — Write tag from database
# ---------------------------------------------------------------------------

def _walk_library():
    """
    Walk the library and return a nested dict:
      { category: { material: { colour: { uid: Path } } } }
    Only includes directories at depth 4 (category/material/colour/uid).
    """
    tree = {}
    for uid_dir in LIBRARY_ROOT.rglob('*'):
        if not uid_dir.is_dir():
            continue
        parts = uid_dir.relative_to(LIBRARY_ROOT).parts
        if len(parts) != 4:
            continue
        cat, mat, col, uid = parts
        if cat.startswith('_'):
            continue
        # Must contain a dump file to be usable
        if not any(uid_dir.glob('*-dump.bin')):
            continue
        tree.setdefault(cat, {}).setdefault(mat, {}).setdefault(col, {})[uid] = uid_dir
    return tree


def menu_write_tag():
    _clear()
    _banner("Write Tag from Database")

    pm3 = _get_pm3()
    if not pm3:
        _pause()
        return

    print("Loading library...\n")
    tree = _walk_library()
    if not tree:
        print("Library appears to be empty.")
        _pause()
        return

    # --- Step 1: pick category ---
    categories = sorted(tree)
    print("Select a category:\n")
    idx = _pick("Category", categories)
    if idx is None:
        return
    cat = categories[idx]

    # --- Step 2: pick material ---
    _clear()
    _banner("Write Tag from Database")
    print(f"Category: {cat}\n")
    materials = sorted(tree[cat])
    print("Select a material:\n")
    idx = _pick("Material", materials)
    if idx is None:
        return
    mat = materials[idx]

    # --- Step 3: pick colour ---
    _clear()
    _banner("Write Tag from Database")
    print(f"Category: {cat}  /  Material: {mat}\n")
    colours = sorted(tree[cat][mat])
    print("Select a colour:\n")
    idx = _pick("Colour", colours)
    if idx is None:
        return
    col = colours[idx]

    # --- Step 4: pick UID ---
    _clear()
    _banner("Write Tag from Database")
    print(f"Category: {cat}  /  Material: {mat}  /  Colour: {col}\n")
    uids = sorted(tree[cat][mat][col])
    if len(uids) == 1:
        uid = uids[0]
        uid_dir = tree[cat][mat][col][uid]
        print(f"One entry found: {uid}")
    else:
        print("Select a UID:\n")
        idx = _pick("UID", uids)
        if idx is None:
            return
        uid = uids[idx]
        uid_dir = tree[cat][mat][col][uid]

    # --- Resolve dump and key ---
    try:
        tagdump, keydump = writeTag.resolve_dump_and_key(str(uid_dir))
    except ValueError as e:
        print(f"\nError: {e}")
        _pause()
        return

    if keydump is None or not Path(keydump).is_file():
        print(f"\nError: key file not found in {uid_dir}")
        _pause()
        return

    if not Path(tagdump).is_file():
        print(f"\nError: dump file not found in {uid_dir}")
        _pause()
        return

    # --- Delegate to writeTag internals ---
    _clear()
    _banner("Write Tag from Database")

    print()
    summary = writeTag.parse_dump_summary(tagdump)
    if summary:
        print("Filament data that will be written to the tag:")
        print(f"  Material:   {summary['material_name']} ({summary['filament_type']})")
        print(f"  Colour:     {col} ({summary['color']})")
        print(f"  Variant ID: {summary['variant_id']}")
        print(f"  Tag UID:    {summary['uid']}")
        print()
        confirm = input("Is this the correct filament? (y/N) ").strip()
        if confirm.lower() not in ('y', 'yes'):
            print("Cancelled.")
            _pause()
            return
        print()

    print("Place your Proxmark3 onto the blank tag you wish to write,")
    print("then press Enter.")
    input()

    # Temporarily redirect writeTag's global pm3 state
    writeTag.pm3Location = pm3

    try:
        tagtype = writeTag.getTagType()
    except RuntimeError as e:
        print(f"\nError: {e}")
        _pause()
        return

    print()
    print("=========== WARNING! == WARNING! == WARNING! ===========")
    print("This script will write the contents of a dump to your")
    print("RFID tag, and then PERMANENTLY WRITE LOCK the tag.")
    print("")
    print("This process is IRREVERSIBLE, proceed at your own risk.")
    print("========================================================")
    print()

    confirm = input("Are you SURE you wish to continue? (y/N) ").strip()
    if confirm.lower() not in ('y', 'yes'):
        print("Cancelled.")
        _pause()
        return

    print("Writing tag data now...")
    writeTag.writeTag(tagdump, keydump, tagtype)

    print()
    print("Writing complete! Your tag should now register on the AMS.")

    _pause()


# ---------------------------------------------------------------------------
# Option 4 — Fix database  (delegates to fix_library)
# ---------------------------------------------------------------------------

def menu_fix_database():
    _clear()
    _banner("Fix Database")

    print("Scanning library for issues...\n")
    mismatches, parse_errors, duplicates = fix_library.scan_library(LIBRARY_ROOT, _color_db)

    if parse_errors:
        print(f"{len(parse_errors)} file(s) failed to parse:")
        for path, err in parse_errors:
            print(f"  [!] {path}: {err}")
        print()

    if not mismatches and not duplicates:
        print("No issues found — library is correctly organised.")
        _pause()
        return

    location_mismatches = [m for m in mismatches if m['type'] == 'location']
    colour_mismatches   = [m for m in mismatches if m['type'] == 'colour_name']
    normal_loc  = [m for m in location_mismatches if not m['warning']]
    suspect_loc = [m for m in location_mismatches if m['warning']]

    if normal_loc:
        print(f"{len(normal_loc)} misplaced folder(s):\n")
        for m in normal_loc:
            print(f"  {m['rel_current']}")
            print(f"    -> {m['rel_expected']}  ({m['tag_cat']} / {m['tag_mat']})")

    if suspect_loc:
        print(f"\n{len(suspect_loc)} suspicious entry(s):\n")
        for m in suspect_loc:
            print(f"  {m['rel_current']}")
            print(f"    -> {m['rel_expected']}")
            print(f"    [!] {m['warning']}")

    if colour_mismatches:
        print(f"\n{len(colour_mismatches)} wrong colour folder name(s):\n")
        fix_library._colour_mismatch_summary(colour_mismatches)

    if duplicates:
        print(f"\n{len(duplicates)} duplicate UID(s) — resolve manually:\n")
        for uid, paths in sorted(duplicates.items()):
            print(f"  {uid}  ({len(paths)} copies)")
            for p in paths:
                print(f"    {p.relative_to(LIBRARY_ROOT)}")

    print()
    if not mismatches:
        # Only duplicates — nothing to auto-fix.
        print("Duplicate UIDs must be resolved manually (keep one copy, delete the other).")
        _pause()
        return

    print("Options:")
    if colour_mismatches:
        print("  1.  Fix locations automatically; review each colour rename one by one")
        if suspect_loc:
            print("  2.  Same as above, and quarantine suspicious entries")
    else:
        print("  1.  Apply all fixes")
        if suspect_loc:
            print("  2.  Apply all fixes, quarantine suspicious entries")
    print("  0.  Back (no changes)")
    print()

    choices = ['1']
    if suspect_loc:
        choices.append('2')

    raw = input("Choice [0]: ").strip()
    if raw not in choices:
        print("No changes made.")
        _pause()
        return

    do_quarantine = (raw == '2')

    # Colour renames are reviewed interactively, one group at a time.
    approved_colour_renames = set()
    if colour_mismatches:
        approved_colour_renames = fix_library.review_colour_renames(colour_mismatches)

    print()
    moved, skipped = fix_library.apply_fixes(
        LIBRARY_ROOT, mismatches,
        quarantine=do_quarantine,
        approved_colour_renames=approved_colour_renames,
    )
    print(f"\nDone. {moved} fixed, {skipped} skipped.")

    if moved:
        print()
        confirm = input("Update README.md to reflect the changes? (y/N) ").strip().lower()
        if confirm in ('y', 'yes'):
            update_readme(LIBRARY_ROOT)
            print("README.md updated.")

    _pause()


# ---------------------------------------------------------------------------
# Option 5 — Sync new UIDs from upstream repository
# ---------------------------------------------------------------------------

def menu_sync_upstream():
    _clear()
    _banner("Sync from Upstream")

    print("Imports new tag UIDs from the upstream repository:")
    print("  https://github.com/queengooborg/Bambu-Lab-RFID-Library")
    print()
    print("New UIDs are copied to the local library at their upstream paths.")
    print("Run Fix Database afterwards to move them to the correct locations.")
    print()

    skip_fetch = input("Skip git fetch (use already-fetched data)? (y/N) ").strip().lower() \
                 in ('y', 'yes')
    print()

    try:
        sync_from_upstream.ensure_upstream_remote()
        if not skip_fetch:
            sync_from_upstream.fetch_upstream()
    except SystemExit:
        print("\nFailed — could not configure or fetch upstream remote.")
        _pause()
        return

    print()
    print("Scanning upstream...", end=' ', flush=True)
    upstream_map = sync_from_upstream.get_upstream_uid_map()
    print(f"{len(upstream_map)} UIDs.")

    print("Scanning local library...", end=' ', flush=True)
    local_uids = sync_from_upstream.get_local_uid_set()
    print(f"{len(local_uids)} UIDs.")

    new_uid_map = {uid: path for uid, path in upstream_map.items()
                   if uid not in local_uids}

    if not new_uid_map:
        print("\nNothing to import -- library already has all upstream UIDs.")
        _pause()
        return

    groups = sync_from_upstream._group_by_material(new_uid_map)
    print(f"\n{len(new_uid_map)} new UID(s) across {len(groups)} material group(s):\n")
    for mat_key in sorted(groups):
        entries = groups[mat_key]
        print(f"  {mat_key}/  ({len(entries)} UID(s))")
        for colour, uid in sorted(entries):
            print(f"    {colour}/{uid}")

    print()
    confirm = input(f"Import {len(new_uid_map)} new UID(s)? (y/N) ").strip().lower()
    if confirm not in ('y', 'yes'):
        print("No changes made.")
        _pause()
        return

    print("\nImporting...")
    total_uids = total_files = 0
    for uid, uid_path in sorted(new_uid_map.items(), key=lambda x: x[1]):
        n_written, n_skipped = sync_from_upstream.import_uid_files(uid_path, dry_run=False)
        status = f"{n_written} file(s) written"
        if n_skipped:
            status += f", {n_skipped} already present"
        print(f"  {uid_path}/ -- {status}")
        total_uids += 1
        total_files += n_written

    print(f"\nImported {total_uids} UID(s), {total_files} file(s).")

    if total_files:
        print()
        confirm = input("Run Fix Database to correct any location/name issues? (y/N) ").strip().lower()
        if confirm in ('y', 'yes'):
            # menu_fix_database clears the screen, handles its own _pause(), and
            # offers to update the README, so we return immediately after it.
            menu_fix_database()
            return

    # If the user skipped fix_library, still offer a README update.
    print()
    confirm = input("Update README.md? (y/N) ").strip().lower()
    if confirm in ('y', 'yes'):
        update_readme(LIBRARY_ROOT)
        print("README.md updated.")

    _pause()


# ---------------------------------------------------------------------------
# Option 6 — Contribute new local UIDs to the upstream repository
# ---------------------------------------------------------------------------

def menu_contribute_upstream():
    _clear()
    _banner("Contribute to Upstream")

    print("Finds tag UIDs in your library that are absent from upstream:")
    print("  https://github.com/queengooborg/Bambu-Lab-RFID-Library")
    print()
    print("A single persistent PR branch is kept up to date each run.")
    print("Branch is rooted on upstream/main -- no local naming changes included.")
    print()
    print("Requires the GitHub CLI (gh) to be installed and authenticated.")
    print("  Install: https://cli.github.com/")
    print("  Auth:    gh auth login")
    print()

    skip_fetch = input("Skip git fetch (use already-fetched data)? (y/N) ").strip().lower() \
                 in ('y', 'yes')
    print()

    try:
        sync_from_upstream.ensure_upstream_remote()
        if not skip_fetch:
            sync_from_upstream.fetch_upstream()
    except SystemExit:
        print("\nFailed -- could not configure or fetch upstream remote.")
        _pause()
        return

    print()
    print("Scanning upstream...", end=' ', flush=True)
    upstream_map = sync_from_upstream.get_upstream_uid_map()
    print(f"{len(upstream_map)} UIDs.")

    print("Scanning local library...", end=' ', flush=True)
    local_uid_map = contribute_to_upstream.get_local_uid_map()
    print(f"{len(local_uid_map)} UIDs.")

    to_contribute = {uid: path for uid, path in local_uid_map.items()
                     if uid not in upstream_map}

    if not to_contribute:
        print("\nNothing to contribute -- all local UIDs are already in upstream.")
        _pause()
        return

    path_str_map = {uid: p.relative_to(LIBRARY_ROOT).as_posix()
                    for uid, p in to_contribute.items()}
    groups = sync_from_upstream._group_by_material(path_str_map)
    print(f"\n{len(to_contribute)} UID(s) to contribute across {len(groups)} material group(s):\n")
    for mat_key in sorted(groups):
        entries = groups[mat_key]
        print(f"  {mat_key}/  ({len(entries)} UID(s))")
        for colour, uid in sorted(entries):
            print(f"    {colour}/{uid}")

    # Check prerequisites before asking to proceed
    if not contribute_to_upstream.check_gh_available():
        print()
        print("ERROR: GitHub CLI (gh) is not installed or not authenticated.")
        print("  Install: https://cli.github.com/")
        print("  Then:    gh auth login")
        _pause()
        return

    owner = contribute_to_upstream.get_origin_owner()
    if not owner:
        print("\nERROR: Could not determine GitHub username from origin remote URL.")
        _pause()
        return

    # Show whether this will create a new PR or update the existing one
    existing_url = contribute_to_upstream.get_open_pr_url(owner)
    branch = contribute_to_upstream.CONTRIBUTION_BRANCH
    if existing_url:
        print(f"\nExisting open PR will be updated: {existing_url}")
        action_label = f"Update PR with {len(to_contribute)} UID(s)?"
    else:
        print(f"\nNo open PR found -- a new one will be created.")
        action_label = f"Create PR with {len(to_contribute)} UID(s)?"

    print()
    confirm = input(f"{action_label} (y/N) ").strip().lower()
    if confirm not in ('y', 'yes'):
        print("No changes made.")
        _pause()
        return

    print(f"\nBuilding branch '{branch}' from {sync_from_upstream.UPSTREAM_REF} ...")
    try:
        worktree_dir = contribute_to_upstream.build_contribution_branch(to_contribute)
        contribute_to_upstream.push_and_sync_pr(worktree_dir, to_contribute, owner)
    except Exception as e:
        print(f"\nERROR: {e}")
        _pause()
        return

    print()
    print(f"Branch '{branch}' will be updated on each run until the PR is merged/closed.")
    print(f"View with:  gh pr view --repo {contribute_to_upstream.UPSTREAM_REPO}")

    _pause()


# ---------------------------------------------------------------------------
# Main menu loop
# ---------------------------------------------------------------------------

MENU_OPTIONS = [
    ("Read tag",               menu_read_tag),
    ("Scan tag to database",   menu_scan_tag),
    ("Write tag from database", menu_write_tag),
    ("Fix database",           menu_fix_database),
    ("Sync from upstream",     menu_sync_upstream),
    ("Contribute to upstream", menu_contribute_upstream),
    ("Exit",                   None),
]


def main():
    global _color_db
    _clear()
    _banner("Starting up")
    print("Loading Bambu Studio colour database...")
    _color_db = load_color_database()
    print()

    while True:
        _clear()
        _banner("Main Menu")
        for i, (label, _) in enumerate(MENU_OPTIONS, 1):
            print(f"  {i}.  {label}")
        print()

        raw = input(f"Choice [1–{len(MENU_OPTIONS)}]: ").strip()
        if not raw.isdigit():
            continue
        idx = int(raw) - 1
        if not (0 <= idx < len(MENU_OPTIONS)):
            continue

        label, fn = MENU_OPTIONS[idx]
        if fn is None:
            print("\nGoodbye.")
            sys.exit(0)

        fn()


if __name__ == "__main__":
    main()
