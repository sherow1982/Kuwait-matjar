import os
import re
import json
import html
from pathlib import Path

import pandas as pd
from slugify import slugify

# -------- CONFIG --------
EXCEL_FILE = "products-template.xlsx"   # اسم الملف في الجذر
OUTPUT_DIR = "."                        # مجلد الإخراج
CSS_FILE = "style.css"                  # اسم ملف الستايل الناتج

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
<header class="header">
  <div class="header__inner container">
    <div class="header__logo">المتجر الكويتي</div>
    <div class="header__spacer"></div>
    <nav class="nav">
      <a href="./" class="nav__link">الرئيسية</a>
      <a href="./" class="nav__link">العروض</a>
      <a href="./" class="nav__link">الفئات</a>
    </nav>
  </div>
</header>

<main class="container section">
  <div class="title-line">
    <h1 class="h2">منتجات مميزة</h1>
  </div>
  <div class="products">
{cards}
  </div>
</main>

<footer class="footer">
  <div class="container footer__top">
    <div class="footer__cols">
      <div><h3 class="h3">عن المتجر</h3><p class="lead">تجربة تسوق بسيطة وسريعة.</p></div>
      <div><h3 class="h3">روابط</h3><p><a href="./">الرئيسية</a></p></div>
      <div><h3 class="h3">سياسات</h3><p><a href="./">الخصوصية</a></p></div>
      <div><h3 class="h3">تواصل</h3><p><a href="mailto:info@example.com">info@example.com</a></p></div>
    </div>
  </div>
  <div class="container footer__bottom">
    <p>© 2025 المتجر الكويتي</p>
  </div>
</footer>
</body>
</html>
'''

CARD_TEMPLATE = '''    <a class="product product--hover-buttons" href="{product_page}" aria-label="{name}">
      <div class="product__media">
        <img src="{image}" alt="{name}" loading="lazy" decoding="async">
        {badge}
        <div class="product__hover">
          <button class="btn btn--ghost" type="button">عرض سريع</button>
          <button class="btn" type="button">أضف للسلة</button>
        </div>
      </div>
      <div class="product__body">
        <h2 class="product__title">{name}</h2>
        <div class="price">{price_html}</div>
      </div>
    </a>
'''

PRODUCT_TEMPLATE = '''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<meta name="description" content="{meta_description}">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{meta_description}">
<meta property="og:type" content="product">
<meta property="og:image" content="{image}">
<link rel="stylesheet" href="{css}">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
<header class="header">
  <div class="header__inner container">
    <div class="header__logo">المتجر الكويتي</div>
    <div class="header__spacer"></div>
    <nav class="nav">
      <a class="nav__link" href="./">الرئيسية</a>
    </nav>
  </div>
</header>

<main class="container section">
  <nav class="breadcrumbs mb-2"><a href="./">الرئيسية</a><span>/</span><span>{name}</span></nav>
  <div class="modal is-open" style="display:none" aria-hidden="true"></div>
  <div class="card" style="padding:1rem">
    <div class="row" style="align-items:flex-start">
      <div class="col" style="flex:0 0 420px;max-width:420px">
        <img src="{image}" alt="{name}" style="max-width:420px;width:100%" loading="eager" decoding="async">
      </div>
      <div class="col">
        <h1 class="h1">{name}</h1>
        <p class="price" style="font-size:1.25rem">{price_html}</p>
        <p>{safe_description}</p>
        <p><a class="btn btn--lg" href="{url}" target="_blank" rel="nofollow noopener">اشترِ الآن</a></p>
      </div>
    </div>
  </div>
</main>

<footer class="footer">
  <div class="container footer__bottom">
    <p>© 2025 المتجر الكويتي</p>
  </div>
