# -*- coding: utf-8 -*-

# Python script to extract the keys from a Bambu Lab filament RFID tag, using a Proxmark3
# Created for https://github.com/Bambu-Research-Group/RFID-Tag-Guide
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2025

import subprocess
import os
import re
import sys
import json
import shutil
import tempfile
from pathlib import Path

from lib import get_proxmark3_location, run_command

#Global variables
pm3Location = None                            #Calculated. The location of Proxmark3
pm3Command = "bin/pm3"                      # The command that works to start proxmark3

def setup():
    global pm3Location

    pm3Location = get_proxmark3_location()
    if not pm3Location:
        exit(-1)

def parse_dump_summary(dump_path):
    """Extract display fields from a .bin or .json dump file. Returns dict or None."""
    BLOCK = 16
    try:
        with open(dump_path, 'rb') as f:
            data = f.read()
        try:
            j = json.loads(data)
            if j.get("Created") in ["proxmark3", "bambuman", "queengooborg/Bambu-Lab-RFID-Library/convert.py"]:
                data = b"".join(bytes.fromhex(j["blocks"][k].replace("??", "00")) for k in j["blocks"])
        except (ValueError, KeyError, TypeError):
            pass
        if len(data) < 64 * BLOCK:
            return None
        blk = [data[i:i+BLOCK] for i in range(0, 64*BLOCK, BLOCK)]
        def s(b): return b.decode('ascii', errors='replace').replace('\x00', ' ').strip()
        return {
            'uid':          blk[0][0:4].hex().upper(),
            'filament_type': s(blk[2]),
            'material_name': s(blk[4]),
            'variant_id':   s(blk[1][0:8]),
            'color':        '#' + blk[5][0:4].hex().upper(),
        }
    except Exception:
        return None

def resolve_dump_and_key(path):
    """
    Given a path, return (tagdump, keydump) by auto-discovery where possible.

    Accepted forms:
      - A UID directory  (contains exactly one *-dump.bin and one *-key.bin)
      - A *-dump.bin file (key is inferred from the same directory)
      - Any other file   (keydump returned as None — caller must supply it)

    Raises ValueError if a directory is given but the files cannot be found
    unambiguously.
    """
    p = Path(path)

    if p.is_dir():
        dumps = sorted(p.glob('*-dump.bin'))
        keys  = sorted(p.glob('*-key.bin'))
        if not dumps:
            raise ValueError(f"No *-dump.bin file found in: {p}")
        if len(dumps) > 1:
            raise ValueError(f"Multiple dump files found in {p} — specify one explicitly")
        if not keys:
            raise ValueError(f"No *-key.bin file found in: {p}")
        return str(dumps[0]), str(keys[0])

    if p.name.endswith('-dump.bin'):
        key = p.parent / p.name.replace('-dump.bin', '-key.bin')
        return str(p), str(key)

    # Plain file path — caller must supply the key separately
    return str(p), None


