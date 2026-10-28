# -*- coding: utf-8 -*-
# Scan the library and update README.md status icons and variant IDs to match actual data.
# Rows with ✅/❌ are updated; ⚠️ and ⏳ rows are left untouched.
# Usage: python update_readme.py [library_root] [--dry-run]

import re
import sys
import argparse
from pathlib import Path
from urllib.parse import unquote

from parse import Tag

DUMP_SUFFIX = "-dump.bin"

# README links may use store-facing names that don't match actual folder names
# (e.g. slashes in material names become path separators in URLs, or the folder
# was renamed after the README was generated).  Map the link path prefix to the
# real relative folder path so we can still find the data.
PATH_ALIASES = {
    # PETG-CF folder was created with a space, not a hyphen
    'PETG/PETG-CF':                              'PETG/PETG CF',
    # Slashes in support material names became URL path separators
    'Support Material/Support for PLA/PETG':     'Support Material/Support for PLA-PETG',
    'Support Material/Support for PA/PET':       'Support Material/Support for PA-PET',
}


def get_color_info(color_dir):
    """Return (has_data, sorted_variant_ids) by inspecting all UID subdirs."""
    if not color_dir.exists() or not color_dir.is_dir():
        return False, []

    variants = set()
    has_data = False

    for uid_dir in sorted(color_dir.iterdir()):
        if not uid_dir.is_dir():
            continue

        # Prefer standard *-dump.bin files; fall back to any .bin that isn't a key
        dump_files = list(uid_dir.glob(f'*{DUMP_SUFFIX}'))
        if not dump_files:
            dump_files = [
                f for f in uid_dir.glob('*.bin')
                if not f.name.endswith('-key.bin')
            ]

        for dump_file in dump_files:
            has_data = True
            try:
                with open(dump_file, 'rb') as f:
                    tag = Tag(dump_file.name, f.read(), fail_on_warn=False)
                v = str(tag.data.get('variant_id', '')).strip()
                if v:
                    variants.add(v)
            except Exception:
                pass

    return has_data, sorted(variants)


def process_line(line, library_root):
    """
    Inspect one README line.  If it is a table data row with a ./ link and a
    ✅/❌ status cell, return (new_line, changed, description).
    Otherwise return (line, False, None).
    """
    raw = line.rstrip('\n')

    # Quick pre-checks: needs pipes, a markdown link, and a status icon
    if raw.count('|') < 4 or '](./' not in raw:
        return line, False, None

    cells = raw.split('|')
    if len(cells) < 6:
        return line, False, None

    # Cell layout: '' | color_link | filament_code | variant_id | status | ''
    link_match = re.search(r'\((\./[^)]+)\)', cells[1])
    if not link_match:
        return line, False, None

    link_path = link_match.group(1)
    rel_path = unquote(link_path.lstrip('./'))

    # Translate any known broken/renamed path prefixes to real folder paths
    for alias, real in PATH_ALIASES.items():
        if rel_path == alias or rel_path.startswith(alias + '/'):
            rel_path = real + rel_path[len(alias):]
            break

    color_dir = library_root / rel_path

    # Identify the existing status icon
    old_status = None
    for icon in ['✅', '❌', '⚠️', '⏳']:
        if icon in cells[4]:
            old_status = icon
            break
    if old_status is None:
        return line, False, None

    # Never touch rows that carry a special human-authored status
    if old_status in ('⚠️', '⏳'):
        return line, False, None

    has_data, variants = get_color_info(color_dir)

    new_status = '✅' if has_data else '❌'
    old_variant = cells[3].strip()

    # Update variant ID when we have real data
    new_variant = old_variant
    if variants:
        candidate = '/'.join(variants)
        if old_variant in ('?', '') or old_variant != candidate:
            new_variant = candidate

    changed = (new_status != old_status) or (new_variant != old_variant)
    if not changed:
        return line, False, None

    # Reconstruct cells, preserving original column widths where possible
    old_variant_cell = cells[3]
    new_variant_cell = f' {new_variant} '
    # Pad to at least the original width so the table doesn't shrink
    if len(new_variant_cell) < len(old_variant_cell):
        new_variant_cell = new_variant_cell.ljust(len(old_variant_cell))

    cells[3] = new_variant_cell
    cells[4] = cells[4].replace(old_status, new_status, 1)

    STATUS_LABEL = {'✅': '[ok]', '❌': '[no]', '⚠️': '[warn]', '⏳': '[pending]'}
    parts = []
    if new_status != old_status:
        old_lbl = STATUS_LABEL.get(old_status, old_status)
        new_lbl = STATUS_LABEL.get(new_status, new_status)
        parts.append(f"status {old_lbl} -> {new_lbl}")
    if new_variant != old_variant:
        parts.append(f"variant '{old_variant}' -> '{new_variant}'")

    return '|'.join(cells) + '\n', True, f"{rel_path}: {', '.join(parts)}"


