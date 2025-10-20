const DATA_URL = 'https://raw.githubusercontent.com/sherow1982/Kuwait-matjar/refs/heads/main/data/products-template.json?raw=1';
const searchInput = document.getElementById('searchInput');
const searchSuggestions = document.getElementById('searchSuggestions');
let productsCache = [];

const slugify = (text) => text ? text.toString().toLowerCase().trim().replace(/\s+/g, '-').replace(/[^\u0600-\u06FFa-z0-9-]/g, '').replace(/-+/g, '-') : '';

// جلب المنتجات مرة واحدة وتخزينها مؤقتًا
const fetchProducts = async () => {
    if (productsCache.length > 0) {
        return productsCache;
    }
    try {
        const res = await fetch(DATA_URL);
        if (!res.ok) throw new Error('فشل تحميل بيانات المنتجات للبحث');
        productsCache = await res.json();
        return productsCache;
    } catch (error) {
        console.error("خطأ في جلب منتجات البحث:", error);
        return [];
    }
};

const handleSearch = async (event) => {
    const query = event.target.value.trim().toLowerCase();
    
    if (!query) {
        searchSuggestions.classList.remove('visible');
        return;
    }

    const products = await fetchProducts();
    const matchingProducts = products.filter(p => p['العنوان'].toLowerCase().includes(query));

    if (matchingProducts.length > 0) {
        searchSuggestions.innerHTML = matchingProducts.slice(0, 5).map(p => {
            const productSlug = slugify(p['العنوان']);
            return `<a href="./product.html?name=${productSlug}" target="_blank" rel="noopener noreferrer" class="search-suggestion-item">${p['العنوان']}</a>`;
        }).join('');
    } else {
        searchSuggestions.innerHTML = `<div class="search-suggestion-item no-results">لا توجد منتجات مطابقة.</div>`;
    }

    searchSuggestions.classList.add('visible');
};

const setupSearch = () => {
    if (!searchInput || !searchSuggestions) return;

    searchInput.addEventListener('input', handleSearch);
    
    // إخفاء الاقتراحات عند الضغط خارج المربع
    document.addEventListener('click', (event) => {
        if (!searchInput.contains(event.target)) {
            searchSuggestions.classList.remove('visible');
        }
    });

    // جلب البيانات مسبقًا لتحسين الأداء عند أول بحث
    fetchProducts();
};

setupSearch();
