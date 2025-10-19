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
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


class ColorDataLoader(LoggerMixin):
    """Loads and provides access to Bambu Studio filament color data."""
    
    COLOR_DATA_PATHS = {
        "Windows": Path(os.environ.get("APPDATA", "")) / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
        "Darwin": Path.home() / "Library" / "Application Support" / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
        "Linux": Path.home() / ".config" / "BambuStudio" / "system" / "BBL" / "filament" / "filaments_color_codes.json",
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
            with open(color_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.filament_data = data.get('data', [])
            
            for item in self.filament_data:
                code = item.get('fila_color_code')
                if code:
                    self.color_data[code] = {
                        'fila_color': item.get('fila_color', []),
                        'fila_type': item.get('fila_type', ''),
                        'fila_id': item.get('fila_id', ''),
                        'fila_color_name': item.get('fila_color_name', {}),
                    }
            
            self.logger.info(f"Loaded {len(self.color_data)} filament entries from: {color_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to load color data: {e}")
            raise
    
    def get_color_hex(self, filament_code: str) -> Optional[str]:
        """Get the hex color code for a filament code."""
        item = self.color_data.get(filament_code, {})
        colors = item.get('fila_color', [])
        return colors[0] if colors else None
    
    def get_filament_type(self, filament_code: str) -> Optional[str]:
        """Get the filament type for a filament code."""
        item = self.color_data.get(filament_code, {})
        return item.get('fila_type')
    
    def get_variant_id(self, filament_code: str) -> Optional[str]:
        """Get the variant ID for a filament code."""
        item = self.color_data.get(filament_code, {})
        return item.get('fila_id')
    
    def get_color_name(self, filament_code: str, language: str = 'en') -> Optional[str]:
        """Get the color name for a filament code in a specific language."""
        item = self.color_data.get(filament_code, {})
        names = item.get('fila_color_name', {})
        return names.get(language)
    
    def get_all_by_type(self) -> Dict[str, List[Dict]]:
        """Get all filament data grouped by filament type."""
        filament_types = {}
        for item in self.filament_data:
            fila_type = item.get('fila_type', 'Unknown')
            if fila_type not in filament_types:
                filament_types[fila_type] = []
            filament_types[fila_type].append(item)
        return filament_types


class ReadmeParser(LoggerMixin):
    """Parses existing README.md to extract status information."""
    
    def __init__(self):
        self.table_row_pattern = re.compile(
            r'^\|\s+(?P<color>.+?)\s+\|\s+(?P<filament_code>\d{5}|\?)\s+\|\s+(?P<fila_color>[^|]+)\s+\|\s+(?P<variant_id>[^|]+)\s+\|\s+(?P<status>✅|❌|⚠️|⏳)\s+\|',
            re.MULTILINE
        )
    
    def parse(self, readme_content: str) -> Dict[str, Dict[str, str]]:
        """Parse README and return mapping of filament_code -> row data."""
        return {
            match.group("filament_code"): match.groupdict() 
            for match in self.table_row_pattern.finditer(readme_content)
        }


class TableGenerator(LoggerMixin):
    """Generates markdown tables from filament data."""
    
    def __init__(self, color_loader: ColorDataLoader):
        self.color_loader = color_loader
        self.readme_parser = ReadmeParser()
    
    def generate_table_from_json(self, existing_data: Optional[Dict] = None) -> str:
        """Generate complete markdown output from JSON data."""
        output = "## List of Bambu Lab Materials + Colors\n"
        output += "\n"
        output += "### Notes: \n"
        output += "- Some entries do NOT have corresponding RFID tags provided by BambuLabs.\n"
        output += "\n"
        output += "### Status Icon Legend:\n"
        output += "- ✅: Have tag data\n"
        output += "- ❌: No tag scanned\n"
        output += "- ⚠️: See notes\n"
        output += "- ⏳: Tag data is for an older version of material\n"
        output += "\n"
        
        filament_types = self.color_loader.get_all_by_type()
        
        for fila_type in sorted(filament_types.keys()):
            output += f"### {fila_type}\n\n"
            
            table = PrettyTable()
            table.set_style(TableStyle.MARKDOWN)
            table.align = "l"
            table.field_names = ["Color", "Filament Code", "Color Hex", "Variant ID", "Status"]
            
            for item in sorted(filament_types[fila_type], key=lambda x: x.get('fila_color_code', '')):
                color_name = item.get('fila_color_name', {}).get('en', 'Unknown')
                filament_code = item.get('fila_color_code', '?')
                fila_color = item.get('fila_color', ['?'])[0]
                variant_id = item.get('fila_id', '?')
                
                status = "❌"
                if existing_data and filament_code in existing_data:
                    status = existing_data[filament_code].get('status', '❌')
                
                table.add_row([color_name, filament_code, fila_color, variant_id, status])
            
            output += table.get_string().replace(":-", "--").replace("-|", " |")
            output += "\n\n"
        
        return output
    
    def update_readme(self, readme_path: Path, dry_run: bool = False) -> str:
        """Update datasheet with new filament data, preserving existing status."""
        if not readme_path.exists():
            self.logger.warning(f"Datasheet not found: {readme_path}, creating new output")
            existing_data = {}
        else:
            readme_content = readme_path.read_text(encoding='utf-8')
            existing_data = self.readme_parser.parse(readme_content)
            self.logger.info(f"Parsed {len(existing_data)} existing entries from datasheet")
        
        output = self.generate_table_from_json(existing_data)
        
        if not dry_run:
            readme_path.write_text(output, encoding='utf-8')
            self.logger.info(f"Updated datasheet: {readme_path}")
        else:
            self.logger.info("Dry run mode - no files written")
        
        return output


class CLIApplication(LoggerMixin):
    """Command-line interface for the filament data processor."""
    
    def __init__(self):
        self._setup_logging()
    
    def _setup_logging(self):
        level = logging.DEBUG if os.environ.get('DEBUG') or os.environ.get('VERBOSE') else logging.INFO
        
        class CustomFormatter(logging.Formatter):
            
            FORMATS = {
                logging.DEBUG: '[d]',
                logging.INFO: '[i]',
                logging.WARNING: '[!]',
                logging.ERROR: '[x]',
                logging.CRITICAL: '[X]',
            }
            
            def format(self, record):
                status = self.FORMATS.get(record.levelno, '[?]')
                date_str = self.formatTime(record, '%Y-%b-%d')
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
        print("  --datasheet <path>  Datasheet file to update (default: ./BambuLab_Filament_DataSheet.md)")
        print("  --output <path>     Write output to file instead of updating datasheet")
        print("  --dry-run           Show what would be written without actually writing")
        print("  --verbose, -v       Enable verbose debug logging")
        print("\nExamples:")
        print("  python3 bambu_filament_data.py")
        print('  python3 bambu_filament_data.py --json "/path/to/filaments_color_codes.json"')
        print('  python3 bambu_filament_data.py --datasheet "./BambuLab_Filament_DataSheet.md" --dry-run')
        print('  python3 bambu_filament_data.py --output "./filament_data.md" --verbose')
        print("\nJSON File Locations (searched in order):")
        print("  1. Custom path via --json")
        print("  2. Platform-specific BambuStudio location")
        print("  3. Fallback: ./filaments_color_codes.json (with warning)")
        print("\nEnvironment Variables:")
        print("  DEBUG/VERBOSE       Enable debug logging")
    
    def run(self, args: List[str]):
        verbose = '--verbose' in args or '-v' in args
        dry_run = '--dry-run' in args
        args = [arg for arg in args if arg not in ('--verbose', '-v', '--dry-run')]
        
        if verbose:
            os.environ['VERBOSE'] = '1'
            logging.getLogger().setLevel(logging.DEBUG)
        
        custom_json_path = None
        datasheet_path = Path("./BambuLab_Filament_DataSheet.md")
        output_path = None
        
        i = 0
        while i < len(args):
            if args[i] == '--json' and i + 1 < len(args):
                custom_json_path = Path(args[i + 1])
                i += 2
            elif args[i] == '--datasheet' and i + 1 < len(args):
                datasheet_path = Path(args[i + 1])
                i += 2
            elif args[i] == '--output' and i + 1 < len(args):
                output_path = Path(args[i + 1])
                i += 2
            elif args[i] in ('--help', '-h'):
                self._print_usage()
                sys.exit(0)
            else:
                self.logger.error(f"Unknown argument: {args[i]}")
                self._print_usage()
                sys.exit(1)
        
        try:
            self.logger.info("Loading filament color data...")
            color_loader = ColorDataLoader(custom_json_path)
            
            self.logger.info("Generating table...")
            generator = TableGenerator(color_loader)
            
            if output_path:
                output = generator.generate_table_from_json()
                if not dry_run:
                    output_path.write_text(output, encoding='utf-8')
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