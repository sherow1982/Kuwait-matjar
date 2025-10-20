#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import html
import pathlib
import pandas as pd
from slugify import slugify

# Input Excel (try data/ then root)
CANDIDATES = [
    pathlib.Path("data/products-template.xlsx"),
    pathlib.Path("products-template.xlsx")
]

OUTPUT_DIR = pathlib.Path("products")
DEFAULT_CURRENCY = "KWD"
DEFAULT_BRAND = "المتجر الكويتي"
DEFAULT_AVAIL = "https://schema.org/InStock"

def find_excel():
    for p in CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("Excel file not found. Put it at data/products-template.xlsx")

def clean_price(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    keep = "".join(ch for ch in s if ch.isdigit() or ch in ".,")
    if not keep:
        return None
    return keep.replace(",", ".")

def build_jsonld(title, image, desc, link, price, currency, brand, availability):
    offers = None
    if price:
        offers = {
            "@type": "Offer",
            "url": link or "",
            "price": price,
            "priceCurrency": currency or DEFAULT_CURRENCY,
            "availability": availability or DEFAULT_AVAIL
        }
    data = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": title,
        "image": image or "",
        "description": desc or "",
        "brand": {"@type": "Brand", "name": brand or DEFAULT_BRAND}
    }
    if offers:
        data["offers"] = offers
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

def render_html(title, image, desc, display_price, buy_link, json_ld):
    esc_title = html.escape(title, quote=True)
    esc_desc_attr = html.escape(desc or "", quote=True)
    esc_img = html.escape(image or "", quote=True)
    esc_buy = html.escape(buy_link or "#", quote=True)
    body_title = html.escape(title)
    body_desc = html.escape(desc or "")
    body_price = html.escape(display_price or "")
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title}</title>
  <meta name="description" content="{esc_desc_attr}">
  <link rel="stylesheet" href="../style.css">
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>
  <header>
    <a href="../index.html">العودة للرئيسية</a>
  </header>
  <main>
    <img src="{esc_img}" alt="{esc_title}" style="max-width:300px;border-radius:10px;">
    <h1>{body_title}</h1>
    <p>{body_desc}</p>
    {f'<p><strong>{body_price}</strong></p>' if display_price else ''}
    <a href="{esc_buy}" class="btn">اشتري الآن</a>
  </main>
</body>
</html>
"""

def main():
    excel_path = find_excel()
    df = pd.read_excel(excel_path, engine="openpyxl").fillna("")  # requires openpyxl
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    products = []
    used_slugs = set()

    for _, row in df.iterrows():
        title = (row.get("title") or "").strip()
        if not title:
            continue
        desc = (row.get("desc") or "").strip()
        image = (row.get("image") or "").strip()
        link = (row.get("link") or "").strip()
        price = clean_price(row.get("price"))
        currency = (row.get("currency") or DEFAULT_CURRENCY).strip()
        brand = (row.get("brand") or DEFAULT_BRAND).strip()
        availability_raw = (row.get("availability") or "InStock").strip()
        availability = f"https://schema.org/{availability_raw}" if "schema.org" not in availability_raw else availability_raw

        # slug
        custom_slug = (row.get("slug") or "").strip()
        slug = custom_slug or slugify(title)
        base = slug
        i = 1
        while slug in used_slugs:
            slug = f"{base}-{i}"
            i += 1
        used_slugs.add(slug)

        json_ld = build_jsonld(title, image, desc, link, price, currency, brand, availability)
        display_price = f"{price} {currency}" if price else ""
        html_page = render_html(title, image, desc, display_price, link, json_ld)

        # write HTML
        (OUTPUT_DIR / f"{slug}.html").write_text(html_page, encoding="utf-8")

        # accumulate JSON for index
        products.append({
            "title": title,
            "price": display_price,
            "image": image,
            "link": link,
            "slug": slug,
            "desc": desc
        })

    # write products.json
    (OUTPUT_DIR / "products.json").write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(products)} products into {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
