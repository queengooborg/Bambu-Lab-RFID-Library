# -*- coding: utf-8 -*-

# Python script to repair any Bambu Lab RFID tag dumps without keys
# Created for https://github.com/queengooborg/Bambu-Lab-RFID-Library
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026
# Requires: pycryptodome

import sys
from pathlib import Path

from deriveKeys import kdf
from parse import BYTES_PER_BLOCK, BLOCKS_PER_SECTOR, TOTAL_SECTORS, TOTAL_BYTES

if not sys.version_info >= (3, 6):
  raise Exception("Python 3.6 or higher is required!")

INVALID_KEYS = [b"\xFF" * 6, b"\x00" * 6]

def sector_trailer_offset(sector):
    block_index = sector * BLOCKS_PER_SECTOR + 3
    return block_index * BYTES_PER_BLOCK

def extract_uid(dump):
    return dump[0:4]

def is_invalid_key(key):
    return bytes(key) in INVALID_KEYS

def repair_keys_in_place(path):
    dump_bytes = path.read_bytes()

    if len(dump_bytes) not in TOTAL_BYTES:
        raise ValueError(f"{path} is not a 1K MIFARE Classic dump")

    dump = bytearray(dump_bytes)
    uid = extract_uid(dump)
    print(f"\nFile : {path}")
    print(f"UID  : {uid.hex()}")

    keys_a, keys_b = kdf(uid)
    if len(keys_a) != 16 or len(keys_b) != 16:
        raise ValueError("KDF did not return 16 keys for each of A and B")

    changes = 0

    for sector in range(TOTAL_SECTORS):
        trailer = sector_trailer_offset(sector)

        key_a = dump[trailer : trailer + 6]
        key_b = dump[trailer + 10 : trailer + 16]

        derived_a = keys_a[sector]
        derived_b = keys_b[sector]

        if is_invalid_key(key_a):
            dump[trailer : trailer + 6] = derived_a
            changes += 1
            print(f"  Sector {sector:02d} Key A repaired → {derived_a.hex()}")

        if is_invalid_key(key_b):
            dump[trailer + 10 : trailer + 16] = derived_b
            changes += 1
            print(f"  Sector {sector:02d} Key B repaired → {derived_b.hex()}")

    if changes:
        path.write_bytes(dump)
        print(f"\n{changes} key(s) repaired — file updated in place.")
    else:
        print("\nNo repairs needed — file left unchanged.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: repair.py <dumpfile>")
        sys.exit(1)

    repair_keys_in_place(Path(sys.argv[1]))
