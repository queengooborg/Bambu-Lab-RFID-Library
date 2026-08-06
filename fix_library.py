# -*- coding: utf-8 -*-
# Scan the Bambu Lab RFID library for misplaced tag folders and optionally fix them.
# Run with no flags to report mismatches; add --fix to move folders and update README.
# Add --quarantine to move suspicious entries to _quarantine/ instead of their expected location.
# Usage: python fix_library.py [library_root] [--fix] [--quarantine] [--no-color-check]

import os
import sys
import stat
import shutil
import argparse
from pathlib import Path

from update_readme import run as update_readme
from parse import Tag
from categories import (
    CATEGORY_MAP, MULTI_COLOR_MATERIAL_MAP, MATERIAL_MAP,
    resolve_material, allowed_material_folders,
)
from colordb import load_color_database, lookup_color_name

DUMP_SUFFIX = "-dump.bin"


def is_suspicious(tag_data):
    """
    Return a warning string if the tag data looks internally inconsistent,
    or None if it looks plausible.
    """
    base = tag_data['detailed_filament_type']
    if not base:
        return (
            f"detailed_filament_type is blank — tag may be corrupt or unwritten "
            f"(color={tag_data['filament_color']}, variant={tag_data['variant_id']})"
        )
    count = tag_data.get('filament_color_count', 1)
    if count > 1 and base not in MULTI_COLOR_MATERIAL_MAP:
        return (
            f"tag claims {count} colours but '{base}' has no known multi-colour variant "
            f"(color={tag_data['filament_color']})"
        )
    return None


def scan_library(library_root, color_db=None):
    """
    Walk the library and return (mismatches, parse_errors).

    Each mismatch is a dict with keys:
      type          -- 'location' or 'colour_name'
      uid           -- UID folder name
      src           -- Path of the UID folder as currently found
      dst           -- Path of the UID folder at its correct location
      rel_current   -- slash-joined relative path (for display)
      rel_expected  -- slash-joined expected relative path (for display)
      tag_cat       -- tag's filament_type value
      tag_mat       -- tag's detailed_filament_type value
      warning       -- suspicious-data warning string, or None

    colour_name mismatches additionally have:
      colour_current  -- folder name as found
      colour_expected -- official name from Bambu Studio DB

    Location is checked first; colour name is only checked when location is
    already correct (to avoid double-reporting the same UID).
    """
    mismatches   = []
    parse_errors = []
    uid_paths    = {}   # uid_str -> [Path, ...] — for duplicate detection

    for dump_file in sorted(library_root.rglob(f'*{DUMP_SUFFIX}')):
        rel   = dump_file.relative_to(library_root)
        parts = rel.parts
        if parts[0].startswith('_'):
            continue
        if len(parts) < 5:
            continue

        cat_dir, mat_dir, color_dir, uid_dir = parts[0], parts[1], parts[2], parts[3]

        # Track every UID folder path seen (for duplicate detection).
        uid_folder = library_root / cat_dir / mat_dir / color_dir / uid_dir
        uid_paths.setdefault(uid_dir, [])
        if uid_folder not in uid_paths[uid_dir]:
            uid_paths[uid_dir].append(uid_folder)

        try:
            with open(dump_file, 'rb') as f:
                tag = Tag(dump_file.name, f.read(), fail_on_warn=False)
        except Exception as e:
            parse_errors.append((rel, str(e)))
            continue

        expected_cat = CATEGORY_MAP.get(tag.data['filament_type'], tag.data['filament_type'])
        raw_mat      = tag.data['detailed_filament_type']
        expected_mat = resolve_material(tag.data)
        allowed_mats = allowed_material_folders(tag.data)
        warning      = is_suspicious(tag.data)

        # --- Check location (category / material) ---
        location_wrong = cat_dir != expected_cat or mat_dir not in allowed_mats
        if location_wrong:
            mismatches.append({
                'type':         'location',
                'uid':          uid_dir,
                'src':          library_root / cat_dir / mat_dir / color_dir / uid_dir,
                'dst':          library_root / expected_cat / expected_mat / color_dir / uid_dir,
                'rel_current':  f"{cat_dir}/{mat_dir}/{color_dir}/{uid_dir}",
                'rel_expected': f"{expected_cat}/{expected_mat}/{color_dir}/{uid_dir}",
                'tag_cat':      tag.data['filament_type'],
                'tag_mat':      raw_mat,
                'warning':      warning,
            })

        # --- Check colour folder name against Bambu Studio DB ---
        # For correctly-located tags: src is the current path.
        # For misplaced tags: src is the post-move path (location dst) so both
        # fixes can be applied in a single pass.  The 'pending' flag marks these
        # entries as dependent on the location fix being applied first.
        if color_db:
            exact_name, _ = lookup_color_name(tag.data, color_db)
            if exact_name and color_dir != exact_name:
                if location_wrong:
                    # Colour src/dst are relative to the correct category/material.
                    c_cat, c_mat = expected_cat, expected_mat
                    pending = True
                else:
                    c_cat, c_mat = cat_dir, mat_dir
                    pending = False
                mismatches.append({
                    'type':            'colour_name',
                    'uid':             uid_dir,
                    'src':             library_root / c_cat / c_mat / color_dir / uid_dir,
                    'dst':             library_root / c_cat / c_mat / exact_name / uid_dir,
                    'rel_current':     f"{c_cat}/{c_mat}/{color_dir}/{uid_dir}",
                    'rel_expected':    f"{c_cat}/{c_mat}/{exact_name}/{uid_dir}",
                    'colour_current':  color_dir,
                    'colour_expected': exact_name,
                    'tag_cat':         tag.data['filament_type'],
                    'tag_mat':         raw_mat,
                    'warning':         warning,
                    'pending':         pending,
                })

    # Duplicates: any UID that appears in more than one folder.
    duplicates = {uid: paths for uid, paths in uid_paths.items() if len(paths) > 1}

    return mismatches, parse_errors, duplicates


