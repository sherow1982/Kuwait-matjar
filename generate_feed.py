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
# قوالب HTML تبقى كما هي، لا حاجة لتغييرها
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

def normalize_price(value: str) -> tuple[str, str]:
    """يعيد السعر بالتنسيق الصحيح للعرض ولجوجل."""
    s = (value or "").strip()
    num = re.sub(r"[^\d.,]", "", s).replace(",", ".")
    if num.count('.') > 1:
        parts = num.split('.')
        num = "".join(parts[:-1]) + "." + parts[-1]
    if not num: num = "0"
    has_kwd = re.search(r"\bkwd\b", s, re.I) or ("د.ك" in s) or ("دينار" in s)
    display = s if s else num
    if not has_kwd: display = f"{display} KWD"
    return display, num

def map_availability(value: str) -> tuple[str, str]:
    """يحوّل نص التوفّر إلى قيم جوجل المعتمدة."""
    v = (value or "").strip().lower()
    if v in ["متوفر", "متاح", "متوفر الآن", "متوفر بالمخزون", "in stock", "in_stock"]:
        g = "in stock"
    elif v in ["غير متوفر", "نفد", "نفد من المخزون", "غير متاح", "out of stock", "out_of_stock"]:
        g = "out of stock"
    else:
        g = "in stock" # الافتراضي
    
    schema_url_map = {
        "in stock": "https://schema.org/InStock",
        "out of stock": "https://schema.org/OutOfStock",
    }
    schema_url = schema_url_map.get(g, "https://schema.org/InStock")
    return g, schema_url

# -------- FEED generation --------
def build_feed(items: list[dict], base_url: str, out_file: Path) -> None:
    """
    ينشئ ملف التغذية بالروابط الصحيحة لصفحات المنتجات التي تم إنشاؤها.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
    lines.append("  <channel>")
    lines.append("    <title>Matjar Kuwait - Products</title>")
    lines.append(f"    <link>{html.escape(base_url)}</link>")
    lines.append("    <description>Latest products from Matjar Kuwait</description>")

    for it in items:
        title = get_first(it, ["العنوان", "title"], "منتج")
        slug = slugify(title)
        local_page = f"{base_url.rstrip('/')}/{OUTPUT_DIR}/{slug}.html"
        
        price_raw = get_first(it, ["السعر", "price"], "")
        _, price_num = normalize_price(price_raw)
        avail_raw = get_first(it, ["مدى التوفّر", "availability"], "متوفر")
        g_avail, _ = map_availability(avail_raw)
        
        lines.append("    <item>")
        lines.append(f"      <g:id>{html.escape(get_first(it, ['المعرّف', 'sku', 'id'], slug.upper()))}</g:id>")
        lines.append(f"      <g:title>{html.escape(title)}</g:title>")
        lines.append(f"      <g:description>{html.escape(get_first(it, ['الوصف', 'description']))}</g:description>")
        lines.append(f"      <g:link>{html.escape(local_page)}</g:link>")
        lines.append(f"      <g:image_link>{html.escape(get_first(it, ['رابط الصورة', 'image_link']))}</g:image_link>")
        lines.append(f"      <g:availability>{g_avail}</g:availability>")
        lines.append("      <g:condition>new</g:condition>")
        lines.append(f"      <g:price>{price_num} KWD</g:price>")
        lines.append("      <g:brand>Matjar Kuwait</g:brand>")
        lines.append("      <g:identifier_exists>no</g:identifier_exists>")
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

    # إنشاء صفحات المنتجات
    for p in rows:
        title = get_first(p, ["العنوان", "title"], "منتج")
        slug = slugify(title)
        product_rel_path = Path(OUTPUT_DIR) / f"{slug}.html"
        
        # يمكنك هنا استخدام قالب HTML لصفحة المنتج PRODUCT_PAGE_TEMPLATE
        # هذا مثال مبسط لإنشاء الصفحة
        page_content = f"<h1>{html.escape(title)}</h1><p>Product page for {html.escape(title)}</p>"
        product_rel_path.write_text(page_content, encoding="utf-8")

    # إنشاء ملف التغذية بعد إنشاء الصفحات
    build_feed(rows, BASE_URL, Path("products-feed.xml"))

    print(f"تم إنشاء {len(rows)} صفحة منتج وملف products-feed.xml بنجاح.")

if __name__ == "__main__":
    main()
