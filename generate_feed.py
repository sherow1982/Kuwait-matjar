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
BASE_URL = "https://sherow1982.github.io/Kuwait-matjar/"  # حدّثه إذا تغيّر المسار

# -------- HTML Templates --------
INDEX_TEMPLATE = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>المتجر الكويتي - منتجات مميزة</title>
<link rel="stylesheet" href="{css}">
<meta name="description" content="منتجات مميزة من المتجر الكويتي بتصميم سريع وخفيف.">
</head>
<body>
<header>
  <h1>المتجر الكويتي</h1>
  <p>منتجات مميزة يتم تحديثها تلقائيًا</p>
</header>
<main class="grid">
{cards}
</main>
<footer>
  <p>© 2025 المتجر الكويتي</p>
</footer>
</body>
</html>
'''

CARD_TEMPLATE = '''
<article class="card">
  <a href="{product_page}" target="_blank" rel="noopener noreferrer">
    <img src="{image}" alt="{name}">
    <h2>{name}</h2>
    <p>{short_desc}</p>
    <span class="price">{price}</span>
  </a>
</article>
'''

PRODUCT_PAGE_TEMPLATE = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<link rel="stylesheet" href="../{css}">
<meta name="description" content="{description}">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
<header>
  <h1>{name}</h1>
</header>
<main>
  <img src="{image}" alt="{name}" style="max-width:420px;width:100%">
  <p>{description}</p>
  <p class="price">{price_display}</p>
  <a href="{original_url}" target="_blank" rel="nofollow noopener">اشترِ الآن</a>
</main>
<footer>
  <p>© 2025 المتجر الكويتي</p>
</footer>
</body>
</html>
'''

# -------- Helpers --------
def slugify(text: str) -> str:
    """Slug عربي/لاتيني بسيط مع إزالة الرموز غير المرغوبة."""
    if not text:
        return "product"
    text = text.strip().lower()
    # حذف التشكيل والعلامات
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

# احتمالات أسماء الأعمدة (بما فيها نسخ مُشوّهة RTL)
TITLE_KEYS = ["العنوان", "عنوان", "title", "name"]
LINK_KEYS = ["الرابط", "link", "url"]
IMG_KEYS = ["رابط الصورة", "الصورة", "image", "image_link"]
DESC_KEYS = ["الوصف", "description", "desc"]
SKU_KEYS = ["المعرّف", "sku", "id", "الرمز"]
PRICE_KEYS = ["السعر", "price", "ﺎﻠﺴﻋﺭ"]  # نسخة معكوسة RTL للـ "السعر"
AVAIL_KEYS = ["مدى التوفّر", "التوفر", "التوافر", "availability", "ﻡﺩﻯ ﺎﻠﺗﻮﻓّﺭ"]  # نسخ محتملة

def normalize_price(value: str) -> tuple[str, str]:
    """
    يعيد (price_display, price_numeric) وفق مواصفة Google:
    display: نص للواجهة، numeric: رقم عشري كنص بدون العملة لاستخدامه في JSON-LD/المعالجة.
    """
    s = (value or "").strip()
    # استخرج أرقام وعلامات الفاصلة/النقطة
    num = re.sub(r"[^\d.,]", "", s).replace(",", ".")
    if num.count(".") > 1:
        parts = num.split(".")
        num = "".join(parts[:-1]) + "." + parts[-1]
    if not num:
        num = "0"
    # عرض السعر: أضف KWD إذا لم تكن موجودة بالفعل
    has_kwd = re.search(r"\bkwd\b", s, re.I) or ("د.ك" in s) or ("دينار" in s)
    display = s if s else num
    if not has_kwd:
        display = f"{display} KWD"
    return display, num

def map_availability(value: str) -> tuple[str, str]:
    """
    يحوّل نص التوفّر إلى قيم Google: in_stock / out_of_stock / preorder / backorder
    ويعيد (g_availability, schema_url)
    """
    v = (value or "").strip().lower()
    # أشكال عربية شائعة
    if v in ["متوفر", "متاح", "متوفر الآن", "متوفر بالمخزون"]:
        g = "in_stock"
    elif v in ["غير متوفر", "نفد", "نفد من المخزون", "غير متاح", "غير متوافر"]:
        g = "out_of_stock"
    elif v in ["طلب مسبق", "حجز مسبق", "preorder"]:
        g = "preorder"
    elif v in ["تحت الطلب", "backorder", "طلب بالطلب"]:
        g = "backorder"
    else:
        # افتراضي آمن
        g = "in_stock"
    schema_url = {
        "in_stock": "https://schema.org/InStock",
        "out_of_stock": "https://schema.org/OutOfStock",
        "preorder": "https://schema.org/PreOrder",
        "backorder": "https://schema.org/BackOrder",
    }[g]
    return g, schema_url

