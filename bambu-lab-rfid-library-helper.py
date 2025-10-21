#!/usr/bin/env python3

"""
Bambulab RFID Tag Reader/Writer Tool

WARNING: This is experimental software. Authors and distributors are NOT liable
for any damages, data loss, or hardware issues. Use at your own risk.
See full readme: https://github.com/queengooborg/Bambu-Lab-RFID-Library/README.md
"""

import os
import re
import sys
import json
import shutil
import tempfile
import logging
import platform
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, ClassVar
from contextlib import contextmanager

try:
    from prettytable import PrettyTable, TableStyle
except ImportError:
    logging.critical("prettytable module not found (pip install prettytable)")
    sys.exit(1)

BYTES_PER_BLOCK: int = 16


class LoggerMixin:

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


@dataclass
class Config:

    PM3_SEARCH_PATHS: ClassVar[List[str]] = [
        "/opt/proxmark3/pm3",
        "/usr/local/bin/pm3",
        "/usr/bin/pm3",
        "C:/opt/proxmark3/pm3.exe",
        "C:/Program Files/proxmark3/pm3.exe",
        os.path.expanduser("~/proxmark3/pm3"),
    ]

    pm3_path: Optional[Path] = None
    dump_base_dir: Path = field(default_factory=lambda: Path.cwd())

    def __post_init__(self):
        if self.pm3_path is None:
            self.pm3_path = self._find_proxmark3()

        env_pm3 = os.environ.get("PM3_PATH")
        if env_pm3:
            self.pm3_path = Path(env_pm3)

        env_dump = os.environ.get("DUMP_BASE_DIR")
        if env_dump:
            self.dump_base_dir = Path(env_dump)

        self._normalize_paths()

    def _find_proxmark3(self) -> Path:
        system = platform.system()

        for path_str in self.PM3_SEARCH_PATHS:
            path = Path(path_str).expanduser()

            if system == "Windows":
                if not str(path).endswith(".exe"):
                    path = path.with_suffix(".exe")

            if path.is_file() and os.access(path, os.X_OK):
                return path

        raise RuntimeError(f"proxmark3 not found. Searched: {', '.join(self.PM3_SEARCH_PATHS)}\n" f"Set PM3_PATH environment variable or install proxmark3.")

    def _normalize_paths(self):
        self.pm3_path = self.pm3_path.resolve()
        self.dump_base_dir = self.dump_base_dir.resolve()

    def validate(self):
        if not self.pm3_path.is_file():
            raise RuntimeError(f"proxmark3 not found: {self.pm3_path}")

        if not os.access(self.pm3_path, os.X_OK):
            raise RuntimeError(f"proxmark3 not executable: {self.pm3_path}")