def _colour_mismatch_summary(colour_mismatches):
    """
    Print a grouped summary of colour-name mismatches.
    Pending renames (dependent on a location fix) are shown with a note.
    When all tags in a group share the same tag_mat that differs from their
    material folder, that type is noted for clarity.
    """
    from itertools import groupby
    key = lambda m: (m['colour_current'], m['colour_expected'])
    for (cur, exp), group in groupby(sorted(colour_mismatches, key=key), key=key):
        items        = list(group)
        uids         = [m['uid'] for m in items]
        pending_all  = all(m.get('pending') for m in items)
        pending_some = any(m.get('pending') for m in items)

        tag_mats     = {m['tag_mat'] for m in items}
        folder_names = {m['src'].parent.parent.name for m in items}
        type_note    = ""
        if len(tag_mats) == 1:
            tag_mat     = next(iter(tag_mats))
            folder_name = next(iter(folder_names)) if len(folder_names) == 1 else None
            if folder_name and tag_mat != folder_name:
                type_note = f"  [tag type: {tag_mat}, filed under: {folder_name}]"

        pending_note = ""
        if pending_all:
            pending_note = "  [after location fix]"
        elif pending_some:
            n = sum(1 for m in items if m.get('pending'))
            pending_note = f"  [{n} after location fix]"

        print(f"  '{cur}'  ->  '{exp}'  ({len(items)} UID(s): {', '.join(uids)})"
              f"{type_note}{pending_note}")


def review_colour_renames(colour_mismatches):
    """
    Walk through colour-name mismatches group by group and ask the user
    whether to apply each rename.

    Returns a set of (colour_current, colour_expected) tuples that were approved.
    An empty set means nothing was approved (no renames will be applied).
    """
    from itertools import groupby

    key     = lambda m: (m['colour_current'], m['colour_expected'])
    groups  = [(k, list(g)) for k, g in groupby(sorted(colour_mismatches, key=key), key=key)]
    approved = set()

    print(f"\n{len(groups)} colour folder rename(s) to review:\n")

    for i, ((cur, exp), items) in enumerate(groups, 1):
        pending_count = sum(1 for m in items if m.get('pending'))
        pending_note  = (f"  [all after location fix]" if pending_count == len(items)
                         else f"  [{pending_count} after location fix]" if pending_count
                         else "")
        print(f"[{i}/{len(groups)}]  '{cur}'  ->  '{exp}'  ({len(items)} UID(s)){pending_note}")
        for m in items:
            mat_note     = (f"  [tag type: {m['tag_mat']}]"
                            if m['tag_mat'] != m['src'].parent.parent.name else "")
            after_note   = "  [after location fix]" if m.get('pending') else ""
            print(f"         {m['src']}{mat_note}{after_note}")
        raw = input("  Apply rename? (y/N) ").strip().lower()
        if raw in ('y', 'yes'):
            approved.add((cur, exp))
        print()

    return approved


