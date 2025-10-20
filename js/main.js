const DATA_URL = 'https://raw.githubusercontent.com/sherow1982/Kuwait-matjar/refs/heads/main/data/products-template.json?raw=1';
const container = document.getElementById('products-container');

/**
 * دالة محسّنة لإنشاء روابط صديقة لمحركات البحث (slug) تدعم اللغة العربية بشكل كامل.
 * @param {string} text - النص المراد تحويله (اسم المنتج).
 * @returns {string} - النص المحوّل إلى رابط.
 */
const slugify = (text) => {
  if (!text) return '';
  return text.toString().toLowerCase().trim()
    .replace(/\s+/g, '-')           // استبدال المسافات بـ -
    .replace(/[^\u0600-\u06FFa-z0-9-]/g, '') // إزالة جميع الأحرف الخاصة ما عدا العربية والإنجليزية والأرقام والشرطات
    .replace(/-+/g, '-');            // استبدال الشرطات المتعددة بشرطة واحدة
};

const formatKD = (val) => typeof val === 'number' ? new Intl.NumberFormat('ar-KW', { style: 'currency', currency: 'KWD' }).format(val) : '';
const parsePrice = (priceStr) => priceStr ? parseFloat(String(priceStr).replace(/[^0-9.]/g, '')) : null;

const createProductCard = (p = {}) => {
    const title = p['العنوان'] || 'منتج غير متوفر';
    const image = p['رابط الصورة'] || './placeholder.webp';
    const productSlug = slugify(title); // سيتم استخدام الدالة الجديدة هنا
    const productPageLink = `./product.html?name=${productSlug}`;
    
    const salePriceNum = parsePrice(p['السعر المخفّض']);
    const regularPriceNum = parsePrice(p['السعر']);
    
    const currentPriceHTML = formatKD(salePriceNum || regularPriceNum);
    const oldPriceHTML = salePriceNum ? `<s>${formatKD(regularPriceNum)}</s>` : '';
    
    let saleBadge = '';
    if (salePriceNum && regularPriceNum && regularPriceNum > salePriceNum) {
        const discount = Math.round(((regularPriceNum - salePriceNum) / regularPriceNum) * 100);
        saleBadge = `<span class="product__badge">-${discount}%</span>`;
    }

    return `
        <div class="product">
            <a href="${productPageLink}" target="_blank" rel="noopener noreferrer" class="product__media">
                ${saleBadge}
                <img src="${image}" alt="${title}" loading="lazy" decoding="async" onerror="this.onerror=null;this.src='./placeholder.webp';">
            </a>
            <div class="product__body">
                <div class="product__title"><h3><a href="${productPageLink}" target="_blank" rel="noopener noreferrer">${title}</a></h3></div>
                <div class="price">${oldPriceHTML}<span>${currentPriceHTML}</span></div>
            </div>
        </div>
    `;
};

const renderProducts = (items) => {
    const productsGrid = document.createElement('div');
    productsGrid.className = 'products';
    if (items?.length) {
        productsGrid.innerHTML = items.map(createProductCard).join('');
    } else {
        productsGrid.innerHTML = '<p>عفواً، لم يتم العثور على منتجات حالياً.</p>';
    }
    container.appendChild(productsGrid);
};

(async () => {
    if (container) {
        try {
            const res = await fetch(DATA_URL);
            if (!res.ok) throw new Error('فشل تحميل المنتجات');
            const items = await res.json();
            renderProducts(items);
        } catch (error) {
            console.error(error);
            container.innerHTML = '<h2>أحدث المنتجات</h2><p>حدث خطأ أثناء تحميل المنتجات.</p>';
        }
    }
})();
