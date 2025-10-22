import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace
from xml.dom.minidom import parseString

# --- معلومات المتجر الأساسية ---
STORE_TITLE = "Matjar Kuwait - Products"
STORE_LINK = "https://sherow1982.github.io/Kuwait-matjar/"
STORE_DESCRIPTION = "Latest products from Matjar Kuwait"
# -----------------------------

# تسجيل الـ namespace لـ "g" لتجنب ظهور "ns0"
register_namespace('g', 'http://base.google.com/ns/1.0')

# قراءة البيانات من ملف الإكسل
try:
    df = pd.read_excel("products.xlsx")
except FileNotFoundError:
    print("Error: products.xlsx not found!")
    exit()

# إنشاء الهيكل الأساسي لملف XML
rss = Element('rss', {'version': '2.0'})
channel = SubElement(rss, 'channel')
SubElement(channel, 'title').text = STORE_TITLE
SubElement(channel, 'link').text = STORE_LINK
SubElement(channel, 'description').text = STORE_DESCRIPTION

# إضافة كل منتج كعنصر <item>
for _, row in df.iterrows():
    item = SubElement(channel, 'item')
    
    SubElement(item, 'g:id').text = str(row.get('id', ''))
    SubElement(item, 'g:title').text = str(row.get('title', ''))
    SubElement(item, 'g:description').text = str(row.get('description', ''))
    SubElement(item, 'g:link').text = str(row.get('link', ''))
    SubElement(item, 'g:image_link').text = str(row.get('image_link', ''))
    
    # تصحيح قيمة التوفر
    availability = str(row.get('availability', 'in stock')).lower().replace('_', ' ')
    SubElement(item, 'g:availability').text = availability
    
    SubElement(item, 'g:condition').text = 'new'
    SubElement(item, 'g:price').text = str(row.get('price', ''))
    SubElement(item, 'g:brand').text = str(row.get('brand', ''))
    SubElement(item, 'g:identifier_exists').text = 'no'

    # إضافة معلومات الشحن
    shipping = SubElement(item, 'g:shipping')
    SubElement(shipping, 'g:country').text = str(row.get('shipping_country', 'KW'))
    SubElement(shipping, 'g:service').text = str(row.get('shipping_service', 'Standard'))
    SubElement(shipping, 'g:price').text = str(row.get('shipping_price', '0.00 KWD'))

# تحويل الـ XML إلى نص وتنسيقه
xml_str = tostring(rss, 'utf-8')
pretty_xml_str = parseString(xml_str).toprettyxml(indent="  ")

# كتابة الملف النهائي في جذر المستودع
with open("feed.xml", "w", encoding="utf-8") as f:
    f.write(pretty_xml_str)

print("feed.xml has been generated successfully with shipping info.")