def apply_fixes(library_root, mismatches, quarantine=False, approved_colour_renames=None):
    """
    Apply fixes for mismatches returned by scan_library.

    Location mismatches are processed first, then colour-name mismatches.
    Suspicious entries are quarantined if quarantine=True, otherwise skipped.
    Empty colour folders left behind after colour-name renames are removed.

    approved_colour_renames: set of (colour_current, colour_expected) tuples to apply.
      Pass None to apply all colour renames; pass an empty set to skip all.

    Returns (moved, skipped).
    """
    quarantine_root  = library_root / "_quarantine"
    moved, skipped   = 0, 0
    colour_src_dirs  = set()   # colour folders that may be empty after renames

    location_normal  = [m for m in mismatches if m['type'] == 'location' and not m['warning']]
    location_suspect = [m for m in mismatches if m['type'] == 'location' and m['warning']]
    colour_fixes     = [m for m in mismatches if m['type'] == 'colour_name']

    # --- 1. Fix normal location mismatches ---
    for m in location_normal:
        src, dst = m['src'], m['dst']
        if dst.exists():
            src_dumps = sorted(src.glob(f'*{DUMP_SUFFIX}'))
            dst_dumps = sorted(dst.glob(f'*{DUMP_SUFFIX}'))
            if src_dumps and dst_dumps and \
                    src_dumps[0].read_bytes() == dst_dumps[0].read_bytes():
                shutil.rmtree(str(src))
                print(f"  Removed stale duplicate: {m['rel_current']}")
                print(f"     (data already at {m['rel_expected']})")
                moved += 1
            else:
                print(f"  [!] Skipped {m['uid']}: destination exists with different data")
                skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"  Moved: {m['rel_current']}")
        print(f"      -> {m['rel_expected']}")
        moved += 1

    # --- 2. Handle suspicious location mismatches ---
    if location_suspect:
        if quarantine:
            for m in location_suspect:
                src = m['src']
                dst = quarantine_root / m['rel_current']
                if dst.exists():
                    print(f"  [!] Skipped {m['uid']}: quarantine destination already exists")
                    skipped += 1
                    continue
                dst.mkdir(parents=True, exist_ok=True)
                for item in src.iterdir():
                    # Clear read-only flag before moving (git sets R/O on Windows)
                    try:
                        os.chmod(item, stat.S_IWRITE | stat.S_IREAD)
                    except OSError:
                        pass
                    shutil.move(str(item), str(dst / item.name))
                src.rmdir()
                (dst / "_quarantine.txt").write_text(
                    f"Quarantined from: {m['rel_current']}\n"
                    f"Expected location: {m['rel_expected']}\n"
                    f"Tag data: {m['tag_cat']} / {m['tag_mat']}\n"
                    f"Warning: {m['warning']}\n",
                    encoding='utf-8',
                )
                print(f"  Quarantined: {m['rel_current']}")
                moved += 1
        else:
            print(f"\n{len(location_suspect)} suspicious folder(s) were NOT moved.")
            print("Re-run with --fix --quarantine to quarantine them.")

    # --- 3. Fix colour-name mismatches ---
    for m in colour_fixes:
        if approved_colour_renames is not None and \
                (m['colour_current'], m['colour_expected']) not in approved_colour_renames:
            continue
        src, dst = m['src'], m['dst']
        if not src.exists():
            # Pending rename whose location fix was skipped or failed — nothing to do.
            continue
        colour_src_dirs.add(src.parent)
        if dst.exists():
            # src and dst share the same UID folder name — they are the same physical
            # tag. Dump bytes can differ between captures (sector trailer key fields),
            # so a byte comparison is unreliable. Just remove the misnamed copy; the
            # correctly-named dst is the authoritative one.
            shutil.rmtree(str(src))
            print(f"  Removed misnamed copy: {m['rel_current']}")
            print(f"     (already present at {m['rel_expected']})")
            moved += 1
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"  Renamed colour: {m['rel_current']}")
            print(f"              -> {m['rel_expected']}")
            moved += 1

    # --- 4. Remove any colour folders that are now empty ---
    for colour_dir in sorted(colour_src_dirs):
        if colour_dir.exists() and not any(colour_dir.iterdir()):
            colour_dir.rmdir()
            print(f"  Removed empty folder: {colour_dir.relative_to(library_root)}")

    return moved, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Find (and optionally fix) misplaced or mislabelled RFID tag folders.'
    )
    parser.add_argument(
        'library_root', nargs='?', default='.',
        help='Path to library root (default: current directory)'
    )
    parser.add_argument(
        '--fix', action='store_true',
        help='Move misplaced folders to their correct location'
    )
    parser.add_argument(
        '--quarantine', action='store_true',
        help='When used with --fix, quarantine suspicious entries instead of moving them'
    )
    parser.add_argument(
        '--no-color-check', action='store_true',
        help='Skip colour folder name validation against the Bambu Studio database'
    )
    args = parser.parse_args()

    library_root = Path(args.library_root).resolve()
    if not library_root.exists():
        print(f"Error: {library_root} does not exist")
        sys.exit(1)

    color_db = []
    if not args.no_color_check:
        color_db = load_color_database()

    print(f"\nScanning {library_root} ...")
    mismatches, parse_errors, duplicates = scan_library(library_root, color_db)

    if parse_errors:
        print(f"\n{len(parse_errors)} file(s) failed to parse:")
        for path, err in parse_errors:
            print(f"  [!] {path}: {err}")

    if not mismatches and not duplicates:
        print("\nNo issues found — library is correctly organised.")
        return

    # --- Display ---
    location_mismatches = [m for m in mismatches if m['type'] == 'location']
    colour_mismatches   = [m for m in mismatches if m['type'] == 'colour_name']

    normal_loc   = [m for m in location_mismatches if not m['warning']]
    suspect_loc  = [m for m in location_mismatches if m['warning']]

    if normal_loc:
        print(f"\n{len(normal_loc)} misplaced folder(s):\n")
        for m in normal_loc:
            print(f"  {m['rel_current']}")
            print(f"    -> {m['rel_expected']}  (tag: {m['tag_cat']} / {m['tag_mat']})")

    if suspect_loc:
        print(f"\n{len(suspect_loc)} suspicious entry(s) — tag data may be corrupt:\n")
        for m in suspect_loc:
            print(f"  {m['rel_current']}")
            print(f"    -> {m['rel_expected']}  (tag: {m['tag_cat']} / {m['tag_mat']})")
            print(f"    [!] {m['warning']}")

    if colour_mismatches:
        print(f"\n{len(colour_mismatches)} wrong colour folder name(s):\n")
        _colour_mismatch_summary(colour_mismatches)

    if duplicates:
        print(f"\n{len(duplicates)} duplicate UID(s) — must be resolved manually:\n")
        for uid, paths in sorted(duplicates.items()):
            print(f"  {uid}  ({len(paths)} copies)")
            for p in paths:
                print(f"    {p.relative_to(library_root)}")

    if not args.fix:
        hint = "--fix"
        if suspect_loc:
            hint += " --quarantine"
        print(f"\nRun with {hint} to apply fixes.")
        return

    # Colour renames are always reviewed interactively — too risky to apply blindly.
    approved_colour_renames = set()
    if colour_mismatches:
        approved_colour_renames = review_colour_renames(colour_mismatches)

    print()
    moved, skipped = apply_fixes(
        library_root, mismatches,
        quarantine=args.quarantine,
        approved_colour_renames=approved_colour_renames,
    )
    print(f"\nDone: {moved} fixed, {skipped} skipped.")

    if moved:
        print("\nUpdating README.md ...")
        update_readme(library_root)


if __name__ == "__main__":
    main()
