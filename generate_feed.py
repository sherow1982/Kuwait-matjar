import csv
import re
import html
from pathlib import Path
from urllib.parse import urlencode

# --- إعدادات أساسية ---
CSV_FILE = "products.csv"
BASE_URL = "https://sherow1982.github.io/Kuwait-matjar/"
OUTPUT_FEED_FILE = "products-feed.xml"

# --- دوال مساعدة ---
def get_first(d: dict, keys: list[str], default: str = "") -> str:
    for k in keys:
        if k in d and str(d[k]).strip():
            return str(d[k]).strip()
    return default

def normalize_price(value: str) -> str:
    s = (value or "").strip()
    num = re.sub(r"[^\d.,]", "", s).replace(",", ".")
    if num.count('.') > 1:
        parts = num.split('.')
        num = "".join(parts[:-1]) + "." + parts[-1]
    return num if num else "0"

def map_availability(value: str) -> str:
    v = (value or "").strip().lower()
    if v in ["متوفر", "متاح", "in stock"]:
        return "in stock"
    elif v in ["غير متوفر", "نفد", "out of stock"]:
        return "out of stock"
    return "in stock"

# --- إنشاء ملف التغذية ---
def build_feed(items: list[dict], base_url: str, out_file: Path) -> None:
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
    lines.append("  <channel>")
    lines.append("    <title>Matjar Kuwait - Products</title>")
    lines.append(f"    <link>{html.escape(base_url)}</link>")
    lines.append("    <description>Latest products from Matjar Kuwait</description>")

    for it in items:
        title = get_first(it, ["العنوان", "title"], "منتج")
        price_num = normalize_price(get_first(it, ["السعر", "price"], ""))
        g_avail = map_availability(get_first(it, ["مدى التوفّر", "availability"], "متوفر"))
        
        product_param = urlencode({"name": title})
        product_link = f"{base_url.rstrip('/')}/product.html?{product_param}"
        
        lines.append("    <item>")
        lines.append(f"      <g:id>{html.escape(get_first(it, ['المعرّف', 'sku', 'id'], title.upper()))}</g:id>")
        lines.append(f"      <g:title>{html.escape(title)}</g:title>")
        lines.append(f"      <g:description>{html.escape(get_first(it, ['الوصف', 'description']))}</g:description>")
        lines.append(f"      <g:link>{html.escape(product_link)}</g:link>")
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

# --- التشغيل ---
def main():
    try:
        with open(CSV_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"خطأ: لم يتم العثور على الملف {CSV_FILE}")
        return

    build_feed(rows, BASE_URL, Path(OUTPUT_FEED_FILE))
    print(f"تم إنشاء ملف {OUTPUT_FEED_FILE} بنجاح.")

if __name__ == "__main__":
    main()