def _check_broken_links(lines, library_root):
    """
    Scan README lines for table rows whose link path does not exist on disk.
    Returns a list of (display_name, rel_path) tuples for broken links.
    These arise when a colour folder is renamed without updating the README row.
    """
    broken = []
    for line in lines:
        raw = line.rstrip('\n')
        if raw.count('|') < 4 or '](./' not in raw:
            continue
        cells = raw.split('|')
        if len(cells) < 6:
            continue
        link_match = re.search(r'\[([^\]]+)\]\(\./([^)]+)\)', cells[1])
        if not link_match:
            continue
        display = link_match.group(1)
        rel_path = unquote(link_match.group(2))

        for alias, real in PATH_ALIASES.items():
            if rel_path == alias or rel_path.startswith(alias + '/'):
                rel_path = real + rel_path[len(alias):]
                break

        color_dir = library_root / rel_path
        # Only warn about colour-level folders (3 path components) that have a ✅ status
        # but no matching folder on disk.  Missing ❌ folders are normal (not yet scanned).
        parts = Path(rel_path).parts
        if len(parts) == 3 and not color_dir.exists():
            # Check whether this row carries a ✅ status
            if '✅' in raw:
                broken.append((display, rel_path))
    return broken


def run(library_root, dry_run=False):
    """Update README.md in library_root. Returns number of changes made."""
    library_root = Path(library_root).resolve()
    readme_path = library_root / 'README.md'

    if not readme_path.exists():
        print(f"Error: {readme_path} not found")
        return 0

    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    changes = []

    for line in lines:
        new_line, changed, description = process_line(line, library_root)
        new_lines.append(new_line)
        if changed:
            changes.append(description)

    # Warn about README rows whose colour folder no longer exists on disk.
    # This happens when fix_library renames a colour folder but the README link
    # is not updated to match.  These rows will silently flip to ❌ on the
    # next update_readme run even though data may exist under the new name.
    broken = _check_broken_links(lines, library_root)
    if broken:
        print(f"\nWARNING: {len(broken)} README row(s) link to non-existent folder(s).")
        print("  These rows may have stale display names or link paths.")
        print("  Update the README row (display text + URL) to match the actual folder name.")
        for display, rel_path in broken:
            print(f"    '{display}' -> {rel_path}")

    if not changes:
        print("README is already up to date.")
        return 0

    print(f"{len(changes)} change(s):")
    for c in changes:
        print(f"  {c}")

    if dry_run:
        print("\nDry run - README not modified. Remove --dry-run to apply.")
        return len(changes)

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("README updated.")
    return len(changes)


def main():
    parser = argparse.ArgumentParser(
        description='Update README.md status icons and variant IDs from actual library data.'
    )
    parser.add_argument(
        'library_root', nargs='?', default='.',
        help='Path to library root (default: current directory)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Show what would change without writing the file'
    )
    args = parser.parse_args()
    run(args.library_root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
