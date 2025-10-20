#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import html
import traceback
import requests
from bs4 import BeautifulSoup
from slugify import slugify

# إعدادات عامة
SITEMAP_URL = "https://tagerkwait.sellsite.net/sitemap.xml"
OUTPUT_DIR = "products"
DEFAULT_CURRENCY = "KWD"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 0.6  # ثوانٍ بين الطلبات لتخفيف الضغط

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0.0.0 Safari/537.36"
})

def get_text(tag, attr):
    """إرجاع قيمة الخاصية إن وُجدت وإلا None."""
    try:
        if tag and tag.get(attr):
            return tag.get(attr).strip()
    except Exception:
        pass
    return None

def get_meta_content(soup, key, value):
    """جلب content من وسم meta حسب property أو name."""
    tag = soup.find("meta", {key: value})
    return get_text(tag, "content")

def fetch(url):
    """طلب صفحة مع معالجة الأخطاء."""
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp

def parse_sitemap_links(sitemap_url):
    """إرجاع روابط المنتجات من خريطة الموقع."""
    resp = fetch(sitemap_url)
    soup = BeautifulSoup(resp.text, "xml")
    locs = [loc.text.strip() for loc in soup.find_all("loc")]
    # اختيار روابط المنتجات فقط
    product_links = [u for u in locs if "/products/" in u]
    # إزالة التكرارات والحفاظ على الترتيب
    seen = set()
    ordered = []
    for u in product_links:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered

def ensure_unique_slug(base_slug, existing):
    """ضمان عدم تكرار الـ slug."""
    if base_slug not in existing:
        existing[base_slug] = 1
        return base_slug
    n = existing[base_slug]
    existing[base_slug] = n + 1
    return f"{base_slug}-{n}"

def scrape_product(link, slug_counts):
    """سحب بيانات المنتج من صفحة المنتج."""
    page = fetch(link)
    soup = BeautifulSoup(page.text, "html.parser")

    # العنوان
    title = get_meta_content(soup, "property", "og:title") \
            or (soup.title.get_text(strip=True) if soup.title else None) \
            or link.rstrip("/").split("/")[-1].replace("-", " ").title()

    # الصورة
    image = get_meta_content(soup, "property", "og:image")
    if not image:
        img_tag = soup.find("img", src=True)
        image = img_tag["src"].strip() if img_tag else ""

    # الوصف
    desc = get_meta_content(soup, "name", "description")
    if not desc:
        # محاولة أخذ أول فقرة مفيدة
        p = soup.find("p")
        desc = p.get_text(" ", strip=True) if p else f"منتج: {title}"

    # السعر والعملة
    price_raw = get_meta_content(soup, "property", "product:price:amount")
    currency = get_meta_content(soup, "property", "product:price:currency") or DEFAULT_CURRENCY

    # تنظيف السعر ليسمح فقط بالأرقام والنقطة والفاصلة
    price = None
    if price_raw:
        cleaned = "".join(ch for ch in price_raw if ch.isdigit() or ch in ".,")
        price = cleaned.replace(",", ".") if cleaned else None

    # إنشاء slug فريد
    base_slug = slugify(title)
    slug = ensure_unique_slug(base_slug, slug_counts)

    # JSON-LD وفق Schema.org Product + Offer
    product_schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": title,
        "image": image,
        "description": desc,
        "brand": {
            "@type": "Brand",
            "name": "المتجر الكويتي"
        }
    }

    # إضافة العرض إذا وُجد سعر
    if price:
        product_schema["offers"] = {
            "@type": "Offer",
            "url": link,
            "price": price,
            "priceCurrency": currency,
            "availability": "https://schema.org/InStock"
        }

    json_ld = json.dumps(product_schema, ensure_ascii=False, separators=(",", ":"))

    # هروب للنصوص ضمن صفات HTML
    esc_title_attr = html.escape(title, quote=True)
    esc_desc_attr = html.escape(desc, quote=True)
    esc_image_attr = html.escape(image, quote=True)
    esc_link_attr = html.escape(link, quote=True)

    # عرض السعر النصي
    display_price = f"{price} {currency}" if price else "السعر غير متاح"

    # بناء صفحة HTML للمنتج
    html_page = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc_title_attr}</title>
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
    <img src="{esc_image_attr}" alt="{esc_title_attr}" style="max-width:300px;border-radius:10px;">
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(desc)}</p>
    <p><strong>{html.escape(display_price)}</strong></p>
    <a href="{esc_link_attr}" class="btn">اشتري الآن</a>
  </main>
</body>
</html>
"""

    return {
        "title": title,
        "price": display_price,
        "image": image,
        "link": link,
        "slug": slug,
        "desc": desc,
        "html": html_page
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("جاري سحب روابط المنتجات...")
    try:
        links = parse_sitemap_links(SITEMAP_URL)
    except Exception:
        print("تعذر قراءة خريطة الموقع:")
        traceback.print_exc()
        return

    print(f"تم العثور على {len(links)} رابط منتج")
    products = []
    slug_counts = {}

    for i, link in enumerate(links, start=1):
        try:
            print(f"[{i}/{len(links)}] سحب: {link}")
            item = scrape_product(link, slug_counts)

            # حفظ صفحة المنتج
            out_path = os.path.join(OUTPUT_DIR, f"{item['slug']}.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(item["html"])

            # حفظ بيانات JSON
            products.append({
                "title": item["title"],
                "price": item["price"],
                "image": item["image"],
                "link": item["link"],
                "slug": item["slug"],
                "desc": item["desc"]
            })

        except Exception:
            print("خطأ أثناء معالجة:", link)
            traceback.print_exc()

        time.sleep(REQUEST_DELAY)

    # حفظ ملف JSON للمنتجات
    json_path = os.path.join(OUTPUT_DIR, "products.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"تم إنشاء {len(products)} منتج بنجاح ✅")

if __name__ == "__main__":
    main()
