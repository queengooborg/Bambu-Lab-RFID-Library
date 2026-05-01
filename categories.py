# -*- coding: utf-8 -*-
# Shared category / material lookup tables used by multiple scripts.
# Import from here instead of duplicating these definitions.

# Maps filament_type values to top-level library category folder names
CATEGORY_MAP = {
    'PA-S':     'Support Material',
    'PLA-S':    'Support Material',
    'Support':  'Support Material',
    'PVA':      'Support Material',
    'ABS-S':    'Support Material',
    'PETG-CF':  'PETG',
    'TPU-AMS':  'TPU',
    'ABS-GF':   'ABS',
    'PLA-CF':   'PLA',
    'PA-CF':    'PA',
    'PA-GF':    'PA',
    'ASA-CF':   'ASA',
    'ASA Aero': 'ASA',
}

# Maps tag detailed_filament_type values for materials shared across multiple library folders.
# Value is (single_colour_folder, multi_colour_folder).
# Note: 'PLA Silk+' stores 'PLA Silk+' in the tag and needs no entry here.
#       'PLA Silk' covers two distinct products:
#         - PLA Silk (discontinued single-colour) -> PLA Silk/
#         - PLA Silk Multi-Color                  -> PLA Silk Multi-Color/
MULTI_COLOR_MATERIAL_MAP = {
    'PLA Silk': ('PLA Silk', 'PLA Silk Multi-Color'),
}

# Maps tag detailed_filament_type values to additional acceptable library subfolder names.
# Entries here are alternatives — the primary expected folder comes from resolve_material().
MATERIAL_MAP = {
    'Support for PA':  ['Support for PA-PET'],
    'Support For PA':  ['Support for PA-PET'],
    'Support G':       ['Support for PA-PET'],
    'Support W':       ['Support for PLA-PETG'],
    'Support for PLA': ['Support for PLA (New Version)', 'Support for PLA-PETG'],
    'PETG-CF':         ['PETG CF'],
    'PLA Basic':       ['PLA Basic Gradient'],
    'PLA':             ['PLA Silk Multi-Color'],
}


def resolve_material(tag_data):
    """
    Return the canonical library folder name for a tag's material.
    For materials in MULTI_COLOR_MATERIAL_MAP, multi-colour tags map to the
    multi folder; single-colour tags map to the single folder.
    """
    base = tag_data['detailed_filament_type']
    if base in MULTI_COLOR_MATERIAL_MAP:
        single_folder, multi_folder = MULTI_COLOR_MATERIAL_MAP[base]
        return multi_folder if tag_data.get('filament_color_count', 1) > 1 else single_folder
    return base


def allowed_material_folders(tag_data):
    """
    Return a list of acceptable library subfolder names for a tag's material.
    For MULTI_COLOR_MATERIAL_MAP entries only the resolved folder name is valid
    (the raw tag value is not a real library folder name).
    For other materials the expected folder, the raw tag value, and any MATERIAL_MAP
    aliases are all acceptable.
    """
    raw_mat = tag_data['detailed_filament_type']
    expected_mat = resolve_material(tag_data)

    if raw_mat in MULTI_COLOR_MATERIAL_MAP:
        single_folder, multi_folder = MULTI_COLOR_MATERIAL_MAP[raw_mat]
        if tag_data.get('filament_color_count', 1) > 1:
            return [multi_folder]
        else:
            return [single_folder]
    else:
        extra = MATERIAL_MAP.get(raw_mat, [])
        if not isinstance(extra, list):
            extra = [extra]
        return list(dict.fromkeys([expected_mat, raw_mat] + extra))
