# -*- coding: utf-8 -*-

# Python script to convert Bambu Lab RFID tag data between formats (Proxmark, Flipper Zero)
# Created for https://github.com/queengooborg/Bambu-Lab-RFID-Library
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026

import sys
import os
import json
import struct
from pathlib import Path
from typing import Dict, List

from parse import Tag, bytes_to_hex, BLOCKS_PER_SECTOR, TOTAL_SECTORS

DUMP_SUFFIX = "-dump.bin"
KEY_SUFFIX = "-key.bin"
JSON_SUFFIX = "-dump.json"
NFC_SUFFIX = ".nfc"

# Helper functions

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
        "Created": "proxmark3",
        "FileType": "mfc v2",
        "Card": {
            "UID": tag.data['uid'],
            "ATQA": "0400",
            "SAK": "08"
        },
        "blocks": {},
        "SectorKeys": {}
    }

    i = 0
    for block in tag.blocks:
        output['blocks'][str(i)] = bytes_to_hex(block)
        i += 1

    for sector in range(TOTAL_SECTORS):
        output['SectorKeys'][str(sector)] = {
            "KeyA": bytes_to_hex(keys[sector]),
            "KeyB": bytes_to_hex(keys[sector+TOTAL_SECTORS]),
            "AccessConditions": "87878769",
            "AccessConditionsText": {
                f"block{sector*4}": "read AB",
                f"block{sector*4+1}": "read AB",
                f"block{sector*4+2}": "read AB",
                f"block{sector*4+3}": "read ACCESS by AB; write ACCESS by B",
                "UserData": "69"
            }
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
    lines.append("ATQA: 00 04")
    lines.append("SAK: 08")
    lines.append("# Mifare Classic specific data")
    lines.append("Mifare Classic type: 1K")
    lines.append("Data format version: 2")
    lines.append("# Mifare Classic blocks, '??' means unknown data")

    for i, block in enumerate(tag.blocks):
        lines.append(f"Block {i}: {bytes_to_hex(block, True)}")

    with open(path, "w") as f:
        f.write("\n".join(lines))


# Check directory and write any missing files

def sync_directory(path):
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
                    tags.append((kind, tag))
            except Exception as e:
                print(f"  [!] Failed to parse {file.name}: {e}")

        if not tags:
            continue

        # consistency check
        ref_kind, ref_tag = tags[0]
        for kind, tag in tags[1:]:
            if not blocks_equal(ref_tag.blocks, tag.blocks):
                print(f"  [!] MISMATCH between {ref_kind} and {kind}")
                print("      Consider deleting malformed files")
                continue

        tag = ref_tag
        keys = extract_keys_from_blocks(tag.blocks)

        # XXX Key files might be formatted differently than expected...
        # if "key" in entries:
        #     with open(entries['key'], "rb") as f:
        #         if not blocks_equal(b''.join(keys), f.read()):
        #             print(f"  [!] MISMATCH between keys and {ref_kind}")
        #             print("      Consider deleting malformed files")
        #             continue

        # generate missing files
        if "dump" not in entries:
            out = path / f"{base}{DUMP_SUFFIX}"
            write_dump_bin(out, tag.blocks)
            print(f"  [+] Created {out.name}")

        # XXX Key files might be formatted differently than expected...
        # if "key" not in entries:
        #     out = path / f"{base}{KEY_SUFFIX}"
        #     write_key_bin(out, keys)
        #     print(f"  [+] Created {out.name}")

        if "json" not in entries:
            out = path / f"{base}{JSON_SUFFIX}"
            write_dump_json(out, tag)
            print(f"  [+] Created {out.name}")

        if "nfc" not in entries:
            out = path / f"{base}{NFC_SUFFIX}"
            write_flipper_nfc(out, tag)
            print(f"  [+] Created {out.name}")

        if unhandled_files:
            print(f"  [!] UNKNOWN FILES in folder: {", ".join(unhandled_files)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sync_tags.py <folder>")
        sys.exit(1)

    sync_directory(Path(sys.argv[1]))
