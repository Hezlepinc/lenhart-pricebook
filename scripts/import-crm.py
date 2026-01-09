#!/usr/bin/env python3
"""
NetSuite CRM Export to Price Book JSON Converter
Parses NetSuite XML SpreadsheetML or CSV exports and generates pricebook.json

Usage:
    python import-crm.py path/to/export.xls
    python import-crm.py path/to/export.csv
"""

import json
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Category mapping based on package name patterns
CATEGORY_PATTERNS = [
    (r'(PANEL|SERVICE.*PANEL|SUB PANEL)', 'Panel Upgrades'),
    (r'SURGE', 'Surge Protection'),
    (r'(E CAR|EV CIRCUIT|EV CHARGER)', 'EV Charging'),
    (r'HOT TUB', 'Hot Tub Circuits'),
    (r'240V.*CKT(?!.*EV)', 'Heavy Duty Circuits'),
    (r'OUTLET.*WP|WP.*OUTLET', 'Exterior Outlets'),
    (r'(FLOOD|SOFFIT|COACH LT|LANDSCAPE)', 'Exterior Lighting'),
    (r'(RCAN|WAFER|RECESSED)', 'Recessed Lighting'),
    (r'TAPE LT', 'LED Tape Lighting'),
    (r'(OUTLET|SWITCH|DIMMER|RECEPTACLE)(?!.*WP)', 'Outlets & Switches'),
    (r'(FIXTURE|LIGHT BOX|CHANDELIER|PENDANT)', 'Interior Lighting'),
    (r'(FAN|CEILING FAN)', 'Ceiling Fans'),
    (r'(EXHAUST|BATH FAN|VENT FAN)', 'Bathrooms'),
    (r'(GEN |GENERATOR|18KW|22KW|24KW|26KW)', 'Home Generators'),
    (r'INTERLOCK', 'Portable Generator'),
    (r'AIR CONDITIONER|A/C|AC CIRCUIT', 'HVAC Circuits'),
    (r'SMOKE|CARBON|CO DETECTOR', 'Safety Devices'),
    (r'GFCI|GFI', 'GFCI Protection'),
    (r'BREAKER', 'Breakers'),
]

def categorize_package(name):
    """Determine category based on package name patterns"""
    name_upper = name.upper()
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, name_upper):
            return category
    return 'Other Services'

def parse_xml_spreadsheet(filepath):
    """Parse NetSuite XML SpreadsheetML format"""
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Handle namespaces
    ns = {
        'ss': 'urn:schemas-microsoft-com:office:spreadsheet',
        'o': 'urn:schemas-microsoft-com:office:office',
        'x': 'urn:schemas-microsoft-com:office:excel'
    }

    rows = []
    worksheet = root.find('.//ss:Worksheet', ns)
    if worksheet is None:
        # Try without namespace
        for elem in root.iter():
            if 'Worksheet' in elem.tag:
                worksheet = elem
                break

    table = worksheet.find('.//ss:Table', ns) if worksheet is not None else None
    if table is None:
        for elem in root.iter():
            if 'Table' in elem.tag:
                table = elem
                break

    if table is None:
        raise ValueError("Could not find Table element in XML")

    for row in table.iter():
        if 'Row' in row.tag:
            cells = []
            for cell in row.iter():
                if 'Cell' in cell.tag:
                    data = None
                    for d in cell.iter():
                        if 'Data' in d.tag:
                            data = d.text or ''
                            break
                    cells.append(data if data else '')
            if cells:
                rows.append(cells)

    return rows

def parse_csv(filepath):
    """Parse CSV export"""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows

def clean_price(price_str):
    """Convert price string to number"""
    if not price_str:
        return 0
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[,$]', '', str(price_str))
        return float(cleaned)
    except (ValueError, TypeError):
        return 0

def clean_hours(hours_str):
    """Convert hours string to number"""
    if not hours_str:
        return 0
    try:
        return float(hours_str)
    except (ValueError, TypeError):
        return 0