class ColorDataLoader(LoggerMixin):
    """Loads and provides access to Bambu Studio filament color data."""

    COLOR_DATA_PATHS = {
        "Windows": Path(os.environ.get("APPDATA", "")) / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
        "Darwin": Path.home() / "Library" / "Application Support" / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
        "Linux": Path.home() / ".config" / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
    }

    FILAMENT_TYPE_MAPPING = {
        "PVA": "Support",
        "PA6": "PA",
    }

    def __init__(self, custom_path: Optional[Path] = None):
        self.color_data = {}
        self.filament_data = []
        self.color_hex_to_name = {}
        self._load_color_data(custom_path)

    def _get_color_data_path(self) -> Path:
        system = platform.system()
        path = self.COLOR_DATA_PATHS.get(system)

        if not path:
            raise RuntimeError(f"unsupported platform: {system}")

        return path

    def _load_color_data(self, custom_path: Optional[Path] = None):
        if custom_path:
            color_file = custom_path
        else:
            try:
                color_file = self._get_color_data_path()
            except RuntimeError:
                script_dir = Path(__file__).parent
                color_file = script_dir / "filaments_color_codes.json"
                self.logger.warning(f"Using fallback location: {color_file}")

        if not color_file.exists():
            script_dir = Path(__file__).parent
            color_file = script_dir / "filaments_color_codes.json"
            self.logger.warning(f"Using script directory fallback: {color_file}")

        if not color_file.exists():
            raise FileNotFoundError(f"Color data file not found: {color_file}")

        try:
            with open(color_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.filament_data = data.get("data", [])

            for item in self.filament_data:
                code = item.get("fila_color_code")
                if code:
                    self.color_data[code] = {
                        "fila_color": item.get("fila_color", []),
                        "fila_type": item.get("fila_type", ""),
                        "fila_id": item.get("fila_id", ""),
                        "fila_color_name": item.get("fila_color_name", {}),
                    }

                colors = item.get("fila_color", [])
                color_name = item.get("fila_color_name", {}).get("en", "Unknown")

                for hex_val in colors:
                    hex_clean = hex_val.lstrip("#").upper()
                    self.color_hex_to_name[hex_clean] = color_name

                    if len(hex_clean) >= 6:
                        self.color_hex_to_name[hex_clean[:6]] = color_name

            self.logger.info(f"Loaded {len(self.color_data)} filament entries from: {color_file}")
            self.logger.debug(f"Built color hex mapping with {len(self.color_hex_to_name)} entries")

        except Exception as e:
            self.logger.error(f"Failed to load color data: {e}")
            raise

    def hex_to_color_name(self, hex_color: str) -> str:
        """Convert hex color to closest matching color name from database."""
        hex_color = hex_color.lstrip("#").upper()

        if hex_color in self.color_hex_to_name:
            return self.color_hex_to_name[hex_color]

        hex_rgb = hex_color[:6]
        if hex_rgb in self.color_hex_to_name:
            return self.color_hex_to_name[hex_rgb]

        hex_with_alpha = hex_rgb + "FF"
        if hex_with_alpha in self.color_hex_to_name:
            return self.color_hex_to_name[hex_with_alpha]

        target_rgb = tuple(int(hex_rgb[i : i + 2], 16) for i in (0, 2, 4))

        min_dist = float("inf")
        closest_name = "Unknown"

        for hex_val, name in self.color_hex_to_name.items():
            hex_val_rgb = hex_val[:6]
            rgb = tuple(int(hex_val_rgb[i : i + 2], 16) for i in (0, 2, 4))
            dist = sum((a - b) ** 2 for a, b in zip(target_rgb, rgb))
            if dist < min_dist:
                min_dist = dist
                closest_name = name

        return closest_name

    def normalize_filament_type(self, filament_type: str) -> str:
        """Normalize filament type string for filesystem usage."""
        return filament_type.replace("/", "-").strip()

    def get_filament_category(self, filament_type: str) -> str:
        """Extract the category from a filament type, applying mapping rules."""
        normalized = self.normalize_filament_type(filament_type)
        category = re.split(r"[\s-]+", normalized)[0] if normalized else ""

        ft_upper = normalized.upper()
        for pattern, mapped_category in self.FILAMENT_TYPE_MAPPING.items():
            if ft_upper.startswith(pattern):
                return mapped_category

        return category

    def find_by_type_and_color(self, filament_type: str, color_name: str) -> Optional[Dict]:
        """Find filament data by type and color name."""
        normalized_type = self.normalize_filament_type(filament_type)

        for item in self.filament_data:
            item_type = self.normalize_filament_type(item.get("fila_type", ""))
            item_color = item.get("fila_color_name", {}).get("en", "")

            if item_type == normalized_type and item_color == color_name:
                return item

        return None

    def get_color_hex(self, filament_code: str) -> Optional[str]:
        """Get the hex color code for a filament code."""
        item = self.color_data.get(filament_code, {})
        colors = item.get("fila_color", [])
        return colors[0] if colors else None

    def get_filament_type(self, filament_code: str) -> Optional[str]:
        """Get the filament type for a filament code."""
        item = self.color_data.get(filament_code, {})
        return item.get("fila_type")

    def get_variant_id(self, filament_code: str) -> Optional[str]:
        """Get the variant ID for a filament code."""
        item = self.color_data.get(filament_code, {})
        return item.get("fila_id")

    def get_color_name(self, filament_code: str, language: str = "en") -> Optional[str]:
        """Get the color name for a filament code in a specific language."""
        item = self.color_data.get(filament_code, {})
        names = item.get("fila_color_name", {})
        return names.get(language)

    def get_all_by_type(self) -> Dict[str, List[Dict]]:
        """Get all filament data grouped by filament type."""
        filament_types = {}
        for item in self.filament_data:
            fila_type = item.get("fila_type", "Unknown")
            if fila_type not in filament_types:
                filament_types[fila_type] = []
            filament_types[fila_type].append(item)
        return filament_types


class FilesystemScanner(LoggerMixin):
    """Scans filesystem for dumped RFID tags to determine status."""

    def __init__(self, base_path: Path, color_loader: ColorDataLoader):
        self.base_path = base_path
        self.color_loader = color_loader
        self.tag_cache = {}
        self.non_compliant_folders = set()
        self.partial_folders = set()
        self._scan_tags()

    def _scan_tags(self):
        """Scan for hf-mf-*-dump.bin and hf-mf-*-key*.bin pairs."""
        self.logger.info(f"Scanning for tag dumps in: {self.base_path}")

        for dump_file in self.base_path.rglob("hf-mf-*-dump.bin"):
            uid_match = re.search(r"hf-mf-([A-F0-9]+)-dump", dump_file.name)
            if not uid_match:
                continue

            uid = uid_match.group(1)
            key_files = list(dump_file.parent.glob(f"hf-mf-{uid}-key*.bin"))

            if key_files:
                parts = dump_file.relative_to(self.base_path).parts

                if len(parts) >= 4:
                    filament_category = parts[0]
                    detailed_type = parts[1]
                    color = parts[2]
                    uid_folder = parts[3]

                    self.tag_cache[uid] = {"category": filament_category, "detailed_type": detailed_type, "color": color, "uid_folder": uid_folder, "path": dump_file.parent, "has_complete_data": True}

                    self.logger.debug(f"Found tag: {uid} ({filament_category}/{detailed_type}/{color}/{uid_folder})")

        self._scan_non_compliant_folders()
        self.logger.info(f"Found {len(self.tag_cache)} complete tag dumps")
        if self.tag_cache:
            self.logger.debug("Tag cache entries:")
            for uid, data in self.tag_cache.items():
                self.logger.debug(f"  {uid}: {data['category']}/{data['detailed_type']}/{data['color']}/{data['uid_folder']}")
        self.logger.info(f"Found {len(self.non_compliant_folders)} non-compliant folders")
        self.logger.info(f"Found {len(self.partial_folders)} partially populated folders")

    def _scan_non_compliant_folders(self):
        """Scan for folders with files but missing proper PM3 tag structure."""
        if not self.base_path.exists():
            return

        color_folder_status = {}

        for item in self.base_path.rglob("*"):
            if not item.is_dir():
                continue

            files = [f for f in item.iterdir() if f.is_file()]
            if not files:
                continue

            parts = item.relative_to(self.base_path).parts
            if len(parts) != 4:
                continue

            category = parts[0]
            detailed_type = parts[1]
            color = parts[2]
            uid_folder = parts[3]

            color_key = (category, detailed_type, color)

            has_dump = any(f.name == f"hf-mf-{uid_folder}-dump.bin" for f in files)
            has_key = any(f.name.startswith(f"hf-mf-{uid_folder}-key") and f.name.endswith(".bin") for f in files)

            if color_key not in color_folder_status:
                color_folder_status[color_key] = {"compliant": 0, "non_compliant": 0}

            if has_dump and has_key:
                color_folder_status[color_key]["compliant"] += 1
            else:
                color_folder_status[color_key]["non_compliant"] += 1

        for color_key, status in color_folder_status.items():
            if status["compliant"] == 0 and status["non_compliant"] > 0:
                self.non_compliant_folders.add(color_key)
            elif status["compliant"] > 0 and status["non_compliant"] > 0:
                self.partial_folders.add(color_key)

    def get_status(self, filament_type: str, color_name: str) -> str:
        """Determine status icon for a filament type and color."""
        normalized_type = self.color_loader.normalize_filament_type(filament_type)
        category = self.color_loader.get_filament_category(filament_type)

        self.logger.debug(f"Checking status for: type='{filament_type}' -> normalized='{normalized_type}', category='{category}', color='{color_name}'")

        color_key = (category, normalized_type, color_name)

        if color_key in self.non_compliant_folders:
            return "⚠️"

        if color_key in self.partial_folders:
            return "👀"

        for uid, tag_data in self.tag_cache.items():
            self.logger.debug(f"  Comparing with tag {uid}: cat={tag_data['category']}, type={tag_data['detailed_type']}, color={tag_data['color']}")
            if tag_data["category"] == category and tag_data["detailed_type"] == normalized_type and tag_data["color"] == color_name:
                self.logger.debug(f"  ✅ MATCH found for {uid}")
                return "✅"

        return "❌"


class TableGenerator(LoggerMixin):
    """Generates markdown tables from filament data."""

    def __init__(self, color_loader: ColorDataLoader, scanner: Optional[FilesystemScanner] = None):
        self.color_loader = color_loader
        self.scanner = scanner

    def generate_table_from_json(self, existing_data: Optional[Dict] = None) -> str:
        """Generate complete markdown output from JSON data."""
        output = "## List of Bambu Lab Materials + Colors\n\n"
        output += "Status Icon Legend:\n"
        output += "- ✅: Have complete tag data\n"
        output += "- ❌: No tag scanned\n"
        output += "- 👀: Folder has at least one compliant UID but also has non-compliant UIDs\n"
        output += "- ⚠️: Folder exists with files but ALL UIDs missing proper PM3 tag structure\n\n"

        filament_types = self.color_loader.get_all_by_type()

        for fila_type in sorted(filament_types.keys()):
            output += f"### {fila_type}\n\n"

            table = PrettyTable()
            table.set_style(TableStyle.MARKDOWN)
            table.align = "l"
            table.field_names = ["Color", "Filament Code", "Color Hex", "Variant ID", "Status"]

            for item in sorted(filament_types[fila_type], key=lambda x: x.get("fila_color_code", "")):
                color_name = item.get("fila_color_name", {}).get("en", "Unknown")
                filament_code = item.get("fila_color_code", "?")
                fila_color = item.get("fila_color", ["?"])[0]
                variant_id = item.get("fila_id", "?")
                filament_type = item.get("fila_type", "")

                if self.scanner:
                    status = self.scanner.get_status(filament_type, color_name)
                elif existing_data and filament_code in existing_data:
                    status = existing_data[filament_code].get("status", "❌")
                else:
                    status = "❌"

                table.add_row([color_name, filament_code, fila_color, variant_id, status])

            output += table.get_string().replace(":-", "--").replace("-|", " |")
            output += "\n\n"

        return output

    def update_readme(self, readme_path: Path, dry_run: bool = False) -> str:
        """Update datasheet with new filament data, determining status from filesystem."""
        output = self.generate_table_from_json()

        if not dry_run:
            readme_path.write_text(output, encoding="utf-8")
            self.logger.info(f"Updated datasheet: {readme_path}")
        else:
            self.logger.info("Dry run mode - no files written")

        return output


@dataclass(frozen=True)
class TagInfo:

    uid: str
    filament_type: str
    detailed_filament_type: str
    color_hex: str
    _color_loader: Optional[ColorDataLoader] = field(default=None, repr=False, compare=False)

    @property
    def color_name(self) -> str:
        if self._color_loader:
            try:
                return self._color_loader.hex_to_color_name(self.color_hex)
            except Exception:
                return self.color_hex
        return self.color_hex

    @property
    def detailed_type(self) -> str:
        return self.detailed_filament_type or self.filament_type

    def get_path(self, base_dir: Path) -> Path:
        color_dir_name = self.color_name if self._color_loader else self.color_hex
        path = base_dir / self.filament_type / self.detailed_type / color_dir_name / self.uid
        return path.resolve()

    def __str__(self) -> str:
        return f"UID: {self.uid}\n" f"Type: {self.filament_type} / {self.detailed_type}\n" f"Color: {self.color_name} (#{self.color_hex})"


@dataclass
class TagFiles:

    dump_file: Path
    key_file: Path
    tag_id: str

    @classmethod
    def from_directory(cls, directory: Path) -> "TagFiles":
        if not directory.is_dir():
            raise NotADirectoryError(f"not a directory: {directory}")

        dump_files = list(directory.glob("hf-mf-*-dump.bin"))

        if not dump_files:
            raise FileNotFoundError(f"no dump file found in: {directory}")

        dump_file = dump_files[0]
        tag_id = dump_file.stem.split("-")[2]

        key_candidates = list(directory.glob(f"hf-mf-{tag_id}-key*.bin"))
        if not key_candidates:
            raise FileNotFoundError(f"matching key file not found for tag {tag_id}")

        return cls(dump_file=dump_file, key_file=key_candidates[0], tag_id=tag_id)


class TagParser:

    def __init__(self, color_loader: Optional[ColorDataLoader] = None):
        self.color_loader = color_loader

    @staticmethod
    def bytes_to_string(data: bytes) -> str:
        return data.decode("ascii", errors="ignore").replace("\x00", " ").strip()

    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        return data.hex().upper()

    def parse(self, data: bytes) -> TagInfo:
        blocks = [data[i : i + BYTES_PER_BLOCK] for i in range(0, len(data), BYTES_PER_BLOCK)]

        if len(blocks) < 6:
            raise ValueError(f"insufficient data blocks: {len(blocks)}")

        return TagInfo(uid=self.bytes_to_hex(blocks[0][0:4]), filament_type=self.bytes_to_string(blocks[2]), detailed_filament_type=self.bytes_to_string(blocks[4]), color_hex=self.bytes_to_hex(blocks[5][0:4]), _color_loader=self.color_loader)


class Proxmark3(LoggerMixin):

    def __init__(self, config: Config):
        self.config = config

    def _path_for_pm3(self, path: Path) -> str:
        return path.as_posix()

    def _run(self, command: str, capture: bool = False) -> subprocess.CompletedProcess:
        full_command = [str(self.config.pm3_path), "-c", command]
        self.logger.debug(f"Executing: {' '.join(repr(c) for c in full_command)}")

        try:
            return subprocess.run(full_command, capture_output=True, text=True, timeout=30, shell=False) if capture else subprocess.run(full_command, stderr=subprocess.STDOUT, timeout=30, shell=False)
        except subprocess.TimeoutExpired:
            raise RuntimeError("proxmark3 command timed out")

    def check_tag(self) -> Optional[str]:
        self.logger.info("Checking for tag presence...")
        result = self._run("hf mf info", capture=True)
        output = result.stdout + result.stderr

        self.logger.debug(f"hf mf info output:\n{output}")

        if result.returncode != 0:
            raise RuntimeError("failed to read tag - check tag position")

        uid = None
        for line in output.split("\n"):
            if "UID" in line or "uid" in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.upper() in ["UID", "UID:"]:
                        hex_bytes = []
                        for j in range(i + 1, len(parts)):
                            if len(parts[j]) == 2 and all(c in "0123456789ABCDEFabcdef" for c in parts[j]):
                                hex_bytes.append(parts[j])
                            else:
                                break
                        if hex_bytes:
                            uid = "".join(hex_bytes).upper()
                            break
                if uid:
                    break

        self.logger.info(f"Tag detected with UID: {uid}")
        return uid

    def get_tag_type(self) -> str:
        self.logger.info("Identifying tag type...")
        result = self._run("hf mf info", capture=True)
        output = result.stdout + result.stderr

        self.logger.debug(f"hf mf info output:\n{output}")

        if "iso14443a card select failed" in output.lower():
            raise RuntimeError("Tag not found or is wrong type")

        magic_section_found = False
        capabilities = []

        for line in output.split("\n"):
            if "--- Magic Tag Information" in line:
                magic_section_found = True
                continue

            if magic_section_found:
                if line.startswith("[=] ---"):
                    break

                if "[=] <n/a>" in line:
                    raise RuntimeError("Tag is not a compatible magic type, or has already been locked")

                if "Magic capabilities" in line:
                    capabilities.append(line)

        if not magic_section_found:
            raise RuntimeError("Could not obtain magic tag information")

        if not capabilities:
            raise RuntimeError("Tag is not a compatible magic type (must be Gen 4 FUID or UFUID)")

        caps_str = "\n".join(capabilities)

        if "Gen 4 GDM / USCUID ( ZUID Gen1 Magic Wakeup )" in caps_str:
            self.logger.info("Detected: Gen 4 UFUID")
            return "UFUID"
        elif "Gen 4 GDM / USCUID ( Gen4 Magic Wakeup )" in caps_str:
            self.logger.info("Detected: Gen 4 FUID")
            return "FUID"
        elif "Write Once / FUID" in caps_str:
            self.logger.info("Write Once / FUID capability detected, falling back to Gen 2 FUID")
            return "FUID"

        raise RuntimeError("Tag is not a compatible type (must be Gen 4 FUID or UFUID)")

    def read_keys(self, tmp_dir: Path) -> str:
        self.logger.info("Reading Bambulab keys from tag...")
        result = self._run("hf mf bambukeys -r -d", capture=True)
        output = result.stdout + result.stderr

        self.logger.debug(f"hf mf bambukeys output:\n{output}")

        if result.returncode != 0:
            self.logger.error(f"Command failed with return code: {result.returncode}")
            self.logger.error(f"Output: {output}")
            raise RuntimeError("failed to read tag keys")

        key_file_path = next((line[line.find("`") + 1 : line.rfind("`")] for line in output.split("\n") if "Saved" in line and "binary file" in line and "`" in line), None)

        if not key_file_path:
            self.logger.error("Could not find key file path in output")
            self.logger.error(f"Full output:\n{output}")
            raise RuntimeError("no key file in output")

        key_file = Path(key_file_path)
        if not key_file.exists():
            self.logger.error(f"Key file was reported but doesn't exist: {key_file}")
            raise RuntimeError(f"key file not found: {key_file}")

        dest = tmp_dir / key_file.name
        shutil.move(str(key_file), str(dest))
        self.logger.info(f"Keys saved to: {dest.name}")
        return key_file.name

    def dump_tag(self, key_file: str, tmp_dir: Path) -> str:
        uid = key_file[key_file.find("hf-mf-") + 6 : key_file.find("-key")]
        if not uid:
            raise RuntimeError(f"cannot extract UID from key file: {key_file}")

        dump_file = f"hf-mf-{uid}-dump.bin"
        key_path = (tmp_dir / key_file).resolve()
        dump_path = (tmp_dir / dump_file).resolve()

        self.logger.info(f"Dumping tag contents for UID: {uid}")

        command = f'hf mf dump -k "{self._path_for_pm3(key_path)}" -f "{self._path_for_pm3(dump_path)}"'
        result = self._run(command, capture=True)

        self.logger.debug(f"hf mf dump output:\n{result.stdout + result.stderr}")

        if result.returncode != 0 or not dump_path.exists():
            raise RuntimeError("dump failed")

        self.logger.info(f"Dump saved to: {dump_file}")
        return dump_file

    def write_tag(self, tag_files: TagFiles, tag_type: str) -> bool:
        self.logger.info(f"Writing tag data for UID: {tag_files.tag_id} (type: {tag_type})")

        dump_path = tag_files.dump_file.resolve()
        key_path = tag_files.key_file.resolve()

        if tag_type == "FUID":
            command = f'hf mf restore --force -f "{self._path_for_pm3(dump_path)}" -k "{self._path_for_pm3(key_path)}"'
            result = self._run(command, capture=True)
            self.logger.debug(f"write output:\n{result.stdout + result.stderr}")

            if result.returncode != 0:
                raise RuntimeError("write failed")

        elif tag_type == "UFUID":
            self.logger.info("Using UFUID write sequence (cload + seal)")

            commands = [
                f'hf mf cload -f "{self._path_for_pm3(dump_path)}"',
                "hf 14a raw -a -k -b 7 40",
                "hf 14a raw -k 43",
                "hf 14a raw -k -c e100",
                "hf 14a raw -c 85000000000000000000000000000008",
            ]

            for step_number, command in enumerate(commands, 1):
                self.logger.debug(f"UFUID step {step_number}/{len(commands)}: {command}")
                result = self._run(command, capture=True)
                self.logger.debug(f"step {step_number} output:\n{result.stdout + result.stderr}")

                if result.returncode != 0:
                    raise RuntimeError(f"UFUID write failed at step {step_number}")

        else:
            raise RuntimeError(f"unsupported tag type: {tag_type}")

        self.logger.info("Write operation completed")
        return True


class BaseOperation(ABC, LoggerMixin):

    def __init__(self, config: Config):
        self.config = config
        self.pm3 = Proxmark3(config)
        self.color_loader = self._load_color_data()
        self.tag_parser = TagParser(self.color_loader)

    def _load_color_data(self) -> Optional[ColorDataLoader]:
        """Attempt to load color data, but don't fail if unavailable."""
        try:
            return ColorDataLoader()
        except FileNotFoundError:
            self.logger.warning("Color database not found, color names will be hex values")
            return None

    @abstractmethod
    def run(self, *args, **kwargs):
        pass


class RFIDIdentifier(BaseOperation):

    def run(self):
        input("Place tag on antenna, press Enter...")

        uid = self.pm3.check_tag()
        tag_type = self.pm3.get_tag_type()

        self.logger.info("Tag Identification:")
        self.logger.info(f"  UID: {uid}")
        self.logger.info(f"  Type: Gen 4 {tag_type}")


class RFIDReader(BaseOperation):

    def run(self):
        input("Place tag on antenna, press Enter...")

        uid = self.pm3.check_tag()

        self.logger.info("Reading tag data...")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir).resolve()

            key_file = self.pm3.read_keys(tmp_dir)
            dump_file = self.pm3.dump_tag(key_file, tmp_dir)

            with open(tmp_dir / dump_file, "rb") as f:
                tag_info = self.tag_parser.parse(f.read())

            self.logger.info("Tag Information:")
            self.logger.info(f"  UID: {tag_info.uid}")
            self.logger.info(f"  Type: {tag_info.filament_type} / {tag_info.detailed_type}")
            self.logger.info(f"  Color: {tag_info.color_name} (#{tag_info.color_hex})")


