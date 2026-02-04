#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python script to convert Bambu Lab RFID tag data between formats (Proxmark, Flipper Zero)
# Created for https://github.com/queengooborg/Bambu-Lab-RFID-Library
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List

from parse import Tag, bytes_to_hex, BLOCKS_PER_SECTOR, TOTAL_SECTORS

DUMP_SUFFIX = "-dump.bin"
KEY_SUFFIX = "-key.bin"
JSON_SUFFIX = "-dump.json"
NFC_SUFFIX = ".nfc"
PARSED_SUFFIX = "-parsed.txt"

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

    b8 = int(hexstr[0:2], 16)
    b7 = int(hexstr[2:4], 16)
    b6 = int(hexstr[4:6], 16)
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
    return all(x == y for x, y in zip(a, b))


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

    i = 0
    for block in tag.blocks:
        output['blocks'][str(i)] = bytes_to_hex(block)
        i += 1

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
    # Flipper has the ATQA bytes reveresed
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

def write_parsed(path, tag):
    with open(path, "w") as f:
        f.write(str(tag)+'\n')

# Check directory and write any missing files

def sync_directory(path, create_files=True, create_parsed=False):
    # If we're given a specific file, get the parent instead
    if path.is_file():
        path = path.parent

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
        elif name.endswith(PARSED_SUFFIX):
            base = name[:-len(PARSED_SUFFIX)]
            groups.setdefault(base, {})["parsed"] = file
        else:
            if file.name not in [".DS_Store", "_attribution.txt"]:
                unhandled_files.append(file.name)

    for base, entries in groups.items():
        print(f"\n== {path}/{base} ==")

        tags = []
        for kind, file in entries.items():
            if kind in ["key", "parsed"]:
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

        if unhandled_files:
            print(f'  [!] UNKNOWN FILES in folder: {", ".join(unhandled_files)}')

        if not tags:
            continue

        # consistency check
        ref_kind, ref_tag = tags[0]
        for kind, tag in tags[1:]:
            if not blocks_equal(ref_tag.blocks, tag.blocks):
                print(f"  [!] MISMATCH between {ref_kind} and {kind}")
                print(f"      Consider deleting malformed {kind} file")
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
        if create_files:
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

            if create_parsed and "parsed" not in entries:
                out = path / f"{base}{PARSED_SUFFIX}"
                write_parsed(out, tag)
                print(f"  [+] Created {out.name}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Convert a tag from binary to JSON/Flipper/nfc/keys/parsed text')
    parser.add_argument('directory', nargs='+', help='Directory(ies) containing tag data')
    parser.add_argument('-n', '--no-create', action='store_false', dest='create_files',
                        help='Do not create missing files')
    parser.add_argument('-p', '--create-parsed', action='store_true', dest='create_parsed',
                        help='Create parsed text files')
    args = parser.parse_args()

    for dir_path in args.directory:
        sync_directory(Path(dir_path), args.create_files, args.create_parsed)
