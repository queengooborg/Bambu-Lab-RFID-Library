# -*- coding: utf-8 -*-

# Python script to convert Bambu Lab RFID tag data between formats (Proxmark, Flipper Zero)
# Created for https://github.com/queengooborg/Bambu-Lab-RFID-Library
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026

import sys
import argparse
import json
import os

from pathlib import Path

from parse import Tag, bytes_to_hex, BLOCKS_PER_SECTOR, TOTAL_SECTORS

if not sys.version_info >= (3, 6):
  raise Exception("Python 3.6 or higher is required!")

DUMP_SUFFIX = "-dump.bin"
KEY_SUFFIX = "-key.bin"
JSON_SUFFIX = "-dump.json"
NFC_SUFFIX = ".nfc"
DATA_ACCESS = {
        0x00: "read AB; write AB; increment AB; decrement transfer restore AB",
        0x01: "read AB; decrement transfer restore AB",
        0x02: "read AB",
        0x03: "read B; write B",
        0x04: "read AB; writeB",
        0x05: "read B",
        0x06: "read AB; write B; increment B; decrement transfer restore AB",
        0x07: "none"
}

TRAILER_ACCESS = {
        0x00: "read A by A; read ACCESS by A; read B by A; write B by A",
        0x01: "write A by A; read ACCESS by A write ACCESS by A; read B by A; write B by A",
        0x02: "read ACCESS by A; read B by A",
        0x03: "write A by B; read ACCESS by AB; write ACCESS by B; write B by B",
        0x04: "write A by B; read ACCESS by AB; write B by B",
        0x05: "read ACCESS by AB; write ACCESS by B",
        0x06: "read ACCESS by AB",
        0x07: "read ACCESS by AB"
}

# Helper functions

def decode_access_bits(sector, hexstr):
    ret = {}

    b6 = int(hexstr[0:2], 16)
    b7 = int(hexstr[2:4], 16)
    b8 = int(hexstr[4:6], 16)
    userdata = hexstr[6:8]

    C1 = []
    C2 = []
    C3 = []

    for i in range(4):
        C1_i = (b7 >> (4 + i)) & 0x1
        C2_i = (b8 >> i) & 0x1
        C3_i = (b8 >> (4 + i)) & 0x1

        C1.append(C1_i)
        C2.append(C2_i)
        C3.append(C3_i)

    codes = [(C1[i] << 2) | (C2[i] << 1) | C3[i] for i in range(4)]
    for i in range(4):
        if i % 4 == 3:
            ret[f'block{sector*4+i}'] = TRAILER_ACCESS[codes[i]]
        else:
            ret[f'block{sector*4+i}'] = DATA_ACCESS[codes[i]]
    ret['UserData'] = userdata
    return ret


def sector_trailer_block(sector):
    return sector * BLOCKS_PER_SECTOR + 3


def extract_keys_from_blocks(blocks):
    keysA = []
    keysB = []
    for sector in range(TOTAL_SECTORS):
        trailer = blocks[sector_trailer_block(sector)]
        keysA.append(trailer[0:6])
        keysB.append(trailer[10:16])
    return keysA + keysB


def blocks_equal(a, b):
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


# Format writers
def write_dump_bin(path, blocks):
    with open(path, "wb") as f:
        for block in blocks:
            f.write(block)


def write_key_bin(path, keys):
    with open(path, "wb") as f:
        for key in keys:
            f.write(key)


def write_dump_json(path, tag):
    keys = extract_keys_from_blocks(tag.blocks)

    output = {
        "Created": "queengooborg/Bambu-Lab-RFID-Library/convert.py",
        "FileType": "mfc v2",
        "Card": {
            "UID": tag.data['uid'],
            "ATQA": bytes_to_hex(tag.blocks[0][6:8]),
            "SAK": bytes_to_hex(tag.blocks[0][5].to_bytes(1, 'big'))
        },
        "blocks": {},
        "SectorKeys": {}
    }

    for i, block in enumerate(tag.blocks):
        output['blocks'][str(i)] = bytes_to_hex(block)

    for sector in range(TOTAL_SECTORS):
        access_bits = bytes_to_hex(tag.blocks[sector_trailer_block(sector)][6:10])
        output['SectorKeys'][str(sector)] = {
            "KeyA": bytes_to_hex(keys[sector]),
            "KeyB": bytes_to_hex(keys[sector+TOTAL_SECTORS]),
            "AccessConditions": access_bits,
            "AccessConditionsText": decode_access_bits(sector, access_bits)
        }

    with open(path, "w") as f:
        json.dump(output, f, indent=2)


def write_flipper_nfc(path, tag):
    keys = extract_keys_from_blocks(tag.blocks)

    lines = []
    lines.append("Filetype: Flipper NFC device")
    lines.append("Version: 4")
    lines.append("# Device type can be ISO14443-3A, ISO14443-3B, ISO14443-4A, ISO14443-4B, ISO15693-3, FeliCa, NTAG/Ultralight, Mifare Classic, Mifare Plus, Mifare DESFire, SLIX, ST25TB, EMV")
    lines.append("Device type: Mifare Classic")
    lines.append("# UID is common for all formats")
    lines.append(f"UID: {bytes_to_hex(tag.blocks[0][0:4], True)}")
    lines.append("# ISO14443-3A specific data")
    # Flipper has the ATQA bytes reversed
    lines.append(f"ATQA: {bytes_to_hex(int.from_bytes(tag.blocks[0][6:8], 'little').to_bytes(2,'big'), True)}")
    lines.append(f"SAK: {bytes_to_hex(tag.blocks[0][5].to_bytes(1,'big'))}")
    lines.append("# Mifare Classic specific data")
    lines.append("Mifare Classic type: 1K")
    lines.append("Data format version: 2")
    lines.append("# Mifare Classic blocks, '??' means unknown data")

    for i, block in enumerate(tag.blocks):
        lines.append(f"Block {i}: {bytes_to_hex(block, True)}")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# Check directory and write any missing files