class RFIDVerifier(BaseOperation):

    def run(self, directory: Path):
        tag_files = TagFiles.from_directory(directory)

        with open(tag_files.dump_file, "rb") as f:
            expected_info = self.tag_parser.parse(f.read())

        self.logger.info("Expected tag data (from file):")
        self.logger.info(f"  UID: {expected_info.uid}")
        self.logger.info(f"  Type: {expected_info.filament_type} / {expected_info.detailed_type}")
        self.logger.info(f"  Color: {expected_info.color_name} (#{expected_info.color_hex})")

        input("\nPlace tag on antenna, press Enter...")

        self.logger.info("Reading physical tag...")
        physical_uid = self.pm3.check_tag()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir).resolve()

            try:
                key_file = self.pm3.read_keys(tmp_dir)
                dump_file = self.pm3.dump_tag(key_file, tmp_dir)

                with open(tmp_dir / dump_file, "rb") as f:
                    physical_info = self.tag_parser.parse(f.read())

                self.logger.info("Physical tag data (from reader):")
                self.logger.info(f"  UID: {physical_info.uid}")
                self.logger.info(f"  Type: {physical_info.filament_type} / {physical_info.detailed_type}")
                self.logger.info(f"  Color: {physical_info.color_name} (#{physical_info.color_hex})")

                checks = [
                    ("UID", expected_info.uid, physical_info.uid),
                    ("Filament Type", expected_info.filament_type, physical_info.filament_type),
                    ("Detailed Type", expected_info.detailed_filament_type, physical_info.detailed_filament_type),
                    ("Color Hex", expected_info.color_hex, physical_info.color_hex),
                ]

                self.logger.info("Verification results:")
                all_match = True
                for field, expected, actual in checks:
                    match = expected == actual
                    all_match = all_match and match
                    status = "MATCH" if match else "MISMATCH"
                    self.logger.info(f"  {field}: {status} (expected: {expected}, actual: {actual})")

                if all_match:
                    self.logger.info("Verification PASSED - all fields match")
                else:
                    self.logger.warning("Verification FAILED - mismatch detected")

            except Exception as e:
                self.logger.error(f"Failed to read physical tag: {e}")
                raise


