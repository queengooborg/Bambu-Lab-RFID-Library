# -*- coding: utf-8 -*-
"""
sync_from_upstream.pyImport new tag UIDs from the upstream repository.

Compares the upstream repo (queengooborg/Bambu-Lab-RFID-Library) against
your local library and imports any UID directories that are present upstream
but absent locally.  UIDs are matched by their 8-character hex name, so a
tag that has been moved to a different colour/material folder in your library
is correctly recognised as already present.

After import, the files land at the upstream folder paths.  Run
fix_library.py --fix afterwards to move anything to the right location and
correct any colour folder names to match your conventions.

Usage:
    python sync_from_upstream.py              # fetch + preview
    python sync_from_upstream.py --apply      # fetch + import
    python sync_from_upstream.py --no-fetch   # preview using already-fetched data
    python sync_from_upstream.py --no-fetch --apply   # import without re-fetching
"""

import sys
import subprocess
import argparse
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LIBRARY_ROOT     = Path(__file__).parent.resolve()
UPSTREAM_REMOTE  = 'upstream'
UPSTREAM_URL     = 'https://github.com/queengooborg/Bambu-Lab-RFID-Library.git'
UPSTREAM_REF     = 'upstream/main'

# Top-level folders that contain library data (everything else is scripts/docs)
LIBRARY_CATEGORIES = {'PLA', 'PETG', 'ABS', 'ASA', 'PC', 'TPU', 'PA', 'Support Material'}

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _git(*args, capture=True, check=True):
    """Run a git command in the library root; return stdout text or None."""
    result = subprocess.run(
        ['git'] + list(args),
        capture_output=capture,
        cwd=str(LIBRARY_ROOT),
    )
    if check and result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ''
        print(f"git error: {err}", file=sys.stderr)
        sys.exit(1)
    if capture:
        return result.stdout.decode('utf-8', errors='replace')
    return None


def ensure_upstream_remote():
    remotes = _git('remote').split()
    if UPSTREAM_REMOTE not in remotes:
        print(f"Adding remote '{UPSTREAM_REMOTE}' -> {UPSTREAM_URL}")
        _git('remote', 'add', UPSTREAM_REMOTE, UPSTREAM_URL)
    else:
        print(f"Remote '{UPSTREAM_REMOTE}' already configured.")


def fetch_upstream():
    print(f"Fetching {UPSTREAM_REMOTE} ...", end=' ', flush=True)
    _git('fetch', UPSTREAM_REMOTE, capture=False)
    print("done.")


# ---------------------------------------------------------------------------
# Tree scanning
# ---------------------------------------------------------------------------

def _is_uid(name):
    """Heuristic: a UID folder name is 8 uppercase hex chars."""
    return len(name) == 8 and all(c in '0123456789ABCDEFabcdef' for c in name)


def get_upstream_uid_map():
    """
    Return {uid: uid_rel_path} for every UID directory in UPSTREAM_REF.
    uid_rel_path is the POSIX path string 'Category/Material/Colour/UID'.
    Only top-level categories in LIBRARY_CATEGORIES are considered.
    """
    output = _git('ls-tree', '-r', '--name-only', UPSTREAM_REF)
    uid_map = {}
    for line in output.splitlines():
        parts = Path(line).parts
        if len(parts) < 5:
            continue
        category = parts[0]
        if category not in LIBRARY_CATEGORIES:
            continue
        uid = parts[3]
        if not _is_uid(uid):
            continue
        uid_path = '/'.join(parts[:4])
        if uid.upper() not in uid_map:
            uid_map[uid.upper()] = uid_path
    return uid_map


