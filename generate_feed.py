import csv
import os
import re
import json
import html
from pathlib import Path

# -------- CONFIG --------
OUTPUT_DIR = "products"            # مجلد صفحات المنتجات
CSV_FILE = "products.csv"          # ملف المنتجات بصيغة CSV
CSS_FILE = "style.css"             # ملف الستايل في الجذر
BASE_URL = "https://sherow1982.github.io/Kuwait-matjar/"  # رابط متجرك

# -------- HTML Templates --------
# ... (قوالب HTML تبقى كما هي) ...
INDEX_TEMPLATE = '''...'''
CARD_TEMPLATE = '''...'''
PRODUCT_PAGE_TEMPLATE = '''...'''

# -------- Helpers --------
def slugify(text: str) -> str:
    """Slug عربي/لاتيني بسيط مع إزالة الرموز غير المرغوبة."""
    if not text:
        return "product"
    text = text.strip().lower()
    text = re.sub(r"[^\u0600-\u06FF0-9a-zA-Z\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")[:80] or "product"

def get_first(d: dict, keys: list[str], default: str = "") -> str:
    """يحاول استخراج أول قيمة موجودة من مجموعة مفاتيح محتملة."""
    for k in keys:
        if k in d and str(d[k]).strip():
            return str(d[k]).strip()
    return default

# ... (باقي الدوال المساعدة تبقى كما هي) ...

# -------- FEED generation --------
def build_feed(items: list[dict], base_url: str, out_file: Path) -> None:
    """
    ينشئ ملف تغذية بصيغة RSS 2.0 مع مساحة الأسماء g وفق مواصفات Google Merchant.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
    lines.append("  <channel>")
    lines.append("    <title>Matjar Kuwait - Products</title>")
    lines.append(f"    <link>{html.escape(base_url)}</link>")
    lines.append("    <description>Latest products from Matjar Kuwait</description>")

    for it in items:
        title = get_first(it, ["العنوان", "عنوان", "title", "name"], "منتج")
        img = get_first(it, ["رابط الصورة", "الصورة", "image", "image_link"], "")
        desc = get_first(it, ["الوصف", "description", "desc"], "")
        price_raw = get_first(it, ["السعر", "price"], "")
        avail_raw = get_first(it, ["مدى التوفّر", "التوفر", "availability"], "متوفر")
        sku = get_first(it, ["المعرّف", "sku", "id"], "")

        slug = slugify(title)
        local_page = f"{base_url.rstrip('/')}/{OUTPUT_DIR}/{slug}.html"

        _, price_num = normalize_price(price_raw)
        g_avail, _ = map_availability(avail_raw)

        lines.append("    <item>")
        lines.append(f"      <g:id>{html.escape(sku or slug.upper())}</g:id>")
        lines.append(f"      <g:title>{html.escape(title)}</g:title>")
        lines.append(f"      <g:description>{html.escape(desc)}</g:description>")
        lines.append(f"      <g:link>{html.escape(local_page)}</g:link>")
        lines.append(f"      <g:image_link>{html.escape(img)}</g:image_link>")
        lines.append(f"      <g:availability>{g_avail}</g:availability>")
        lines.append("      <g:condition>new</g:condition>")
        lines.append(f"      <g:price>{price_num} KWD</g:price>")
        lines.append("      <g:brand>Matjar Kuwait</g:brand>")
        lines.append("      <g:identifier_exists>no</g:identifier_exists>")
        lines.append("      <g:shipping>")
        lines.append("        <g:country>KW</g:country>")
        lines.append("        <g:service>Standard</g:service>")
        lines.append("        <g:price>0.00 KWD</g:price>")
        lines.append("      </g:shipping>")
        lines.append("    </item>")

    lines.append("  </channel>")
    lines.append("</rss>")

    out_file.write_text("\n".join(lines), encoding="utf-8")

# -------- MAIN --------
def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    try:
        with open(CSV_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"خطأ: لم يتم العثور على الملف {CSV_FILE}")
        return

    # ... (باقي كود بناء صفحات المنتجات و index.html يبقى كما هو) ...

    # تعديل اسم ملف التغذية هنا
    build_feed(rows, BASE_URL, Path("products-feed.xml"))

    print(f"تم إنشاء {len(rows)} صفحة منتج وملف products-feed.xml بنجاح.")

if __name__ == "__main__":
    main()
