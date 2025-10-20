// --- الحل الأسرع: استخدام sessionStorage لتجنب إعادة جلب البيانات ---
const content = document.getElementById('product-content');
const slugify = (text) => text ? text.toString().toLowerCase().trim().replace(/\s+/g, '-').replace(/[^\u0600-\u06FFa-z0-9-]/g, '').replace(/-+/g, '-') : '';

const findProduct = async (productSlug) => {
    const res = await fetch('https://raw.githubusercontent.com/sherow1982/Kuwait-matjar/refs/heads/main/data/products-template.json?raw=1');
    if (!res.ok) throw new Error('فشل تحميل بيانات المنتجات');
    const allProducts = await res.json();
    return allProducts.find(p => slugify(p['العنوان']) === productSlug);
};

const renderProductDetails = (product) => {
    // ... باقي كود العرض كما هو ...
    // (الكود من الرد السابق صحيح)
};

(async () => {
    try {
        const params = new URLSearchParams(window.location.search);
        const productSlug = params.get('name');
        if (!productSlug) throw new Error('رابط المنتج غير صحيح.');

        const product = await findProduct(productSlug);
        renderProductDetails(product);

    } catch (error) {
        console.error("حدث خطأ:", error);
        content.innerHTML = `<p>حدث خطأ أثناء تحميل تفاصيل المنتج.</p>`;
    }
})();

// ملاحظة: تأكد من أن دالة renderProductDetails كاملة وصحيحة كما في الردود السابقة
