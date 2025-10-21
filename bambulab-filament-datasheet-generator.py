#!/usr/bin/env python3

"""
Bambu Lab Filament Data Processor

Processes local Bambu Studio filament color data and generates tables.
Can be used as a standalone script or imported as a library.
"""

import os
import sys
import json
import logging
import platform
import re
from pathlib import Path
from typing import Dict, List, Optional
from prettytable import PrettyTable, TableStyle


class LoggerMixin:

    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


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

            self.logger.info(f"Loaded {len(self.color_data)} filament entries from: {color_file}")

        except Exception as e:
            self.logger.error(f"Failed to load color data: {e}")
            raise

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
        output += "- ⚠️: Folder exists with files but ALL UIDs missing proper PM3 tag structure\n"
        output += "- 👀: Folder has at least one compliant UID but also has non-compliant UIDs\n\n"

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


class CLIApplication(LoggerMixin):
    """Command-line interface for the filament data processor."""

    def __init__(self):
        self._setup_logging()

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
        print("Usage: python3 bambu_filament_data.py [options]")
        print("\nOptions:")
        print("  --json <path>       Use custom JSON file path")
        print("  --scan <path>       Base directory to scan for tag dumps (default: current directory)")
        print("  --datasheet <path>  Datasheet file to update (default: ./bambulab_filament_datasheet.md)")
        print("  --output <path>     Write output to file instead of updating datasheet")
        print("  --dry-run           Show what would be written without actually writing")
        print("  --verbose, -v       Enable verbose debug logging")
        print("\nExamples:")
        print("  python3 bambu_filament_data.py")
        print('  python3 bambu_filament_data.py --json "/path/to/filaments_color_codes.json"')
        print('  python3 bambu_filament_data.py --scan "./tags" --datasheet "./bambulab_filament_datasheet.md"')
        print('  python3 bambu_filament_data.py --output "./filament_data.md" --verbose --dry-run')
        print("\nJSON File Locations (searched in order):")
        print("  1. Custom path via --json")
        print("  2. Platform-specific BambuStudio location")
        print("  3. Fallback: ./filaments_color_codes.json (with warning)")
        print("\nEnvironment Variables:")
        print("  DEBUG/VERBOSE       Enable debug logging --verbose")
        print("\nJSON File Locations (searched in order):")
        print("  1. Custom path via --json")
        print("  2. Platform-specific BambuStudio location")
        print("  3. Fallback: ./filaments_color_codes.json (with warning)")
        print("\nEnvironment Variables:")
        print("  DEBUG/VERBOSE       Enable debug logging")

    def run(self, args: List[str]):
        verbose = "--verbose" in args or "-v" in args
        dry_run = "--dry-run" in args
        args = [arg for arg in args if arg not in ("--verbose", "-v", "--dry-run")]

        if verbose:
            os.environ["VERBOSE"] = "1"
            logging.getLogger().setLevel(logging.DEBUG)

        custom_json_path = None
        scan_path = Path.cwd()
        datasheet_path = Path("./bambulab_filament_datasheet.md")
        output_path = None

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
            elif args[i] in ("--help", "-h"):
                self._print_usage()
                sys.exit(0)
            else:
                self.logger.error(f"Unknown argument: {args[i]}")
                self._print_usage()
                sys.exit(1)

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

        except (RuntimeError, FileNotFoundError, KeyboardInterrupt) as e:
            self.logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            self.logger.exception("Unexpected error occurred")
            sys.exit(1)


def main():
    """Entry point for CLI usage."""
    app = CLIApplication()
    app.run(sys.argv[1:])


if __name__ == "__main__":
    main()
