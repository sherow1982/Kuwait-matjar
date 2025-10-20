const content = document.getElementById('product-content');
const slugify = (text) => text ? text.toString().toLowerCase().trim().replace(/\s+/g, '-').replace(/[^\u0600-\u06FFa-z0-9-]/g, '').replace(/-+/g, '-') : '';
const formatKD = (val) => typeof val === 'number' ? new Intl.NumberFormat('ar-KW', { style: 'currency', currency: 'KWD' }).format(val) : '';
const parsePrice = (priceStr) => priceStr ? parseFloat(String(priceStr).replace(/[^0-9.]/g, '')) : null;

const renderProductDetails = (product) => {
    if (!product) {
        content.innerHTML = '<p>عفواً، هذا المنتج غير موجود.</p>';
        return;
    }

    document.title = product['العنوان'];
    document.querySelector('meta[name="description"]').setAttribute("content", product['الوصف'].substring(0, 160));
    
    const title = product['العنوان'];
    const image = product['رابط الصورة'];
    const description = product['الوصف'].replace(/\n/g, '<br>');
    const originalLink = product['الرابط'];
    
    const salePriceNum = parsePrice(product['السعر المخفّض']);
    const regularPriceNum = parsePrice(product['السعر']);
    const currentPrice = formatKD(salePriceNum || regularPriceNum);
    const oldPrice = salePriceNum ? `<s>${formatKD(regularPriceNum)}</s>` : '';

    const whatsappMessage = encodeURIComponent(`مرحباً\nأريد شراء: ${title} | ${currentPrice}`);
    const whatsappLink = `https://wa.me/201110760081?text=${whatsappMessage}`;

    const schema = {
      "@context": "https://schema.org/", "@type": "Product", "name": title, "image": image,
      "description": product['الوصف'], "sku": product['المعرّف'],
      "offers": { "@type": "Offer", "url": originalLink, "priceCurrency": "KWD", "price": (salePriceNum || regularPriceNum).toFixed(2), "availability": "https://schema.org/InStock" }
    };
    const schemaScript = document.createElement('script');
    schemaScript.type = 'application/ld+json';
    schemaScript.textContent = JSON.stringify(schema);
    document.head.appendChild(schemaScript);

    content.innerHTML = `
        <div class="product-details">
            <div class="product-gallery"><img src="${image}" alt="${title}"></div>
            <div class="product-info">
                <h1>${title}</h1>
                <div class="price">${currentPrice} ${oldPrice}</div>
                <p class="product-description">${description}</p>
                <div class="btn-group">
                    <a href="${originalLink}" target="_blank" rel="noopener noreferrer" class="btn btn-buy">اشترِ الآن من المتجر الأصلي</a>
                    <a href="${whatsappLink}" target="_blank" rel="noopener noreferrer" class="btn btn-whatsapp">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.61 15.36 3.48 16.84L2 22L7.32 20.55C8.75 21.33 10.37 21.82 12.04 21.82C17.5 21.82 21.95 17.37 21.95 11.91C21.95 6.45 17.5 2 12.04 2Z"/></svg>
                        اطلب عبر واتساب
                    </a>
                </div>
            </div>
        </div>
    `;
};

(async () => {
    try {
        const params = new URLSearchParams(window.location.search);
        const productSlug = params.get('name');
        if (!productSlug) throw new Error('رابط المنتج غير صحيح.');
        
        const res = await fetch('https://raw.githubusercontent.com/sherow1982/Kuwait-matjar/refs/heads/main/data/products-template.json?raw=1');
        if (!res.ok) throw new Error('فشل تحميل بيانات المنتجات');
        
        const allProducts = await res.json();
        const product = allProducts.find(p => slugify(p['العنوان']) === productSlug);
        renderProductDetails(product);

    } catch (error) {
        console.error("حدث خطأ:", error);
        content.innerHTML = `<p>حدث خطأ أثناء تحميل تفاصيل المنتج. يرجى المحاولة مرة أخرى.</p>`;
    }
})();
