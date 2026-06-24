# -*- coding: utf-8 -*-

# Shared Bambu Studio colour database helpers.
# Used by scanTag.py, fix_library.py, and menu.py.

import json
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Database source locations
# ---------------------------------------------------------------------------

# Authoritative source — maintained by Bambu Lab alongside BambuStudio releases.
COLOR_DB_URL = (
    "https://raw.githubusercontent.com/bambulab/BambuStudio/master"
    "/resources/profiles/BBL/filament/filaments_color_codes.json"
)

# Local fallback — present when Bambu Studio is installed on this machine.
COLOR_DB_LOCAL_PATHS = [
    Path(r"C:\Program Files\Bambu Studio\resources\profiles\BBL\filament\filaments_color_codes.json"),
    Path(r"C:\Program Files (x86)\Bambu Studio\resources\profiles\BBL\filament\filaments_color_codes.json"),
]

# Bundled fallback — committed alongside this script; updated automatically
# whenever a successful GitHub fetch is made.  Ensures the database is always
# available even if the GitHub URL moves or the network is unreachable and
# Bambu Studio is not installed.
BUNDLED_DB_PATH = Path(__file__).parent.resolve() / 'filaments_color_codes.json'

# Network timeout in seconds for the GitHub fetch.
COLOR_DB_TIMEOUT = 5

# fila_color_type values used throughout
SINGLE_TYPE = '单色'
MULTI_TYPES = {'渐变色', '多拼色'}

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _parse_color_db(raw):
    """Extract the list of entries from the parsed JSON (handles {"data":[...]} wrapper)."""
    if isinstance(raw, dict):
        return raw.get('data', [])
    return raw  # already a plain list


def load_color_database(silent=False):
    """
    Load the Bambu Studio filament colour database.

    Tries GitHub first (always up to date); falls back to the locally
    installed copy if the network is unavailable.  Returns a list of
    colour entries, or an empty list if neither source is reachable.

    Pass silent=True to suppress status messages.
    """
    def _msg(s):
        if not silent:
            print(s)

    # --- 1. Try GitHub ---
    try:
        req = urllib.request.Request(
            COLOR_DB_URL,
            headers={'User-Agent': 'BambuRFIDTools/1.0 (Bambu-Research-Group)'},
        )
        with urllib.request.urlopen(req, timeout=COLOR_DB_TIMEOUT) as resp:
            data = resp.read()
        raw = json.loads(data.decode('utf-8'))
        entries = _parse_color_db(raw)
        if entries:
            _msg(f"Loaded colour database from GitHub ({len(entries)} entries).")
            # Refresh the bundled fallback so it stays current.
            try:
                BUNDLED_DB_PATH.write_bytes(data)
            except OSError:
                pass
            return entries
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyboardInterrupt):
        pass  # fall through to local copies

    # --- 2. Fall back to local Bambu Studio installation ---
    for path in COLOR_DB_LOCAL_PATHS:
        if path.exists():
            try:
                with open(path, encoding='utf-8') as f:
                    raw = json.load(f)
                entries = _parse_color_db(raw)
                if entries:
                    _msg(f"(GitHub unreachable — using local Bambu Studio colour database, {len(entries)} entries.)")
                    return entries
            except Exception as e:
                _msg(f"Warning: could not read local colour database at {path}: {e}")

    # --- 3. Fall back to bundled copy shipped with the library ---
    if BUNDLED_DB_PATH.exists():
        try:
            with open(BUNDLED_DB_PATH, encoding='utf-8') as f:
                raw = json.load(f)
            entries = _parse_color_db(raw)
            if entries:
                _msg(f"Warning: GitHub unreachable and Bambu Studio not found.")
                _msg(f"  Using bundled colour database ({len(entries)} entries).")
                _msg(f"  This may be out of date. Update by running with network access.")
                return entries
        except Exception as e:
            _msg(f"Warning: could not read bundled colour database: {e}")

    _msg("Warning: colour database not available — colour name must be entered manually.")
    return []

# ---------------------------------------------------------------------------
# Colour distance helpers
# ---------------------------------------------------------------------------

