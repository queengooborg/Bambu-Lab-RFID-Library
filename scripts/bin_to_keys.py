#!/usr/bin/env python3
import argparse

from parse import generate_keys, TOTAL_BYTES

def generate_key_dicts(uid):
    keys=generate_keys(uid)

    return {'A':keys[0:16],'B':keys[16:]}

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate keys from a binary tag dump using the UID")
    parser.add_argument('file', help='Binary tag dump to generate keys from')
    parser.add_argument('-o', '--output', action='store_true', help='Save keys to hf-mf-<TAG UID>-key.bin')
    args = parser.parse_args()

    with open(args.file, 'rb') as fp:
        uid = fp.read(4)
        dump_bytes = fp.read()

    if len(uid) + len(dump_bytes) != TOTAL_BYTES:
        raise ValueError(f'Dump file {args.file} does not contain {TOTAL_BYTES} bytes!')

    keys = generate_key_dicts(uid)
    if args.output:
        with open(f'hf-mf-{uid.hex().upper()}-key.bin', 'wb') as fp:
            fp.write(b''.join(keys['A']))
            fp.write(b''.join(keys['B']))
    else:
        print('\n'.join([x.hex().upper() for x in keys['A']]))
        print('\n'.join([x.hex().upper() for x in keys['B']]))