</footer>
</body>
</html>
'''

# -------- CSS (WoodMart-like lite) --------
CSS_CONTENT = """:root{--container:1200px;--gutter:1rem;--bg:#f8f8f8;--card:#fff;--accent:#3aa77a;--text:#1f1f1f;--muted:#6b7280;--line:rgba(0,0,0,.08);--shadow:0 6px 18px rgba(0,0,0,.06)}
*{box-sizing:border-box}
html[dir="rtl"] body{direction:rtl}
body{margin:0;font-family:system-ui,-apple-system,'Segoe UI','Noto Sans Arabic',sans-serif;color:var(--text);background:var(--bg);line-height:1.6}
a{text-decoration:none;color:inherit}
.container{max-width:var(--container);margin-inline:auto;padding-inline:var(--gutter)}
.section{padding-block:2rem}
.h1,h1{font-size:clamp(1.6rem,2.5vw,2.2rem);margin:0 0 .75rem}
.h2,h2{font-size:clamp(1.3rem,2vw,1.6rem);margin:0 0 .75rem}
.h3,h3{font-size:1.05rem;margin:0 0 .5rem}
.lead{color:var(--muted)}
.header{position:sticky;top:0;z-index:1000;background:#fff;border-bottom:1px solid var(--line)}
.header__inner{display:flex;align-items:center;gap:.75rem;padding:.9rem var(--gutter)}
.header__logo{font-weight:800}
.header__spacer{flex:1}
.nav{display:flex;gap:.25rem}
.nav__link{padding:.55rem .85rem;border-radius:10px}
.nav__link:hover{background:#f6f7f9}
.title-line{display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem}
.products{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}
@media(max-width:1200px){.products{grid-template-columns:repeat(3,1fr)}}
@media(max-width:900px){.products{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.products{grid-template-columns:1fr}}
.product{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease}
.product:hover{transform:translateY(-2px);box-shadow:var(--shadow);border-color:transparent}
.product__media{position:relative;aspect-ratio:1/1;background:#eee;display:grid;place-items:center;overflow:hidden}
.product__media img{width:100%;height:100%;object-fit:cover;transition:transform .3s ease}
.product:hover .product__media img{transform:scale(1.03)}
.product__hover{position:absolute;inset-inline:.75rem;inset-block-end:.75rem;display:flex;gap:.5rem;opacity:0;transform:translateY(6px);transition:.2s ease}
.product:hover .product__hover{opacity:1;transform:translateY(0)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:.4rem;padding:.6rem .9rem;border-radius:10px;border:none;color:#fff;background:var(--accent);font-weight:700}
.btn--ghost{background:rgba(0,0,0,.7);color:#fff}
.product__body{padding:.8rem}
.product__title{margin:0 0 .35rem;font-size:.98rem}
.price{display:inline-flex;align-items:baseline;gap:.4rem;font-weight:800}
.price s{color:var(--muted);font-weight:500}
.breadcrumbs{display:flex;align-items:center;gap:.4rem;color:var(--muted);font-size:.92rem}
.footer{background:#fff;border-top:1px solid var(--line);margin-top:2rem}
.footer__top{padding:2rem 0}
.footer__cols{display:grid;gap:1rem;grid-template-columns:repeat(4,minmax(0,1fr))}
@media(max-width:900px){.footer__cols{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.footer__cols{grid-template-columns:1fr}}
.footer__bottom{padding:.9rem 0;color:#6b7280}
.product__badge{position:absolute;inset-block-start:.75rem;inset-inline-start:.75rem;background:#ef4444;color:#fff;border-radius:8px;padding:.2rem .5rem;font-size:.78rem;font-weight:800}
html[dir="rtl"] .product__badge{inset-inline-start:auto;inset-inline-end:.75rem}
"""

# -------- Helpers --------
def coerce_str(val: object, fallback: str = "") -> str:
    if pd.isna(val):
        return fallback
    s = str(val).strip()
    return s if s else fallback

def normalize_price(price_raw: str) -> tuple[str, str]:
    """
    Returns (price_display_html, price_numeric_for_jsonld)
    Accepts inputs like: "12.50", "12,50", "12 د.ك", "KWD 12"
    """
    s = price_raw.strip()
    # Build numeric value for JSON-LD
    num = re.sub(r"[^\d.,]", "", s).replace(",", ".")
    if num.count(".") > 1:
        # Keep last dot as decimal separator
        parts = num.split(".")
        num = "".join(parts[:-1]) + "." + parts[-1]
    num = num if num else "0"
    # Build HTML view: keep original plus strike-through optional if matched
    price_html = html.escape(s)
    return price_html, num

def unique_slug(base: str, seen: dict[str, int]) -> str:
    slug = slugify(base) or "product"
    if slug not in seen:
        seen[slug] = 1
        return slug
    seen[slug] += 1
    return f"{slug}-{seen[slug]}"

# -------- MAIN --------
def main():
    # Ensure output directory exists
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Load Excel
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    df = df.fillna("")

    # Write CSS
    with open(Path(OUTPUT_DIR) / CSS_FILE, "w", encoding="utf-8") as f:
        f.write(CSS_CONTENT)

    cards_html = []
    seen_slugs: dict[str, int] = {}

    for _, row in df.iterrows():
        name = coerce_str(row.get("العنوان", "منتج"), "منتج")
        url = coerce_str(row.get("الرابط", "#"), "#")
        price_in = coerce_str(row.get("السعر", "غير متوفر"), "غير متوفر")
        description = coerce_str(row.get("الوصف", ""), "")
        image = coerce_str(row.get("رابط الصورة", ""), "")

        # Slug
        slug = unique_slug(name, seen_slugs)
        product_file = f"{slug}.html"

        # Price normalize
        price_html, price_num = normalize_price(price_in)

        # JSON-LD
        product_ld = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": name,
            "image": [image] if image else [],
            "description": description,
            "offers": {
                "@type": "Offer",
                "url": url,
                "priceCurrency": "KWD",
                "price": price_num,
                "availability": "https://schema.org/InStock"
            }
        }
        jsonld = json.dumps(product_ld, ensure_ascii=False, separators=(",", ":"))

        # Secure text in HTML
        safe_name = html.escape(name)
        safe_description = html.escape(description)
        meta_description = (description or name)[:160].replace("\n", " ")
        meta_description = html.escape(meta_description)

        # Badge if discount-like text found
        has_sale = bool(re.search(r"(خصم|تخفيض|sale|%|-)", price_in, flags=re.I))
        badge = f'<span class="product__badge">عرض</span>' if has_sale else ""

        # Write product page
        with open(Path(OUTPUT_DIR) / product_file, "w", encoding="utf-8") as f:
            f.write(PRODUCT_TEMPLATE.format(
                name=safe_name,
                meta_description=meta_description,
                safe_description=safe_description,
                price_html=price_html,
                image=image,
                url=url,
                css=CSS_FILE,
                jsonld=jsonld
            ))

        # Card for index
        cards_html.append(CARD_TEMPLATE.format(
            product_page=product_file,
            image=image,
            name=safe_name,
            price_html=price_html,
            badge=badge
        ))

    # Write index.html
    with open(Path(OUTPUT_DIR) / "index.html", "w", encoding="utf-8") as f:
        f.write(INDEX_TEMPLATE.format(cards="\n".join(cards_html), css=CSS_FILE))

    print(f"Generated {len(df)} products.")

if __name__ == "__main__":
    main()