def normalize_filenames(path):
    """
    Rename any *.bin dump files that don't use the standard -dump.bin suffix
    to the hf-mf-<UID>-dump.bin convention, and rename their matching key file
    too (if present).  Skips files that can't be parsed as a valid tag.
    Returns the number of files renamed.
    """
    renamed = 0
    for file in sorted(path.glob('*.bin')):
        if file.name.endswith(DUMP_SUFFIX) or file.name.endswith(KEY_SUFFIX):
            continue  # already a standard file

        try:
            with open(file, 'rb') as f:
                tag = Tag(file.name, f.read())
        except Exception:
            continue  # not a valid dump — leave it alone

        uid      = tag.data['uid']
        new_base = f'hf-mf-{uid}'
        new_dump = path / f'{new_base}{DUMP_SUFFIX}'
        new_key  = path / f'{new_base}{KEY_SUFFIX}'
        old_base = file.stem  # filename without the final .bin
        old_key  = path / f'{old_base}{KEY_SUFFIX}'

        if new_dump.exists():
            print(f'  [!] Cannot rename {file.name}: {new_dump.name} already exists')
            continue

        file.rename(new_dump)
        print(f'  [~] Renamed {file.name} -> {new_dump.name}')
        renamed += 1

        if old_key.exists() and not new_key.exists():
            old_key.rename(new_key)
            print(f'  [~] Renamed {old_key.name} -> {new_key.name}')

    return renamed


def sync_directory(path):
    # If we're given a specific file, get the parent instead
    if path.is_file():
        path = path.parent

    # Rename any non-standard *.bin dumps to hf-mf-<UID>-dump.bin before grouping
    normalize_filenames(path)

    files = list(path.iterdir())
    unhandled_files = []
    groups = {}

    # group by base name
    for file in files:
        name = file.name
        base = None

        if name.endswith(DUMP_SUFFIX):
            base = name[:-len(DUMP_SUFFIX)]
            groups.setdefault(base, {})["dump"] = file
        elif name.endswith(KEY_SUFFIX):
            base = name[:-len(KEY_SUFFIX)]
            groups.setdefault(base, {})["key"] = file
        elif name.endswith(JSON_SUFFIX):
            base = name[:-len(JSON_SUFFIX)]
            groups.setdefault(base, {})["json"] = file
        elif name.endswith(NFC_SUFFIX):
            base = name[:-len(NFC_SUFFIX)]
            groups.setdefault(base, {})["nfc"] = file
        else:
            if file.name not in [".DS_Store", "_attribution.txt"]:
                unhandled_files.append(file.name)

    for base, entries in groups.items():
        print(f"\n== {path}/{base} ==")

        tags = []
        for kind, file in entries.items():
            if kind == "key":
                continue

            try:
                with open(file, "rb") as f:
                    tag = Tag(file.name, f.read())
                    # Ensure dump is first so it's the reference tag for comparisons
                    if kind == "dump":
                        tags.insert(0, (kind, tag))
                    else:
                        tags.append((kind, tag))
            except Exception as e:
                print(f"  [!] Failed to parse {file.name}: {e}")

        if not tags:
            continue

        # consistency check — abort file generation for this group if any mismatch found
        ref_kind, ref_tag = tags[0]
        mismatch = False
        for kind, tag in tags[1:]:
            if not blocks_equal(ref_tag.blocks, tag.blocks):
                print(f"  [!] MISMATCH between {ref_kind} and {kind}")
                print(f"      Consider deleting malformed {kind} file")
                mismatch = True

        if mismatch:
            continue

        tag = ref_tag
        keys = extract_keys_from_blocks(tag.blocks)

        if "key" in entries:
            with open(entries['key'], "rb") as f:
                if not blocks_equal(b''.join(keys), f.read()):
                    print(f"  [!] MISMATCH between {ref_kind} and keys")
                    print("      Consider deleting malformed key file")
                    continue

        # generate missing files
        if "dump" not in entries:
            out = path / f"{base}{DUMP_SUFFIX}"
            write_dump_bin(out, tag.blocks)
            print(f"  [+] Created {out.name}")

        if "key" not in entries:
             out = path / f"{base}{KEY_SUFFIX}"
             write_key_bin(out, keys)
             print(f"  [+] Created {out.name}")

        if "json" not in entries:
            out = path / f"{base}{JSON_SUFFIX}"
            write_dump_json(out, tag)
            print(f"  [+] Created {out.name}")

        if "nfc" not in entries:
            out = path / f"{base}{NFC_SUFFIX}"
            write_flipper_nfc(out, tag)
            print(f"  [+] Created {out.name}")

    if unhandled_files:
        print(f"  [!] UNKNOWN FILES in folder: {', '.join(unhandled_files)}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Convert a tag from binary to JSON/Flipper/nfc/keys/parsed text')
    parser.add_argument('directory', nargs='+', help='Directory(ies) containing tag data')
    args = parser.parse_args()

    for dir_path in args.directory:
        for root, dirs, files in os.walk(dir_path):
            if files:
                sync_directory(Path(root))