def main():
    print("--------------------------------------------------------")
    print("RFID Tag Writer v0.1.0 - Bambu Research Group 2025")
    print("--------------------------------------------------------")
    print("This will write a tag dump to a physical tag using your")
    print("Proxmark3 device, allowing RFID tags for non-Bambu spools.")
    print("--------------------------------------------------------")

    # Run setup
    setup()

    # --- Resolve tag dump and key file ---
    # Accept: a UID directory, a *-dump.bin file, or two explicit file paths.
    # Either relative or absolute paths are fine.

    raw1 = (os.path.abspath(sys.argv[1]) if len(sys.argv) > 1
            else input("Enter the path to the tag dump or UID directory: ").replace("\\ ", " ").strip())

    try:
        tagdump, keydump = resolve_dump_and_key(raw1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

    if keydump is None:
        # Auto-discovery didn't find a key — need a second path
        keydump = (os.path.abspath(sys.argv[2]) if len(sys.argv) > 2
                   else input("Enter the path to the key file: ").replace("\\ ", " ").strip())
    elif len(sys.argv) > 2:
        # Directory/dump-file auto-discovery succeeded but a second arg was also given — warn
        print(f"Note: key file auto-detected as {keydump!r}; ignoring extra argument.")

    for label, path in [("Tag dump", tagdump), ("Key file", keydump)]:
        if not os.path.isfile(path):
            print(f"Error: {label} not found: {path}")
            exit(1)

    print()
    summary = parse_dump_summary(tagdump)
    if summary:
        # Derive color name from folder structure: .../<Color>/<UID>/file.bin
        dump_parts = Path(tagdump).parts
        color_name = dump_parts[-3] if len(dump_parts) >= 3 else None
        color_display = f"{color_name} ({summary['color']})" if color_name else summary['color']

        print("Filament data that will be written to the tag:")
        print(f"  Material:   {summary['material_name']} ({summary['filament_type']})")
        print(f"  Color:      {color_display}")
        print(f"  Variant ID: {summary['variant_id']}")
        print(f"  Tag UID:    {summary['uid']}")
        print()
        confirm = input("Is this the correct filament? (y/N) ")
        if confirm.lower() not in ["y", "yes"]:
            print("Cancelled.")
            exit(0)
        print()

    print("Place your Proxmark3 onto the blank tag you wish to write,")
    print("then press Enter.")

    input()

    try:
        tagtype = getTagType()
    except RuntimeError as e:
        print(f"\nError: {e}")
        exit(1)

    print()
    print("=========== WARNING! == WARNING! == WARNING! ===========")
    print("This script will write the contents of a dump to your")
    print("RFID tag, and then PERMANENTLY WRITE LOCK the tag.")
    print("")
    print("This process is IRREVERSIBLE, proceed at your own risk.")
    print("========================================================")
    print()

    confirm = input("Are you SURE you wish to continue (y/N)? ")
    if confirm.lower() not in ["y", "yes"]:
        print("Confirmation not obtained, exiting")
        exit(0)

    print("Writing tag data now...")
    writeTag(tagdump, keydump, tagtype)

    print()
    print("Writing complete! Your tag should now register on the AMS.")
    print()


def getTagType():
    print(f"Checking tag type...")
    output = run_command([pm3Location / pm3Command, "-d", "1", "-c", f"hf mf info"])

    if output is None:
        raise RuntimeError("No output from Proxmark3 — check device connection")

    if 'iso14443a card select failed' in output:
        raise RuntimeError("Tag not found or is wrong type")

    cap_re = r"(?:\[\+\] Magic capabilities\.\.\. ([()/\w\d ]+)\n)"

    # Allow optional blank line between the section header and capability lines
    match = re.search(rf"\[=\] --- Magic Tag Information\n\n?(\[=\] <n/a>\n|{cap_re}+)", output)
    if not match:
        raise RuntimeError("Could not obtain magic tag information")

    if "[=] <n/a>" in match.group(1):
        raise RuntimeError("Tag is not writable — it may already be locked, or is not a supported type (Gen 2 FUID, Gen 4 FUID, Gen 4 UFUID)")

    capabilities = re.findall(cap_re, match.group(1))

    if "Gen 4 GDM / USCUID ( Gen4 Magic Wakeup )" in capabilities:
        return "Gen 4 FUID"
    if "Gen 4 GDM / USCUID ( ZUID Gen1 Magic Wakeup )" in capabilities:
        return "Gen 4 UFUID"
    if "Write Once / FUID" in capabilities:
        return "Gen 2 FUID"

    raise RuntimeError(f"Tag is not a compatible type. Detected capabilities: {capabilities}")

def writeTag(tagdump, keydump, tagtype):
    # Copy files to a temp dir with no spaces so paths survive the Windows cmd->bash->pm3 chain
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dump = os.path.join(tmpdir, 'dump.bin').replace('\\', '/')
        tmp_key  = os.path.join(tmpdir, 'key.bin').replace('\\', '/')
        shutil.copy2(tagdump, tmp_dump)
        shutil.copy2(keydump, tmp_key)

        if tagtype in ("Gen 4 FUID", "Gen 2 FUID"):
            output = run_command([pm3Location / pm3Command, "-c", f"hf mf restore --force -f {tmp_dump} -k {tmp_key}"])
            if output:
                print(output)
            return

        if tagtype == "Gen 4 UFUID":
            output = run_command([pm3Location / pm3Command, "-c", f"hf mf cload -f {tmp_dump}; hf 14a raw -a -k -b 7 40; hf 14a raw -k 43; hf 14a raw -k -c e100; hf 14a raw -c 85000000000000000000000000000008"])
            if output:
                print(output)


if __name__ == "__main__":
    main() #Run main program
