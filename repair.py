# -*- coding: utf-8 -*-

# Python script to repair any Bambu Lab RFID tag dumps without keys
# Created for https://github.com/queengooborg/Bambu-Lab-RFID-Library
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026
# Requires: pycryptodome

from pathlib import Path
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

from parse import BYTES_PER_BLOCK, BLOCKS_PER_SECTOR, TOTAL_SECTORS, TOTAL_BYTES

INVALID_KEYS = {
    b"\xFF" * 6,
    b"\x00" * 6,
}

def kdf(uid):
    salt = bytes([0x9a,0x75,0x9c,0xf2,0xc4,0xf7,0xca,0xff,0x22,0x2c,0xb9,0x76,0x9b,0x41,0xbc,0x96])
    return HKDF(uid, 6, salt, SHA256, 16, context=b"RFID-A\0") + HKDF(uid, 6, salt, SHA256, 16, context=b"RFID-B\0")

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

    keys = kdf(uid)
    if len(keys) != 32:
        raise ValueError("KDF did not return 32 keys")

    changes = 0

    for sector in range(TOTAL_SECTORS):
        trailer = sector_trailer_offset(sector)

        key_a = dump[trailer : trailer + 6]
        key_b = dump[trailer + 10 : trailer + 16]

        derived_a = keys[sector]
        derived_b = keys[16 + sector]

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

def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: repair_dump.py <dumpfile>")
        return

    repair_keys_in_place(Path(sys.argv[1]))

if __name__ == "__main__":
    main()