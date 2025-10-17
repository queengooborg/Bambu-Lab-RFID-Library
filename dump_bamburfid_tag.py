#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    import webcolors
except ImportError:
    print("ERROR: webcolors module not found (pip install webcolors)", file=sys.stderr)
    sys.exit(1)

BYTES_PER_BLOCK = 16

@dataclass
class Config:
    pm3_path: Path = Path(os.environ.get("PM3_PATH", "/opt/proxmark3/pm3"))
    dump_base_dir: Path = Path(os.environ.get("DUMP_BASE_DIR", "./"))
    
    def validate(self):
        if not self.pm3_path.is_file() or not os.access(self.pm3_path, os.X_OK):
            raise RuntimeError(f"proxmark3 not found or not executable: {self.pm3_path}")

@dataclass
class TagInfo:
    uid: str
    filament_type: str
    detailed_filament_type: str
    color_hex: str
    
    @property
    def color_name(self) -> str:
        return ColorConverter.hex_to_name(self.color_hex)
    
    @property
    def detailed_type(self) -> str:
        return self.detailed_filament_type or self.filament_type
    
    def get_path(self, base_dir: Path) -> Path:
        return base_dir / self.filament_type / self.detailed_type / self.color_name / self.uid

class ColorConverter:
    @staticmethod
    def hex_to_name(hex_color: str) -> str:
        hex_color = hex_color[:6] if len(hex_color) == 8 else hex_color
        
        try:
            return webcolors.hex_to_name(f'#{hex_color}').capitalize()
        except ValueError:
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            closest = min(
                webcolors.CSS3_HEX_TO_NAMES.items(),
                key=lambda item: sum((a - b) ** 2 for a, b in zip(rgb, webcolors.hex_to_rgb(item[0])))
            )
            return closest[1].capitalize()

class TagParser:
    @staticmethod
    def bytes_to_string(data: bytes) -> str:
        return data.decode('ascii').replace('\x00', ' ').strip()
    
    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        return data.hex().upper()
    
    @classmethod
    def parse(cls, data: bytes) -> TagInfo:
        blocks = [data[i:i+BYTES_PER_BLOCK] for i in range(0, len(data), BYTES_PER_BLOCK)]
        
        return TagInfo(
            uid=cls.bytes_to_hex(blocks[0][0:4]),
            filament_type=cls.bytes_to_string(blocks[2]),
            detailed_filament_type=cls.bytes_to_string(blocks[4]),
            color_hex=cls.bytes_to_hex(blocks[5][0:4])
        )

class Proxmark3:
    def __init__(self, config: Config):
        self.config = config
    
    def _run(self, cmd: str, capture: bool = False) -> subprocess.CompletedProcess:
        full_cmd = [str(self.config.pm3_path), "-c", cmd]
        print(f"+ {' '.join(full_cmd)}", file=sys.stderr)
        
        return subprocess.run(
            full_cmd,
            capture_output=True,
            text=True
        ) if capture else subprocess.run(full_cmd, stderr=subprocess.STDOUT)
    
    def check_tag(self) -> bool:
        result = self._run("hf mf info", capture=True)
        print(result.stdout + result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            raise RuntimeError("failed to read tag - check tag position")
        
        print("\n[OK] Tag detected\n", file=sys.stderr)
        return True
    
    def read_keys(self, tmp_dir: Path) -> str:
        result = self._run("hf mf bambukeys -r -d", capture=True)
        output = result.stdout + result.stderr
        print(output, file=sys.stderr)
        
        if result.returncode != 0:
            raise RuntimeError("failed to read tag")
        
        key_file_path = next(
            (line[line.find('`')+1:line.rfind('`')] 
             for line in output.split('\n') 
             if 'Saved' in line and 'binary file' in line and '`' in line),
            None
        )
        
        if not key_file_path:
            raise RuntimeError("no key file in output")
        
        key_file = Path(key_file_path)
        if not key_file.exists():
            raise RuntimeError(f"key file not found: {key_file}")
        
        dest = tmp_dir / key_file.name
        shutil.move(str(key_file), str(dest))
        return key_file.name
    
    def dump_tag(self, key_file: str, tmp_dir: Path) -> str:
        uid = key_file[key_file.find('hf-mf-')+6:key_file.find('-key')]
        if not uid:
            raise RuntimeError(f"cannot extract UID from key file: {key_file}")
        
        dump_file = f"hf-mf-{uid}-dump.bin"
        key_path = (tmp_dir / key_file).resolve()
        dump_path = (tmp_dir / dump_file).resolve()
        
        result = self._run(f"hf mf dump -k {key_path} -f {dump_path}")
        
        if result.returncode != 0 or not dump_path.exists():
            raise RuntimeError("dump failed")
        
        return dump_file

class RFIDDumper:
    def __init__(self, config: Config):
        self.config = config
        self.pm3 = Proxmark3(config)
    
    def _confirm_write(self, tag_info: TagInfo, target_dir: Path) -> bool:
        print(f"\nParsed tag info:", file=sys.stderr)
        print(f"  UID: {tag_info.uid}", file=sys.stderr)
        print(f"  Type: {tag_info.filament_type} / {tag_info.detailed_type}", file=sys.stderr)
        print(f"  Color: {tag_info.color_name} (#{tag_info.color_hex})", file=sys.stderr)
        print(f"\nTarget directory: {target_dir}", file=sys.stderr)
        
        response = input("Write files to this location? [Y/n]: ")
        return response.lower() not in ('n', 'no')
    
    def _organize_files(self, dump_file: str, tmp_dir: Path) -> Path:
        with open(tmp_dir / dump_file, 'rb') as f:
            tag_info = TagParser.parse(f.read())
        
        target_dir = tag_info.get_path(self.config.dump_base_dir)
        
        if not self._confirm_write(tag_info, target_dir):
            raise RuntimeError("aborted by user")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for item in tmp_dir.iterdir():
            shutil.move(str(item), str(target_dir / item.name))
        
        return target_dir
    
    def run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_dir = Path(tmpdir)
            
            input("Place tag on antenna, press Enter...")
            
            self.pm3.check_tag()
            key_file = self.pm3.read_keys(tmp_dir)
            dump_file = self.pm3.dump_tag(key_file, tmp_dir)
            target_dir = self._organize_files(dump_file, tmp_dir)
            
            print(f"\nSaved to: {target_dir}")
            for item in sorted(target_dir.iterdir()):
                print(f"  {item.name} ({item.stat().st_size} bytes)")

def main():
    try:
        config = Config()
        config.validate()
        
        dumper = RFIDDumper(config)
        dumper.run()
    except (RuntimeError, KeyboardInterrupt) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()