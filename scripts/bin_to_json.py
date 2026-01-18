#!/usr/bin/env python3

import argparse
import json

from collections import OrderedDict
from pathlib import Path

BYTES_PER_BLOCK = 16

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


def decode_access_bits(sector, hexstr):
    ret = {}

    b8 = int(hexstr[0:2], 16)
    b7 = int(hexstr[2:4], 16)
    b6 = int(hexstr[4:6], 16)
    ud = hexstr[6:8]

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
            ret[f'block{sector*4+i}']=TRAILER_ACCESS[codes[i]]
        else:
            ret[f'block{sector*4+i}']=DATA_ACCESS[codes[i]]
    ret['UserData']=ud
    return ret

def load_data(filename):
    filepath = Path(filename)
    with open(filepath, "rb") as f:
        data = f.read()
    if len(data) != 1024: 
        print(f"{filepath} is the wrong length {len(data)} != 1024 bytes")
        data = bytes()

    return data


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate a proxmark JSON file from a binary dump")
    parser.add_argument('file', help='Binary tag dump to parse to JSON')
    parser.add_argument('-o', '--output', action='store_true', help='Save JSON to hf-mf-<TAG UID>.json')
    args = parser.parse_args()

    data = load_data(args.file)

    if data:
        tag_dict = OrderedDict({'Created':'proxmark3',
                               'FileType':'mfc v2',
                               'Card':{'UID':'',
                                       'ATQA':'',
                                       'SAK':''},
                                'blocks':{}, 
                                'SectorKeys':{}})
        sector = 0
        blocks = list(data[0+i:BYTES_PER_BLOCK+i] for i in range(0, len(data), BYTES_PER_BLOCK))
        for i, line in enumerate(blocks):
            if sector == 0 and i == 0:
                tag_dict['Card']['UID']=line[0:4].hex().upper()
                tag_dict['Card']['ATQA']=line[6:8].hex().upper()
                tag_dict['Card']['SAK']=line[5].to_bytes(1,'big').hex().upper()
        
            tag_dict['blocks'][i]=line.hex().upper()
            if i % 4 == 3:
                access_bits=line[6:10].hex().upper()
                tag_dict['SectorKeys'][sector]={
                    'KeyA':line[0:6].hex().upper(),
                    'KeyB':line[10:].hex().upper(),
                    'AccessConditions':access_bits
                }
                tag_dict['SectorKeys'][sector]['AccessConditionsText']=decode_access_bits(sector, access_bits)
                sector+=1
        
        if args.output:
            with open(f"hf-mf-{tag_dict['Card']['UID']}.json",'w') as fp:
                json.dump(tag_dict, fp, indent='\t')
        else:
            print(json.dumps(tag_dict, indent='\t'))