def get_local_uid_set():
    """
    Return a set of UIDs (uppercase hex) present anywhere in the local library,
    regardless of which folder they are currently stored under.
    Includes UIDs that have been quarantined so they are not re-imported.
    """
    uids = set()
    for p in LIBRARY_ROOT.rglob('*'):
        if not p.is_dir():
            continue
        parts = p.relative_to(LIBRARY_ROOT).parts
        # Normal library entry: Category/Material/Colour/UID
        if len(parts) == 4 and not parts[0].startswith('_') and _is_uid(parts[3]):
            uids.add(parts[3].upper())
        # Quarantined entry: _quarantine/.../UID (depth varies; match by name)
        elif parts[0] == '_quarantine' and _is_uid(parts[-1]):
            uids.add(parts[-1].upper())
    return uids


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def import_uid_files(uid_path, dry_run=False):
    """
    Copy all files for uid_path (e.g. 'PLA/PLA Basic/Gray/A1B2C3D4') from the
    upstream ref into the local working tree.
    Returns (n_written, n_skipped).
    """
    file_list_raw = _git('ls-tree', '--name-only', UPSTREAM_REF, f'{uid_path}/')
    files = [l for l in file_list_raw.splitlines() if l.strip()]

    if not files:
        return 0, 0

    local_dir = LIBRARY_ROOT / uid_path
    n_written = n_skipped = 0

    for filepath in files:
        filename = Path(filepath).name
        dest = local_dir / filename
        if dest.exists():
            n_skipped += 1
            continue
        if dry_run:
            n_written += 1
            continue
        result = subprocess.run(
            ['git', 'show', f'{UPSTREAM_REF}:{filepath}'],
            capture_output=True,
            cwd=str(LIBRARY_ROOT),
        )
        if result.returncode == 0:
            local_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(result.stdout)
            n_written += 1
        else:
            err = result.stderr.decode('utf-8', errors='replace').strip()
            print(f"    WARNING: could not read {filepath}: {err}")

    return n_written, n_skipped


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _group_by_material(uid_path_map):
    """Return {category/material: [(colour, uid), ...]} sorted."""
    groups = defaultdict(list)
    for uid, uid_path in sorted(uid_path_map.items(), key=lambda x: x[1]):
        parts = uid_path.split('/')
        mat_key = f"{parts[0]}/{parts[1]}"
        colour  = parts[2]
        groups[mat_key].append((colour, uid))
    return groups


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Import new tag UIDs from the upstream repository.'
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='Actually import the files (default is preview only).',
    )
    parser.add_argument(
        '--no-fetch', action='store_true',
        help='Skip the git fetch step and use already-fetched upstream data.',
    )
    args = parser.parse_args()

    ensure_upstream_remote()
    if not args.no_fetch:
        fetch_upstream()

    print()
    print("Scanning upstream ...", end=' ', flush=True)
    upstream_map = get_upstream_uid_map()
    print(f"{len(upstream_map)} UIDs.")

    print("Scanning local library ...", end=' ', flush=True)
    local_uids = get_local_uid_set()
    print(f"{len(local_uids)} UIDs.")

    new_uid_map = {uid: path for uid, path in upstream_map.items()
                   if uid not in local_uids}

    if not new_uid_map:
        print("\nNothing to importyour library already has all upstream UIDs.")
        return

    # Display grouped by material
    groups = _group_by_material(new_uid_map)
    print(f"\n{len(new_uid_map)} new UID(s) across {len(groups)} material(s):\n")
    for mat_key in sorted(groups):
        entries = groups[mat_key]
        print(f"  {mat_key}/  ({len(entries)} UID(s))")
        for colour, uid in sorted(entries):
            print(f"    {colour}/{uid}")

    if not args.apply:
        print()
        print("Preview only -- run with --apply to import.")
        print("After importing:")
        print("  python fix_library.py          # preview location/name corrections")
        print("  python fix_library.py --fix    # apply corrections")
        print("  python update_readme.py        # update README")
        print("  git add -A && git commit -m '...' && git push")
        return

    # --- Apply ---
    print("\nImporting ...")
    total_uids = total_files = 0
    for uid, uid_path in sorted(new_uid_map.items(), key=lambda x: x[1]):
        n_written, n_skipped = import_uid_files(uid_path, dry_run=False)
        status = f"{n_written} file(s) written"
        if n_skipped:
            status += f", {n_skipped} already present"
        print(f"  {uid_path}/ {status}")
        total_uids += 1
        total_files += n_written

    print()
    print(f"Imported {total_uids} UID(s), {total_files} file(s).")
    print()
    print("Next steps:")
    print("  1. python fix_library.py          # preview location/name corrections")
    print("  2. python fix_library.py --fix    # apply corrections (interactive)")
    print("  3. python update_readme.py        # update README status + variants")
    print("  4. git add -A && git commit -m 'Import N new tags from upstream' && git push")


if __name__ == '__main__':
    main()