class RFIDDumper(BaseOperation):

    def _confirm_write(self, tag_info: TagInfo, target_dir: Path) -> bool:
        self.logger.info("Tag parsed successfully")
        self.logger.info(f"  UID: {tag_info.uid}")
        self.logger.info(f"  Type: {tag_info.filament_type} / {tag_info.detailed_type}")
        self.logger.info(f"  Color: {tag_info.color_name} (#{tag_info.color_hex})")
        self.logger.info(f"Target directory: {target_dir}")

        response = input("\nWrite files to this location? [Y/n]: ")
        return response.lower() not in ("n", "no")

    def _organize_files(self, dump_file: str, tmp_dir: Path) -> Path:
        with open(tmp_dir / dump_file, "rb") as f:
            tag_info = self.tag_parser.parse(f.read())

        target_dir = tag_info.get_path(self.config.dump_base_dir)

        if not self._confirm_write(tag_info, target_dir):
            raise RuntimeError("aborted by user")

        target_dir.mkdir(parents=True, exist_ok=True)

        for item in tmp_dir.iterdir():
            dest = target_dir / item.name
            shutil.move(str(item), str(dest))
            self.logger.debug(f"Moved: {item.name} -> {dest}")

        return target_dir

    @contextmanager
    def _temp_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir).resolve()
            self.logger.debug(f"Created temporary directory: {tmp_path}")
            yield tmp_path

    def run(self):
        with self._temp_directory() as tmp_dir:
            input("Place tag on antenna, press Enter...")

            self.pm3.check_tag()
            key_file = self.pm3.read_keys(tmp_dir)
            dump_file = self.pm3.dump_tag(key_file, tmp_dir)
            target_dir = self._organize_files(dump_file, tmp_dir)

            self.logger.info(f"Successfully saved to: {target_dir}")
            for item in sorted(target_dir.iterdir()):
                self.logger.info(f"  {item.name} ({item.stat().st_size} bytes)")