def _hex_to_rgba(hex_color):
    """Parse a hex colour string into an (R, G, B, A) tuple.
    Accepts #RRGGBB (alpha assumed 255) or #RRGGBBAA."""
    h = hex_color.lstrip('#')
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    a = int(h[6:8], 16) if len(h) >= 8 else 255
    return r, g, b, a


def _color_distance(hex1, hex2):
    """Euclidean RGBA distance between two hex colour strings (alpha included)."""
    r1, g1, b1, a1 = _hex_to_rgba(hex1)
    r2, g2, b2, a2 = _hex_to_rgba(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2 + (a1 - a2) ** 2) ** 0.5


def distance_label(dist):
    """Human-readable qualifier for an RGBA distance value."""
    if dist < 15:
        return "very close \u2014 likely a production batch variance"
    if dist < 40:
        return "approximate match \u2014 same colour family"
    return "distant match \u2014 may be a genuinely different colour"

# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------

def lookup_color_name(tag_data, db):
    """
    Search the Bambu Studio colour database for entries matching this tag's
    hex colour.

    Filters by colour type (单色 / 渐变色 / 多拼色) using filament_color_count so
    that single-colour tags never match gradient entries and vice versa.

    For multi-colour tags, filament_color is slash-joined ("#720062FF / #3A913FFF");
    ALL of the tag's colours must appear in the database entry.

    Returns (exact_name, candidates) where:
      exact_name  -- English name when material type AND hex both matched, else None
      candidates  -- list of (name, fila_type) for entries where only hex matched
    """
    if not db:
        return None, []

    target_colors = [c.strip().upper() for c in tag_data['filament_color'].split('/')]
    target_type   = tag_data['detailed_filament_type']
    is_multi      = tag_data.get('filament_color_count', 1) > 1

    exact_name = None
    candidates = []

    for entry in db:
        entry_color_type = entry.get('fila_color_type', '')
        if is_multi and entry_color_type not in MULTI_TYPES:
            continue
        if not is_multi and entry_color_type != SINGLE_TYPE:
            continue

        colors = [c.upper() for c in entry.get('fila_color', [])]
        if not all(tc in colors for tc in target_colors):
            continue

        name = entry.get('fila_color_name', {}).get('en', '').strip()
        if not name:
            continue

        if entry.get('fila_type') == target_type:
            if exact_name is None:
                exact_name = name
        else:
            candidates.append((name, entry.get('fila_type', '?')))

    return exact_name, candidates


def find_nearest_color(tag_data, db):
    """
    Find the closest colour in the database by Euclidean RGBA distance.

    Uses only the first colour of multi-colour tags (distance is a scalar).
    Prefers entries whose fila_type matches the tag's detailed_filament_type.

    Returns (name, matched_hex, distance, fila_type, is_exact_type).
    """
    if not db:
        return None, None, float('inf'), None, False

    target_color = tag_data['filament_color'].split('/')[0].strip().upper()
    target_type  = tag_data['detailed_filament_type']
    is_multi     = tag_data.get('filament_color_count', 1) > 1

    best_exact = (None, None, float('inf'), None)
    best_any   = (None, None, float('inf'), None)

    for entry in db:
        entry_color_type = entry.get('fila_color_type', '')
        if is_multi and entry_color_type not in MULTI_TYPES:
            continue
        if not is_multi and entry_color_type != SINGLE_TYPE:
            continue

        name = entry.get('fila_color_name', {}).get('en', '').strip()
        if not name:
            continue

        ftype = entry.get('fila_type', '')

        for hex_c in entry.get('fila_color', []):
            try:
                dist = _color_distance(target_color, hex_c.upper())
            except Exception:
                continue
            if ftype == target_type and dist < best_exact[2]:
                best_exact = (name, hex_c, dist, ftype)
            if dist < best_any[2]:
                best_any = (name, hex_c, dist, ftype)

    if best_exact[0] is not None:
        name, hex_c, dist, ftype = best_exact
        return name, hex_c, dist, ftype, True
    if best_any[0] is not None:
        name, hex_c, dist, ftype = best_any
        return name, hex_c, dist, ftype, False
    return None, None, float('inf'), None, False