def process_crm_data(rows):
    """Process raw rows into structured package data"""
    if not rows:
        return []

    # First row is header
    header = [str(h).strip() for h in rows[0]]

    # Find column indices
    col_map = {}
    for i, h in enumerate(header):
        h_lower = h.lower()
        if 'internal id' in h_lower:
            col_map['id'] = i
        elif h_lower == 'name':
            col_map['name'] = i
        elif 'sales price' in h_lower:
            col_map['price'] = i
        elif 'labor hours' in h_lower:
            col_map['hours'] = i
        elif 'labor cost' in h_lower:
            col_map['labor_cost'] = i
        elif 'description' in h_lower:
            col_map['description'] = i
        elif 'show on mobile' in h_lower:
            col_map['show_mobile'] = i

    packages = []
    for row in rows[1:]:
        if len(row) < max(col_map.values(), default=0) + 1:
            continue

        name = row[col_map.get('name', 1)] if col_map.get('name') is not None else ''
        if not name or not name.strip():
            continue

        # Check if should show on mobile
        show_mobile = row[col_map.get('show_mobile', 6)] if col_map.get('show_mobile') is not None else 'Yes'
        if show_mobile and 'no' in str(show_mobile).lower():
            continue

        price = clean_price(row[col_map.get('price', 5)] if col_map.get('price') is not None else 0)
        if price <= 0:
            continue

        # Clean up name - remove AMSFL_ or GENFL_ prefix for display
        display_name = re.sub(r'^(AMSFL_|GENFL_)', '', name).strip()
        display_name = display_name.replace('INSTALL ', '').strip()

        package = {
            'id': row[col_map.get('id', 0)] if col_map.get('id') is not None else '',
            'name': name,
            'displayName': display_name,
            'price': price,
            'laborHours': clean_hours(row[col_map.get('hours', 3)] if col_map.get('hours') is not None else 0),
            'description': row[col_map.get('description', 8)] if col_map.get('description') is not None else '',
            'category': categorize_package(name),
            'tier': None,  # To be assigned in admin dashboard
            'upsellTo': []  # Related upsell packages
        }
        packages.append(package)

    return packages

def organize_by_category(packages):
    """Group packages by category and find starting prices"""
    categories = defaultdict(lambda: {'packages': [], 'startingAt': float('inf')})

    for pkg in packages:
        cat = pkg['category']
        categories[cat]['packages'].append(pkg)
        if pkg['price'] < categories[cat]['startingAt']:
            categories[cat]['startingAt'] = pkg['price']

    # Convert to list and sort by category name
    result = []
    for name, data in sorted(categories.items()):
        # Sort packages within category by price
        data['packages'].sort(key=lambda x: x['price'])
        result.append({
            'name': name,
            'startingAt': data['startingAt'],
            'packages': data['packages'],
            'icon': get_category_icon(name)
        })

    return result

def get_category_icon(category):
    """Return emoji icon for category"""
    icons = {
        'Panel Upgrades': 'zap',
        'Surge Protection': 'shield',
        'EV Charging': 'battery-charging',
        'Hot Tub Circuits': 'droplet',
        'Heavy Duty Circuits': 'plug',
        'Exterior Outlets': 'sun',
        'Exterior Lighting': 'sun',
        'Recessed Lighting': 'circle',
        'LED Tape Lighting': 'minus',
        'Outlets & Switches': 'toggle-right',
        'Interior Lighting': 'lamp',
        'Ceiling Fans': 'wind',
        'Bathrooms': 'droplet',
        'Home Generators': 'power',
        'Portable Generator': 'battery',
        'HVAC Circuits': 'thermometer',
        'Safety Devices': 'alert-circle',
        'GFCI Protection': 'shield',
        'Breakers': 'square',
    }
    return icons.get(category, 'package')

def main():
    if len(sys.argv) < 2:
        # Default to looking for common export names
        search_paths = [
            Path('../AMSItemGroupCatalogwPriceResults547.xls'),
            Path('../crm_export.csv'),
            Path('AMSItemGroupCatalogwPriceResults547.xls'),
            Path('crm_export.csv'),
        ]
        filepath = None
        for p in search_paths:
            if p.exists():
                filepath = p
                break
        if not filepath:
            print("Usage: python import-crm.py <path-to-crm-export>")
            print("Supports: .xls (XML SpreadsheetML) or .csv files")
            sys.exit(1)
    else:
        filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    print(f"Reading: {filepath}")

    # Detect format and parse
    with open(filepath, 'rb') as f:
        start = f.read(100)

    if b'<?xml' in start or b'<Workbook' in start:
        print("Detected: XML SpreadsheetML format")
        rows = parse_xml_spreadsheet(filepath)
    else:
        print("Detected: CSV format")
        rows = parse_csv(filepath)

    print(f"Found {len(rows) - 1} rows (excluding header)")

    # Process data
    packages = process_crm_data(rows)
    print(f"Processed {len(packages)} valid packages")

    # Organize by category
    categories = organize_by_category(packages)
    print(f"Organized into {len(categories)} categories")

    # Build output structure
    output = {
        'version': '1.0',
        'lastUpdated': None,  # Will be set by admin dashboard
        'categories': categories
    }

    # Write JSON
    output_path = Path(__file__).parent.parent / 'data' / 'pricebook.json'
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\nGenerated: {output_path}")
    print(f"\nCategory Summary:")
    for cat in categories:
        print(f"  {cat['name']}: {len(cat['packages'])} packages (starting at ${cat['startingAt']:,.0f})")

    print("\nNext steps:")
    print("1. Open admin.html to review and assign Good/Better/Best tiers")
    print("2. Configure upsell relationships")
    print("3. Push to GitHub to deploy")

if __name__ == '__main__':
    main()
