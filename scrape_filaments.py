# -*- coding: utf-8 -*-

# Python script to scrape Bambu Lab storepage to get all material types and colors
# Created for https://github.com/Bambu-Research-Group/RFID-Tag-Guide
# Written by Vinyl Da.i'gyu-Kazotetsu (www.queengoob.org), 2025

import sys
import time
import csv
import re
import traceback
import logging
import urllib.parse
from datetime import timedelta
from pathlib import Path
from prettytable import PrettyTable, TableStyle

import requests
import requests_cache
from bs4 import BeautifulSoup

if not sys.version_info >= (3, 6):
  raise Exception("Python 3.6 or higher is required!")

BASE_URL = "https://us.store.bambulab.com"
REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}
RETRIES = 3
RETRY_DELAY = 30

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

# Some material store names cannot be used directly as folder names
# (slashes become path separators; hyphens vs spaces differ from the library).
# Maps store display name -> actual library folder name.
FOLDER_NAME_OVERRIDES = {
    'PETG-CF':              'PETG CF',
    'Support for PLA/PETG': 'Support for PLA-PETG',
    'Support for PA/PET':   'Support for PA-PET',
}

# Some PLA Silk Multi-Color filaments don't publish filament codes
FILAMENT_CODE_OVERRIDES = {
    "Velvet Eclipse (Black-Red)": '13905',
    "Midnight Blaze (Blue-Red)": '13902',
    "Neon City (Blue-Magenta)": '13903',
    "Gilded Rose (Pink-Gold)": '13901',
    "Blue Hawaii (Blue-Green)": '13904',
}

# PLA Lite isn't on any of the storefronts...
PLA_LITE_DATA = {
    "Black": '16100',
    "Gray": '16101',
    "White": '16103',
    "Red": '16200',
    "Yellow": '16400',
    "Cyan": '16600',
    "Blue": '16601',
    "Matte Beige": '16602',
}

# PLA Tough was discontinued in favor of PLA Tough+
# XXX Codes are made up; we don't know what they were 
PLA_TOUGH_DATA = {
    "Lavender Blue": '12005',
    "Light Blue": '12004',
    "Orange": '12002',
    "Silver": '12001',
    "Vermilion Red": '12003',
    "Yellow": '12000',
}

# Support for PA/PET is no longer on the stores
SUPPORT_FOR_PA_PET_DATA = {
    "Green": '65500'
}

requests_cache.install_cache('.bambulab_cache', expire_after=timedelta(days=1))

# -----

def normalize_homoglyphs(text: str) -> str:
    # Mapping of common Cyrillic characters to Latin equivalents
    cyrillic_to_latin = {
        'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
        'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Т': 'T',
        'Х': 'X', 'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o',
        'р': 'p', 'х': 'x',

        # Less common ones
        'І': 'I', 'і': 'i', 'Ј': 'J', 'ј': 'j', 'Љ': 'Lj',
        'љ': 'lj', 'Њ': 'Nj', 'њ': 'nj', 'У': 'Y', 'у': 'y',
        'Д': 'D', 'д': 'd', 'З': '3', 'з': '3',
    }

    return ''.join(cyrillic_to_latin.get(char, char) for char in text)

def get_page(url, attempt=0):
    req = requests.get(url, headers=REQ_HEADERS)
    soup = BeautifulSoup(req.text, "html.parser")

    if soup.title and soup.title.string == "Just a moment...":
        if attempt >= RETRIES:
            raise Exception(f"CloudFlare prohibiting connection, please try again later")

        print(f"CloudFlare limitations, retrying in {RETRY_DELAY} seconds... ({attempt+1}/{RETRIES})")
        time.sleep(RETRY_DELAY)
        return get_page(url, attempt + 1)

    return soup

def get_category(title):
    for category, materials in CATEGORIES.items():
        if title in materials:
            return category
    
    raise Exception(f"Category for {title} is not specified!")

def get_product(product_url):
    soup = get_page(product_url)

    # Get title
    h1 = soup.select_one("h1")
    if not h1:
        return None
    title = h1.get_text(strip=True)

    if "bundle" in title.lower():
        return None

    # Get colors
    colors = {}
    color_selector = soup.select_one(".property_selector_Color")
    if not color_selector:
        return None
    for el in color_selector.select("li"):
        color = re.sub(r"^(Matte|ABS|Glow) ", "", normalize_homoglyphs(el.get("value"))).title().replace(" To ", " to ")

        # Match pattern like "Color Name (12345)"
        match = re.match(r"^([\w\s-]+?)\s?\((\d{5})\)", color)

        color_name = match.group(1).strip() if match else color
        filament_code = FILAMENT_CODE_OVERRIDES.get(color_name, match.group(2) if match else None)
        colors[color_name] = filament_code

    return (title, colors)

def get_products():
    print("Getting products from Bambu Lab, this may take a while...")
    soup = get_page(f"{BASE_URL}/collections/bambu-lab-3d-printer-filament?Compatibility=Compatible+with+AMS")

    product_links = list(filter(lambda a: not any(s in a.get('bl-m-value', '') for s in ['Bundle', 'Pack']), soup.select("a.ProductItem__ImageWrapper")))

    # PETG Basic is not in the "Compatible with AMS" category anymore...not sure why
    product_links.append({"href": "/products/petg-basic"})

    products = []
    i = 1
    for a in product_links:
        try:
            print(f"Getting product {i} of {len(product_links)}...")
            href = a.get("href")
            if href and "/products/" in href:
                product = get_product(BASE_URL + href)
                if product:
                    products.append(product)
                i += 1
        except Exception as e:
            print(f"Failed on {a.get('href')}")
            logging.error(traceback.format_exc())
    
    return products

def get_materials():
    materials = {k: {l: {} for l in CATEGORIES[k]} for k in CATEGORIES}

    for product in get_products():
        material, colors = product
        category = get_category(material)
        materials[category][material] = colors

    # Add overrides
    materials["PLA"]["PLA Lite"] = PLA_LITE_DATA
    materials["PLA"]["PLA Tough"] = PLA_TOUGH_DATA
    materials["PLA"]["PLA Aero"]["Black"] = "14103"
    materials["ABS"]["ABS"]["Yellow"] = "40401" # Superseded by Tangerine Yellow
    materials["Support Material"]["Support for PA/PET"] = SUPPORT_FOR_PA_PET_DATA

    return materials

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

    suffix = readme[next_section:] if next_section != -1 else ""
    updated = readme[:section_start] + header_and_legend + "\n\n" + new_tables + suffix
    readme_path.write_text(updated, encoding='utf-8')
    print(f"README updated: {readme_path}")

if __name__ == "__main__":
    materials = get_materials()
    generate_tables(materials, "./README.md")
