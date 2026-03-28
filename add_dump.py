# -*- coding: utf-8 -*-

# Python script to move a dump.bin file to the correct location in the library, assuming the variant already exists
# so we can identify the color

import argparse
import shutil
import sys

from pathlib import Path

from parse import Tag, bytes_to_hex, BLOCKS_PER_SECTOR, TOTAL_SECTORS

DUMP_SUFFIX = '-dump.bin'
SILENT = False
LIBRARY_ROOT = Path.cwd()


def sprint(*args, **kwargs):
   if not SILENT:
      print(*args, **kwargs)

def load_library():
  library = {}
  for file in LIBRARY_ROOT.rglob(f'*{DUMP_SUFFIX}'):
    if file.parent == LIBRARY_ROOT:
      # skip files that are in the root; they're probably the ones we're trying to add.
      continue
    try:
      with open(file, 'rb') as f:
        tag = Tag(file.name, f.read())
    except Exception as e:
      print(f'\t[!] Library load failed to parse {file.name}: {e}')
      sys.exit(2)

    # Assumes the color name is always the name of the dir 2 up from the binary file:
    # Color/UID/hf-mf-uid-dump.bin
    color = file.parts[-3]

    if (category := tag.data['filament_type']) not in library:
       library.update({category:{}})
    if (material := tag.data['detailed_filament_type']) not in library[category]:
       library[category].update({material:{}})
    if (id := tag.data['variant_id']) not in library[category][material]:
       library[category][material].update({id:color})

  return library


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Parse a binary dump file and add it to the correct place in the library')
  parser.add_argument('file', nargs='+', help='File(s) containing tag data')
  parser.add_argument('-s', '--silent', action='store_true', help='Do not print anything')
  parser.add_argument('-l', '--leave', action='store_true', help='Leave dump file in place; copy to library')
  parser.add_argument('-d', '--dryrun', action='store_true', help='Only print what would be done; overrides --silent')

  args = parser.parse_args()

  if args.dryrun:
     args.silent = False
     print('--dryrun implies not --silent')

  globals().update({'SILENT':args.silent})

  library = load_library()

  for filename in args.file:
    sprint(f'Opening {filename}')
    file = Path(filename)
    if not file.exists():
      print(f'\t[!] File {file.name} does not exist')
      continue
    try:
      with open(file, 'rb') as f:
        tag = Tag(file.name, f.read())
    except Exception as e:
      print(f'\t[!] Failed to parse {file.name}: {e}')
      continue

    category = tag.data['filament_type']
    material = tag.data['detailed_filament_type']
    id = tag.data['variant_id']

    sprint(f'\t{category} {material} {id}', end=' ')

    if category in library and material in library[category] and id in library[category][material]:
        color = library[category][material][id]
        sprint(f'{color}')
        bin_path = Path() / category / material / color / tag.data['uid'] / f'hf-mf-{tag.data["uid"]}{DUMP_SUFFIX}'
        sprint(f'\tPath is {bin_path}')
        if bin_path.exists():
           sprint(f'Binary dump file already exists')
           continue
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        if args.leave:
          action =  shutil.copy
        else:
          action = shutil.move
        if args.dryrun:
          sprint(f'\tWould {action.__name__} {filename} to {bin_path}')
        else:
          sprint(f'\t{action.__name__} {filename} to {bin_path}')
          action(file, bin_path)
    else:
       sprint(f' variant not found in library')
