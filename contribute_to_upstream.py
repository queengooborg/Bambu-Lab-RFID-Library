# -*- coding: utf-8 -*-
"""
contribute_to_upstream.py -- Contribute new local tag UIDs to the upstream repository.

Compares your local library against the upstream repo and creates (or updates)
a single persistent pull-request branch containing every UID that is present
locally but absent upstream.  The branch is rooted on upstream/main, so none
of your local naming convention changes are included.

Each run rebuilds the branch from scratch and force-pushes it, so the open PR
stays up to date as you scan more tags.  When the upstream author merges or
closes the PR, the next run detects no open PR and creates a fresh one.

Requirements:
    - git remote 'upstream' pointing to queengooborg/Bambu-Lab-RFID-Library
    - GitHub CLI (gh) installed and authenticated (run: gh auth login)

Usage:
    python contribute_to_upstream.py              # fetch + preview
    python contribute_to_upstream.py --apply      # fetch + create/update PR
    python contribute_to_upstream.py --no-fetch   # preview using already-fetched data
    python contribute_to_upstream.py --no-fetch --apply
"""

import re
import sys
import shutil
import subprocess
import argparse
import tempfile
from pathlib import Path
from urllib.parse import quote as url_quote

from sync_from_upstream import (
    LIBRARY_ROOT, UPSTREAM_REMOTE, UPSTREAM_URL, UPSTREAM_REF,
    LIBRARY_CATEGORIES,
    ensure_upstream_remote, fetch_upstream,
    get_upstream_uid_map, _is_uid, _group_by_material,
    _git,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ORIGIN_REMOTE       = 'origin'
UPSTREAM_REPO       = 'queengooborg/Bambu-Lab-RFID-Library'
CONTRIBUTION_BRANCH = 'contribute/pending'   # single persistent PR branch

# ---------------------------------------------------------------------------
# Local library scan
# ---------------------------------------------------------------------------

def get_local_uid_map():
    """
    Return {uid_uppercase: uid_dir_Path} for every non-quarantined UID in the
    local library (directories at depth 4: Category/Material/Colour/UID).
    """
    uid_map = {}
    for p in LIBRARY_ROOT.rglob('*'):
        if not p.is_dir():
            continue
        parts = p.relative_to(LIBRARY_ROOT).parts
        if (len(parts) == 4
                and not parts[0].startswith('_')
                and parts[0] in LIBRARY_CATEGORIES
                and _is_uid(parts[3])):
            uid_map[parts[3].upper()] = p
    return uid_map

# ---------------------------------------------------------------------------
# GitHub CLI helpers
# ---------------------------------------------------------------------------

def _gh(*args, capture=True, check=True):
    """Run a gh command in the library root; return stdout text or None."""
    result = subprocess.run(
        ['gh'] + list(args),
        capture_output=capture,
        cwd=str(LIBRARY_ROOT),
    )
    if check and result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ''
        print(f"gh error: {err}", file=sys.stderr)
        sys.exit(1)
    if capture:
        return result.stdout.decode('utf-8', errors='replace')
    return None


def check_gh_available():
    """Return True if gh CLI is installed and the user is authenticated."""
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_origin_owner():
    """Return the GitHub username/org for the origin remote (e.g. 'NickWaterton')."""
    url = _git('remote', 'get-url', ORIGIN_REMOTE).strip()
    m = re.search(r'[:/]([^/]+)/[^/]+(?:\.git)?$', url)
    return m.group(1) if m else None


def get_open_pr_url(owner):
    """
    Return the URL of the currently open PR from owner:CONTRIBUTION_BRANCH,
    or None if no such PR exists.

    Uses headRefName + headRepositoryOwner — both are valid gh pr list --json
    fields.  headLabel is NOT available in gh pr list (only in gh pr view).
    """
    import json as _json
    try:
        result = subprocess.run(
            ['gh', 'pr', 'list',
             '--repo', UPSTREAM_REPO,
             '--state', 'open',
             '--limit', '100',
             '--json', 'url,headRefName,headRepositoryOwner'],
            capture_output=True,
            cwd=str(LIBRARY_ROOT),
        )
        if result.returncode != 0:
            return None
        prs = _json.loads(result.stdout.decode('utf-8', errors='replace'))
        for pr in prs:
            ref        = pr.get('headRefName', '')
            pr_owner   = pr.get('headRepositoryOwner', {}).get('login', '')
            if ref == CONTRIBUTION_BRANCH and pr_owner.lower() == owner.lower():
                return pr['url']
        return None
    except Exception:
        return None

# ---------------------------------------------------------------------------
# README update helpers
# ---------------------------------------------------------------------------

def _url_path(parts):
    """URL-encode a sequence of path parts and join with '/'."""
    return '/'.join(url_quote(p, safe='') for p in parts)


def _read_dump(uid_dir):
    """Return parsed tag data dict from the first dump file in uid_dir, or None."""
    from parse import Tag
    dump_files = list(uid_dir.glob('*-dump.bin'))
    if not dump_files:
        dump_files = [f for f in uid_dir.glob('*.bin')
                      if not f.name.endswith('-key.bin')]
    if not dump_files:
        return None
    try:
        with open(dump_files[0], 'rb') as fh:
            tag = Tag(dump_files[0].name, fh.read(), fail_on_warn=False)
        return tag.data
    except Exception:
        return None


def _colour_in_readme(content, cat, mat, colour):
    """Return True if the README has any link pointing to this colour folder."""
    plain   = f'./{cat}/{mat}/{colour})'
    encoded = f'./{_url_path([cat, mat, colour])})'
    return plain in content or encoded in content


def _find_table_insert_point(lines, cat, mat):
    """
    Locate the last data row of the material's table in the README.
    Returns the line index to insert after, or None if the section is not found.
    Data rows are identified by starting with '|' and containing '[' (a markdown link).
    """
    mat_encoded = _url_path([cat, mat])
    mat_plain   = f'{cat}/{mat}'

    # Find the section heading that references this material
    section_idx = None
    for i, line in enumerate(lines):
        if line.startswith('#') and (mat_encoded in line or mat_plain in line):
            section_idx = i
            break
    if section_idx is None:
        return None

    heading_depth = len(lines[section_idx]) - len(lines[section_idx].lstrip('#'))
    last_data_row = None

    for i in range(section_idx + 1, len(lines)):
        stripped = lines[i].strip()
        # Stop at the next heading of equal or higher level
        if stripped.startswith('#'):
            depth = len(stripped) - len(stripped.lstrip('#'))
            if depth <= heading_depth:
                break
        # A data row contains a markdown link inside a table cell
        if stripped.startswith('|') and '[' in stripped:
            last_data_row = i

    return last_data_row


def update_upstream_readme(worktree_dir, uid_dirs):
    """
    Update the upstream README.md inside the worktree:

    Step 1 — run update_readme against the worktree to flip any existing ❌ rows
             to ✅ and fill in variant IDs for colours we just added.
    Step 2 — for colours that have no README row at all (brand-new releases),
             parse the dump and insert a new row at the end of the right table.
             The Filament Code column is left as '?' for the upstream maintainer
             to fill in; the variant ID comes from the tag itself.
    """
    import update_readme as _ur

    readme_path = worktree_dir / 'README.md'
    if not readme_path.exists():
        print("  WARNING: README.md not found in worktree -- skipping README update.")
        return

    # Step 1: update existing ❌ rows → ✅ and fill variant IDs
    n_changed = _ur.run(worktree_dir, dry_run=False)
    if n_changed:
        print(f"  Updated {n_changed} existing README row(s) to checkmark.")

    # Re-read the (possibly modified) file
    with open(readme_path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()
    content = ''.join(lines)

    # Step 2: insert rows for colours with no existing README entry
    rows_added = 0
    for uid, local_uid_dir in sorted(uid_dirs.items(), key=lambda kv: str(kv[1])):
        rel_parts = local_uid_dir.relative_to(LIBRARY_ROOT).parts
        cat, mat, colour = rel_parts[0], rel_parts[1], rel_parts[2]

        if _colour_in_readme(content, cat, mat, colour):
            continue  # already handled in step 1 or was already ✅

        # Parse tag data for the variant ID
        uid_dir_in_wt = worktree_dir / cat / mat / colour / rel_parts[3]
        tag_data   = _read_dump(uid_dir_in_wt)
        variant_id = str(tag_data.get('variant_id', '?')).strip() if tag_data else '?'

        colour_link = f'[{colour}](./{_url_path([cat, mat, colour])})'
        new_row     = f'| {colour_link} | ? | {variant_id} | ✅ |\n'

        insert_at = _find_table_insert_point(lines, cat, mat)
        if insert_at is not None:
            lines.insert(insert_at + 1, new_row)
            content = ''.join(lines)   # keep in sync for subsequent iterations
            print(f"  Added README row: {cat}/{mat}/{colour}  (variant: {variant_id})")
            rows_added += 1
        else:
            print(f"  WARNING: no README section found for '{cat}/{mat}' -- "
                  f"add a row for '{colour}' manually.")

    if rows_added:
        with open(readme_path, 'w', encoding='utf-8') as fh:
            fh.writelines(lines)


# ---------------------------------------------------------------------------
# Core: build contribution branch in a temporary worktree
# ---------------------------------------------------------------------------

def build_contribution_branch(uid_dirs):
    """
    (Re)create CONTRIBUTION_BRANCH from UPSTREAM_REF in a temporary worktree,
    copy all uid_dirs into it, and commit.

    Any existing local branch with that name is deleted first so the branch is
    always a clean rebuild from upstream/main.

    Returns the Path of the worktree (caller must clean it up).
    Raises on any git/IO error (cleans up before raising).
    """
    # Delete stale local branch if present
    existing = _git('branch', '--list', CONTRIBUTION_BRANCH).strip()
    if existing:
        _git('branch', '-D', CONTRIBUTION_BRANCH)

    _git('branch', CONTRIBUTION_BRANCH, UPSTREAM_REF)

    worktree_dir = Path(tempfile.mkdtemp(prefix='bambu-contribute-'))
    try:
        _git('worktree', 'add', str(worktree_dir), CONTRIBUTION_BRANCH)

        # Copy each UID directory
        for uid, local_uid_dir in sorted(uid_dirs.items(),
                                          key=lambda kv: str(kv[1])):
            rel = local_uid_dir.relative_to(LIBRARY_ROOT)
            target_dir = worktree_dir / rel
            target_dir.mkdir(parents=True, exist_ok=True)
            n_files = 0
            for f in sorted(local_uid_dir.iterdir()):
                if f.is_file():
                    shutil.copy2(str(f), str(target_dir / f.name))
                    n_files += 1
            print(f"  {rel.as_posix()}/  ({n_files} file(s))")

        # Update the upstream README to reflect the new tags
        print("Updating upstream README.md ...")
        update_upstream_readme(worktree_dir, uid_dirs)

        # Stage all additions (UID files + README changes)
        subprocess.run(['git', 'add', '-A'], cwd=str(worktree_dir), check=True)

        # Build commit message
        n_uids = len(uid_dirs)
        uid_lines = ''.join(f'  - {uid}\n' for uid in sorted(uid_dirs))
        commit_msg = (
            f"Add {n_uids} new tag scan(s); update README\n\n"
            f"UIDs:\n{uid_lines}"
        )
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=str(worktree_dir),
            check=True,
        )

    except Exception:
        # Best-effort cleanup before re-raising
        try:
            _git('worktree', 'remove', '--force', str(worktree_dir))
        except Exception:
            pass
        shutil.rmtree(str(worktree_dir), ignore_errors=True)
        try:
            _git('branch', '-D', CONTRIBUTION_BRANCH)
        except Exception:
            pass
        raise

    return worktree_dir


def push_and_sync_pr(worktree_dir, uid_dirs, owner):
    """
    Force-push CONTRIBUTION_BRANCH to origin, then either open a new PR or
    update the title/body of the existing one.
    Always removes the worktree when done (success or failure).
    """
    try:
        print(f"Pushing branch '{CONTRIBUTION_BRANCH}' to {ORIGIN_REMOTE} ...")
        # --force-with-lease is safe: refuses if someone else pushed since we last fetched
        subprocess.run(
            ['git', 'push', '--force-with-lease', ORIGIN_REMOTE, CONTRIBUTION_BRANCH],
            cwd=str(LIBRARY_ROOT),
            check=True,
        )

        n_uids = len(uid_dirs)
        pr_title = f"Add {n_uids} new tag scan(s)"
        uid_list_md = ''.join(f'- `{uid}`\n' for uid in sorted(uid_dirs))
        pr_body = (
            f"## New tag scans\n\n"
            f"This PR contributes {n_uids} new UID(s) scanned from genuine Bambu Lab "
            f"filament spools.\n\n"
            f"### UIDs included\n\n"
            f"{uid_list_md}\n"
            f"_Contributed from [{owner}/Bambu-Lab-RFID-Library]"
            f"(https://github.com/{owner}/Bambu-Lab-RFID-Library)_\n"
        )

        existing_url = get_open_pr_url(owner)
        if existing_url:
            # Update the existing PR's title and body to reflect the new count/list
            print(f"Updating existing PR ...")
            _gh(
                'pr', 'edit', existing_url,
                '--repo',  UPSTREAM_REPO,
                '--title', pr_title,
                '--body',  pr_body,
                capture=False,
            )
            print(f"PR updated: {existing_url}")
        else:
            print(f"Opening PR against {UPSTREAM_REPO} ...")
            url = _gh(
                'pr', 'create',
                '--repo',  UPSTREAM_REPO,
                '--head',  f'{owner}:{CONTRIBUTION_BRANCH}',
                '--title', pr_title,
                '--body',  pr_body,
            ).strip()
            print(f"PR created: {url}")

    finally:
        try:
            _git('worktree', 'remove', '--force', str(worktree_dir))
        except Exception:
            pass
        shutil.rmtree(str(worktree_dir), ignore_errors=True)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Contribute new local tag UIDs to the upstream repository via a PR.'
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='Actually create/update the PR branch (default: preview only).',
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
    print("Scanning upstream...", end=' ', flush=True)
    upstream_map = get_upstream_uid_map()
    print(f"{len(upstream_map)} UIDs.")

    print("Scanning local library...", end=' ', flush=True)
    local_uid_map = get_local_uid_map()
    print(f"{len(local_uid_map)} UIDs.")

    # UIDs present locally but absent upstream
    to_contribute = {uid: path for uid, path in local_uid_map.items()
                     if uid not in upstream_map}

    if not to_contribute:
        print("\nNothing to contribute -- all local UIDs are already in upstream.")
        return

    # Display grouped by material
    path_str_map = {uid: p.relative_to(LIBRARY_ROOT).as_posix()
                    for uid, p in to_contribute.items()}
    groups = _group_by_material(path_str_map)
    print(f"\n{len(to_contribute)} UID(s) to contribute across {len(groups)} material group(s):\n")
    for mat_key in sorted(groups):
        entries = groups[mat_key]
        print(f"  {mat_key}/  ({len(entries)} UID(s))")
        for colour, uid in sorted(entries):
            print(f"    {colour}/{uid}")

    if not args.apply:
        print()
        print("Preview only -- run with --apply to create/update the PR branch.")
        print()
        print("Prerequisites:")
        print("  - GitHub CLI installed:   https://cli.github.com/")
        print("  - Authenticated:          gh auth login")
        return

    # --- Prerequisites check ---
    if not check_gh_available():
        print("\nERROR: GitHub CLI (gh) is not installed or not authenticated.")
        print("  Install: https://cli.github.com/")
        print("  Then:    gh auth login")
        sys.exit(1)

    owner = get_origin_owner()
    if not owner:
        print("\nERROR: Could not determine GitHub username from origin remote URL.")
        sys.exit(1)

    print(f"\nBuilding branch '{CONTRIBUTION_BRANCH}' from {UPSTREAM_REF} ...")
    worktree_dir = build_contribution_branch(to_contribute)
    push_and_sync_pr(worktree_dir, to_contribute, owner)

    print()
    print(f"Branch '{CONTRIBUTION_BRANCH}' on origin will be updated each run")
    print("until the PR is merged or closed, then a new PR will be opened.")
    print("View/manage the PR:")
    print(f"  gh pr view --repo {UPSTREAM_REPO}")


if __name__ == '__main__':
    main()
