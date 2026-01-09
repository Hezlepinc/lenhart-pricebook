# Lenhart Electric Price Book

Mobile-first, offline-capable price book PWA for Lenhart Electric technicians.

## Features

- **Mobile-First Design** - Optimized for tablet/phone use in the field
- **Offline Mode** - Works without internet in customer homes (PWA)
- **Good/Better/Best Tiers** - Easily present upgrade options to customers
- **Estimate Builder** - Build quotes, copy package IDs to NetSuite
- **CRM Sync** - Import pricing directly from NetSuite exports
- **Admin Dashboard** - Upload CSVs, assign tiers, configure upsells

## Quick Start

### View the App

1. Open `index.html` in a browser (or use a local server for PWA features)
2. For PWA features, use: `npx serve` or `python -m http.server 8000`

### Admin Dashboard

1. Open `admin.html` in a browser
2. Upload a new CRM export CSV to update packages
3. Assign Good/Better/Best tiers to packages
4. Export updated `pricebook.json`
5. Copy to `data/` folder and push to GitHub

## Updating Prices

### Method 1: Admin Dashboard (Recommended)

1. Export data from NetSuite as CSV
2. Open `admin.html`
3. Upload the CSV file
4. Review/adjust tier assignments
5. Click "Export JSON"
6. Replace `data/pricebook.json` with the downloaded file
7. Push to GitHub

### Method 2: Python Script

```bash
python scripts/import-crm.py path/to/crm-export.xls
git add . && git commit -m "Update prices" && git push
```

## Deployment

### GitHub Pages (Free)

1. Push to GitHub
2. Go to Settings > Pages
3. Select "main" branch, "/ (root)" folder
4. Access at `https://yourusername.github.io/lenhart-pricebook`

### Custom Domain

1. Add a `CNAME` file with your domain (e.g., `pricebook.lenhartelectric.com`)
2. Configure DNS with your domain provider

## Project Structure

```
lenhart-pricebook/
├── index.html          # Technician-facing app (lifestyle presentation)
├── admin.html          # Admin dashboard for updates
├── data/
│   └── pricebook.json  # Package data (auto-generated)
├── scripts/
│   └── import-crm.py   # NetSuite XML/CSV converter
├── images/
│   ├── icon.svg        # App icon
│   ├── logo.png        # Lenhart Electric logo
│   └── heroes/         # Category hero images (lifestyle photos)
├── manifest.json       # PWA manifest
└── sw.js               # Service worker for offline
```

## Adding Hero Images

The app supports lifestyle/hero images for each category. To add images:

1. Add images to `images/heroes/` with these filenames:
   - `bathrooms.jpg`
   - `ceiling-fans.jpg`
   - `ev-charging.jpg`
   - `exterior-lighting.jpg`
   - `exterior-outlets.jpg`
   - `heavy-duty-circuits.jpg`
   - `generators.jpg`
   - `hot-tub.jpg`
   - `interior-lighting.jpg`
   - `led-tape.jpg`
   - `outlets-switches.jpg`
   - `panel-upgrades.jpg`
   - `portable-generator.jpg`
   - `recessed-lighting.jpg`
   - `service-upgrades.jpg`
   - `smoke-detectors.jpg`
   - `surge-protection.jpg`
   - `whole-home-rewire.jpg`

2. Recommended image specs:
   - **Size**: 800 x 500px (or similar 1.6:1 aspect ratio)
   - **Format**: JPG (optimized for web, ~50-150KB each)
   - **Style**: Lifestyle photos showing the service in a home setting

3. Layout behavior:
   - **Mobile/Tablet**: Image on top, title and price below
   - **Desktop**: Image on left (60%), title and price on right (40%)

4. If an image is missing, the app shows a gradient background - no errors.

## Adding Package Images

You can add product images to individual packages:

1. Add images to `images/products/` folder
2. Update `data/pricebook.json` to include image URLs:
   ```json
   {
     "name": "AMSFL_EV CHARGER",
     "image": "images/products/ev-charger.jpg",
     ...
   }
   ```

Without images, packages display the Lenhart Electric logo placeholder.

## Brand Colors

- Header: `#6d7b8a` (gray)
- Accent: `#3b6e9c` (blue)
- Price highlight: `#c4a35a` (gold)

## Tech Workflow

1. Open Price Book app on tablet
2. Browse categories or search for packages
3. Tap packages to add to estimate
4. Present Good/Better/Best options to customer
5. Tap "Copy IDs" when ready
6. Open NetSuite Field Service
7. Paste package names into search
8. Add to customer quote

## Support

For issues or updates, contact your system administrator.