def html_escape(s: str) -> str:
    return html.escape(s or "")

def read_csv_products(path: str) -> list[dict]:
    """قراءة كل المنتجات من CSV دون فلترة خاطئة على 'products' ضمن الرابط."""
    items = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

# -------- FEED generation --------
def build_feed(items: list[dict], base_url: str, out_file: Path) -> None:
    """
    ينشئ feed.xml بصيغة RSS 2.0 مع مساحة الأسماء g وفق مواصفات Google Merchant.
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
    lines.append("  <channel>")
    lines.append("    <title>Matjar Kuwait - Products</title>")
    lines.append(f"    <link>{html_escape(base_url)}</link>")
    lines.append("    <description>Latest products from Matjar Kuwait</description>")

    for it in items:
        title = get_first(it, TITLE_KEYS, "منتج")
        link = get_first(it, LINK_KEYS, "")
        img = get_first(it, IMG_KEYS, "")
        desc = get_first(it, DESC_KEYS, "")
        price_raw = get_first(it, PRICE_KEYS, "")
        avail_raw = get_first(it, AVAIL_KEYS, "متوفر")
        sku = get_first(it, SKU_KEYS, "")

        # ابنِ رابط صفحة المنتج داخل الموقع
        slug = slugify(title)
        local_page = f"{base_url.rstrip('/')}/{OUTPUT_DIR}/{slug}.html"

        price_display, price_num = normalize_price(price_raw)
        g_avail, _schema_avail = map_availability(avail_raw)

        lines.append("    <item>")
        lines.append(f"      <g:id>{html_escape(sku or slug.upper())}</g:id>")
        lines.append(f"      <g:title>{html_escape(title)}</g:title>")
        lines.append(f"      <g:description>{html_escape(desc)}</g:description>")
        # رابط صفحة المنتج على موقعك (وليس رابط المصدر الخارجي) حسب توصيات Google
        lines.append(f"      <g:link>{html_escape(local_page)}</g:link>")
        lines.append(f"      <g:image_link>{html_escape(img)}</g:image_link>")
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
    ensure_dir(Path(OUTPUT_DIR))

    rows = read_csv_products(CSV_FILE)

    cards_html = []
    seen_slugs: set[str] = set()
    product_pages_written = 0

    for p in rows:
        title = get_first(p, TITLE_KEYS, "منتج")
        link = get_first(p, LINK_KEYS, "#")
        img = get_first(p, IMG_KEYS, "")
        desc = get_first(p, DESC_KEYS, "")
        sku = get_first(p, SKU_KEYS, "")
        price_raw = get_first(p, PRICE_KEYS, "")

        # slug فريد
        base_slug = slugify(title)
        slug_val = base_slug
        i = 2
        while slug_val in seen_slugs:
            slug_val = f"{base_slug}-{i}"
            i += 1
        seen_slugs.add(slug_val)

        product_rel_path = f"{OUTPUT_DIR}/{slug_val}.html"
        price_display, price_num = normalize_price(price_raw)

        # JSON-LD Product
        g_avail, schema_avail = map_availability(get_first(p, AVAIL_KEYS, "متوفر"))
        product_ld = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": title,
            "image": [img] if img else [],
            "description": desc,
            "sku": sku or slug_val.upper(),
            "offers": {
                "@type": "Offer",
                "url": link or f"{BASE_URL.rstrip('/')}/{product_rel_path}",
                "price": price_num,
                "priceCurrency": "KWD",
                "availability": schema_avail
            }
        }

        # صفحة المنتج
        product_html = PRODUCT_PAGE_TEMPLATE.format(
            name=html_escape(title),
            image=html_escape(img),
            description=html_escape(desc),
            price_display=html_escape(price_display),
            original_url=html_escape(link or "#"),
            jsonld=json.dumps(product_ld, ensure_ascii=False, separators=(",", ":")),
            css=CSS_FILE
        )
        Path(product_rel_path).write_text(product_html, encoding="utf-8")
        product_pages_written += 1

        # بطاقة في الصفحة الرئيسية
        short_desc = (desc[:100] + "...") if len(desc) > 100 else desc
        cards_html.append(CARD_TEMPLATE.format(
            product_page=product_rel_path,
            image=html_escape(img),
            name=html_escape(title),
            short_desc=html_escape(short_desc),
            price=html_escape(price_display)
        ))

    # index.html
    Path("index.html").write_text(
        INDEX_TEMPLATE.format(cards="".join(cards_html), css=CSS_FILE),
        encoding="utf-8"
    )

    # feed.xml
    build_feed(rows, BASE_URL, Path("feed.xml"))

    print(f"تم إنشاء {product_pages_written} صفحة منتج في {OUTPUT_DIR}/ و feed.xml في الجذر.")

if __name__ == "__main__":
    main()