class RFIDWriter(BaseOperation):

    def _display_tag_info(self, tag_info: TagInfo, tag_files: TagFiles):
        self.logger.info("Tag information:")
        self.logger.info(f"  UID: {tag_info.uid}")
        self.logger.info(f"  Type: {tag_info.filament_type} / {tag_info.detailed_type}")
        self.logger.info(f"  Color: {tag_info.color_name} (#{tag_info.color_hex})")
        self.logger.info("Files:")
        self.logger.info(f"  Dump: {tag_files.dump_file}")
        self.logger.info(f"  Keys: {tag_files.key_file}")
        self.logger.info(f"  Tag ID: {tag_files.tag_id}")

    def _confirm_write(self) -> bool:
        response = input("\nWrite to tag? [y/N]: ")
        return response.lower() in ("y", "yes")

    def _verify_write(self, expected_uid: str):
        self.logger.info("Verifying UID write...")
        written_uid = self.pm3.check_tag()

        if written_uid:
            if written_uid == expected_uid:
                self.logger.info(f"Success! UID {expected_uid} is now locked in.")
            else:
                self.logger.warning(f"UID mismatch. Expected {expected_uid}, got {written_uid}")
        else:
            self.logger.warning("Could not extract UID from verification read")

    def run(self, directory: Path):
        tag_files = TagFiles.from_directory(directory)

        with open(tag_files.dump_file, "rb") as f:
            tag_info = self.tag_parser.parse(f.read())

        self._display_tag_info(tag_info, tag_files)

        self.logger.info("Checking for blank tag...")
        self.pm3.check_tag()

        tag_type = self.pm3.get_tag_type()

        if not self._confirm_write():
            raise RuntimeError("aborted by user")

        self.logger.info(f"Writing to tag ({tag_type} mode)...")
        self.pm3.write_tag(tag_files, tag_type)

        self._verify_write(tag_info.uid)


