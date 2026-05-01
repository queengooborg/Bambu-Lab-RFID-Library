# -*- coding: utf-8 -*-

# Python script to scrape Bambu Studio's filament data to update our readme
# Created for https://github.com/Bambu-Research-Group/RFID-Tag-Guide
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2026

import sys
import re
import urllib.parse
from pathlib import Path
from prettytable import PrettyTable, TableStyle

import requests

if not sys.version_info >= (3, 6):
  raise Exception("Python 3.6 or higher is required!")

JSON_URL = "https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/filaments_color_codes.json"

# Material categories (can't extract from Bambu Lab)
CATEGORIES = {
	"PLA": [
		"PLA Basic",
		"PLA Lite",
		"PLA Matte",
		"PLA Basic Gradient",
		"PLA Glow",
		"PLA Marble",
		"PLA Aero",
		"PLA Sparkle",
		"PLA Metal",
		"PLA Translucent",
		"PLA Silk+",
		"PLA Silk Multi-Color",
		"PLA Galaxy",
		"PLA Wood",
		"PLA-CF",
		"PLA Tough+",
		"PLA Tough"
	],
	"PETG": [
		"PETG Basic",
		"PETG HF",
		"PETG Translucent",
		"PETG-CF"
	],
	"ABS": [
		"ABS",
		"ABS-GF"
	],
	"ASA": [
		"ASA",
		"ASA Aero",
		"ASA-CF"
	],
	"PC": [
		"PC",
		"PC FR",
	],
	"TPU": [
		"TPU for AMS"
	],
	"PA": [
		"PAHT-CF",
		"PA6-GF",
	],
	"Support Material": [
		"Support for PLA/PETG",
		"Support for PLA (New Version)",
		"Support for ABS",
		"Support for PA/PET",
		"PVA"
	]
}

# These materials don't have RFIDs or are discontinued
IGNORED_MATERIALS = [
	"PLA Dynamic",
	"PLA Silk",
	"PA6-CF",
	"PPA-CF",
	"PET-CF",
	"PPS-CF",
	"TPU 85A",
	"TPU 90A",
	"TPU 95A",
	"TPU 95A HF",
	"Support for PLA"
]

# Some material store names cannot be used directly as folder names
# (slashes become path separators; hyphens vs spaces differ from the library).
# Maps store display name -> actual library folder name.
FOLDER_NAME_OVERRIDES = {
	'PETG-CF':              'PETG CF',
	'Support for PLA/PETG': 'Support for PLA-PETG',
	'Support for PA/PET':   'Support for PA-PET',
}

def get_category(material):
	for category, materials in CATEGORIES.items():
		if material in materials:
			return category

	raise Exception(f"Category for {material} is not specified!")

def get_materials():
	req = requests.get(JSON_URL)
	filament_data = req.json().get('data')

	if not filament_data:
		raise Exception("Could not obtain filament data")

	result = {}

	for category, materials in CATEGORIES.items():
		result[category] = {}

		for material in materials:
			result[category][material] = {}

	for fila in filament_data:
		material = fila['fila_type']
		color = fila['fila_color_name']['en']
		code = fila['fila_color_code']

		if fila['fila_color_type'] in ["渐变色", "多拼色"]:
			if material == "PLA Basic":	material = "PLA Basic Gradient"
			if material == "PLA Silk": material = "PLA Silk Multi-Color"

		if code == "65104":
			material = "Support for PLA (New Version)"

		if material in IGNORED_MATERIALS:
			continue

		category = get_category(material)

		result[category][material][color] = code

	return result

def get_existing_data(readme):
	table_row_pattern = re.compile(
		r'^\|\s+(?P<color>.+?)\s+\|\s+(?P<filament_code>\d{5}|\?)\s+\|\s+(?P<variant_id>[^|]+)\s+\|\s+(?P<status>✅|❌|⚠️|⏳)\s+\|',
		re.MULTILINE
	)
	return {match.group("filament_code"): match.groupdict() for match in table_row_pattern.finditer(readme)}

def make_md_link(text, url):
	return f"[{text}]({urllib.parse.quote(url)})"

def make_table(category, material, colors, existing_data):
	# Use the actual library folder name in links (may differ from store display name)
	folder = FOLDER_NAME_OVERRIDES.get(material, material)
	out = f"#### {make_md_link(material, f'./{category}/{folder}')}\n\n"

	table = PrettyTable()
	table.set_style(TableStyle.MARKDOWN)
	table.align = "l"
	table.field_names = ["Color", "Filament Code", "Variant ID", "Status"]

	for color, filament_code in colors.items():
		existing_color_data = existing_data.get(filament_code, {})
		status = existing_color_data.get("status", "❌")
		variant_id = existing_color_data.get("variant_id", '?')
		table.add_row([make_md_link(color, f'./{category}/{folder}/{color}'), filament_code, variant_id, status])

	out += table.get_string().replace(":-", "--").replace("-|", " |")
	out += "\n\n"

	return out

def generate_tables(materials, readme_path):
	readme_path = Path(readme_path)
	readme = readme_path.read_text(encoding='utf-8')

	existing_data = get_existing_data(readme)

	# Replace only the "List of Bambu Lab Materials + Colors" section, preserving the rest
	section_start = readme.find("## List of Bambu Lab Materials + Colors")
	if section_start == -1:
		print("Could not find materials section in README — printing to stdout instead")
		for category in materials:
			print(f"### {make_md_link(category, f'./{category}')}\n")
			for material in materials[category]:
				print(make_table(category, material, materials[category][material], existing_data))
		return

	# Find the next top-level heading after the section (## History or similar)
	next_section = readme.find("\n## ", section_start + 1)
	header_and_legend = readme[section_start:readme.find("\n### ", section_start)]

	new_tables = ""
	for category in materials:
		new_tables += f"### {make_md_link(category, f'./{category}')}\n\n"
		for material in materials[category]:
			new_tables += make_table(category, material, materials[category][material], existing_data)

	suffix = readme[next_section+1:] if next_section != -1 else ""
	updated = readme[:section_start] + header_and_legend + "\n" + new_tables + suffix
	readme_path.write_text(updated, encoding='utf-8')
	print(f"README updated: {readme_path}")

if __name__ == "__main__":
	materials = get_materials()
	generate_tables(materials, "./README.md")
