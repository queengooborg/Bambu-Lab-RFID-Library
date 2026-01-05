#!/usr/bin/env python3
import argparse

try:
    from Crypto.Protocol.KDF import HKDF
    from Crypto.Hash import SHA256
except:
    print("Can't import Crypto; install pycryptodome, and try again")
    exit()

SALT = bytes([0x9a,0x75,0x9c,0xf2,0xc4,0xf7,0xca,0xff,0x22,0x2c,0xb9,0x76,0x9b,0x41,0xbc,0x96])

def generate_keys(uid):
    keys_a=HKDF(uid, 6, SALT, SHA256, 16, context=b"RFID-A\0")
    keys_b=HKDF(uid, 6, SALT, SHA256, 16, context=b"RFID-B\0")

    return {'A':keys_a,'B':keys_b}

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate keys from a binary tag dump using the UID")
    parser.add_argument('file', help='Binary tag dump to generate keys from')
    parser.add_argument('-o', '--output', action='store_true', help='Save keys to hf-mf-<TAG UID>-key.bin')
    args = parser.parse_args()

    with open(args.file, 'rb') as fp:
        uid=fp.read(6)
    keys = generate_keys(uid)
    if args.output:
        with open(f'hf-mf-{uid.hex().upper()}-keys.bin', 'wb') as fp:
            fp.write(b''.join(keys['A']))
            fp.write(b''.join(keys['B']))
    else:
        print('\n'.join([x.hex().upper() for x in keys['A']]))
        print('\n'.join([x.hex().upper() for x in keys['B']]))