class DatasheetUpdater(LoggerMixin):
    """Updates filament datasheet with tag scan status."""

    def run(self, args: List[str]):
        custom_json_path = None
        scan_path = Path.cwd()
        datasheet_path = Path("./bambulab_filament_datasheet.md")
        output_path = None
        dry_run = False

        i = 0
        while i < len(args):
            if args[i] == "--json" and i + 1 < len(args):
                custom_json_path = Path(args[i + 1])
                i += 2
            elif args[i] == "--scan" and i + 1 < len(args):
                scan_path = Path(args[i + 1])
                i += 2
            elif args[i] == "--datasheet" and i + 1 < len(args):
                datasheet_path = Path(args[i + 1])
                i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output_path = Path(args[i + 1])
                i += 2
            elif args[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                self.logger.error(f"Unknown argument: {args[i]}")
                self._print_usage()
                return False

        try:
            self.logger.info("Loading filament color data...")
            color_loader = ColorDataLoader(custom_json_path)

            self.logger.info("Scanning filesystem for tag dumps...")
            scanner = FilesystemScanner(scan_path, color_loader)

            self.logger.info("Generating table...")
            generator = TableGenerator(color_loader, scanner)

            if output_path:
                output = generator.generate_table_from_json()
                if not dry_run:
                    output_path.write_text(output, encoding="utf-8")
                    self.logger.info(f"Output written to: {output_path}")
                else:
                    self.logger.info(f"Dry run mode - output would be written to: {output_path}")
                    print(output)
            else:
                output = generator.update_readme(datasheet_path, dry_run=dry_run)
                if dry_run:
                    print(output)

            return True

        except (RuntimeError, FileNotFoundError) as e:
            self.logger.error(str(e))
            return False

    def _print_usage(self):
        print("\nDatasheet Update Options:")
        print("  --json <path>       Use custom JSON file path")
        print("  --scan <path>       Base directory to scan for tag dumps (default: current directory)")
        print("  --datasheet <path>  Datasheet file to update (default: ./bambulab_filament_datasheet.md)")
        print("  --output <path>     Write output to file instead of updating datasheet")
        print("  --dry-run           Show what would be written without actually writing")


class CLIApplication(LoggerMixin):

    MODES = {
        "dump": ("Read and dump RFID tag to organized directory structure", RFIDDumper),
        "read": ("Read and display RFID tag information without saving", RFIDReader),
        "id": ("Identify blank magic tag type (FUID vs UFUID)", RFIDIdentifier),
        "write": ("Write/clone tag data from directory to FUID tag", RFIDWriter),
        "clone": ("Alias for write mode", RFIDWriter),
        "verify": ("Verify physical tag matches stored tag data", RFIDVerifier),
        "update-db": ("Update filament datasheet with current tag scan status", None),
    }

    def __init__(self):
        self._setup_logging()

    def _show_disclaimer(self):
        print("WARNING: Experimental software. No liability for damages. Use at own risk.")
        response = input("Accept? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)
        print()

    def _setup_logging(self):
        level = logging.DEBUG if os.environ.get("DEBUG") or os.environ.get("VERBOSE") else logging.INFO

        class CustomFormatter(logging.Formatter):

            FORMATS = {
                logging.DEBUG: "[?]",
                logging.INFO: "[i]",
                logging.WARNING: "[!]",
                logging.ERROR: "[e]",
                logging.CRITICAL: "[c]",
            }

            def format(self, record):
                status = self.FORMATS.get(record.levelno, "[?]")
                date_str = self.formatTime(record, "%Y-%b-%d")
                return f"{status}[{date_str}][{record.name}]: {record.getMessage()}"

        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())

        logging.root.handlers = []
        logging.root.addHandler(handler)
        logging.root.setLevel(level)

    def _print_usage(self):
        print("Usage: python3 bambu-lab-rfid-library-helper.py <mode> [arguments] [options]")
        print("\nModes:")
        for mode, (description, _) in self.MODES.items():
            print(f"  {mode:10s} {description}")
        print("\nOptions:")
        print("  --accept-eula    Skip EULA prompt")
        print("  --verbose, -v    Enable verbose debug logging")
        print("\nExamples:")
        print("  python3 bambu-lab-rfid-library-helper.py id")
        print("  python3 bambu-lab-rfid-library-helper.py read")
        print("  python3 bambu-lab-rfid-library-helper.py dump --accept-eula --verbose")
        print('  python3 bambu-lab-rfid-library-helper.py write "/path/to/PETG/PETG HF/White/E3D1DC36"')
        print('  python3 bambu-lab-rfid-library-helper.py verify "/path/to/tag" --accept-eula -v')
        print("  python3 bambu-lab-rfid-library-helper.py update-db --scan . --datasheet ./datasheet.md")
        print("\nEnvironment Variables:")
        print("  PM3_PATH          Path to proxmark3 binary")
        print("  DUMP_BASE_DIR     Base directory for tag storage (default: current directory)")
        print("  DEBUG/VERBOSE     Enable debug logging")
        print("\nPM3_PATH Examples:")
        print("  Linux:   export PM3_PATH=/opt/proxmark3/pm3")
        print("  macOS:   export PM3_PATH=/usr/local/bin/pm3")
        print("  Windows: set PM3_PATH=C:\\opt\\proxmark3\\pm3.exe")
        print('           or: $env:PM3_PATH="C:\\Program Files\\proxmark3\\pm3.exe"')
        print("\nNote: Paths with spaces must be quoted on all platforms.")

    def run(self, args: List[str]):
        accept_eula = "--accept-eula" in args
        verbose = "--verbose" in args or "-v" in args

        args = [arg for arg in args if arg not in ("--accept-eula", "--verbose", "-v")]

        if verbose:
            os.environ["VERBOSE"] = "1"
            logging.getLogger().setLevel(logging.DEBUG)

        if len(args) < 1:
            self._print_usage()
            sys.exit(1)

        mode = args[0].lower()

        if mode not in self.MODES:
            self.logger.error(f"Unknown mode: {mode}")
            self._print_usage()
            sys.exit(1)

        if mode == "update-db":
            updater = DatasheetUpdater()
            success = updater.run(args[1:])
            sys.exit(0 if success else 1)

        if not accept_eula:
            self._show_disclaimer()

        try:
            config = Config()
            config.validate()

            _, operation_class = self.MODES[mode]
            operation = operation_class(config)

            if mode in ("write", "clone", "verify"):
                if len(args) != 2:
                    raise RuntimeError(f"{mode} mode requires directory path")

                directory = Path(args[1]).resolve()
                operation.run(directory)
            elif mode == "id":
                operation.run()
            else:
                operation.run()

        except (RuntimeError, FileNotFoundError, NotADirectoryError, KeyboardInterrupt) as e:
            self.logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            self.logger.exception("Unexpected error occurred")
            sys.exit(1)


def main():
    app = CLIApplication()
    app.run(sys.argv[1:])


if __name__ == "__main__":
    main()
