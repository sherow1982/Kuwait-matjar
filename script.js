// Project sitemap candidates (GitHub Pages)
const SITEMAP_CANDIDATES = [
  "https://sherow1982.github.io/Kuwait-matjar/sitemap-products.xml",
  "https://sherow1982.github.io/Kuwait-matjar/sitemap.xml"
];

const productsContainer = document.getElementById("products-container");

// IndexNow settings (batch submit)
// Docs: https://www.indexnow.org/documentation
const INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow";
const HOST = "sherow1982.github.io";
// Replace with your real key string (also add a file named <key>.txt containing the key at KEY_LOCATION below)
const INDEXNOW_KEY = "REPLACE_WITH_YOUR_INDEXNOW_KEY";
// Option 2: key file lives under the same host within the project path; URLs must start with that path
const KEY_LOCATION = `https://${HOST}/Kuwait-matjar/${INDEXNOW_KEY}.txt`;

// Fetch the first available sitemap text
async function fetchFirstAvailable(urls) {
  for (const url of urls) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) return await res.text();
    } catch (_) {
      // try next
    }
  }
  throw new Error("No sitemap available");
}

// Parse <loc> from XML sitemap (namespace-agnostic)
function parseSitemap(xmlText) {
  const parser = new DOMParser();
  const xml = parser.parseFromString(xmlText, "application/xml");
  const locEls = Array.from(xml.getElementsByTagNameNS("*", "loc"));
  const urls = locEls
    .map((el) => (el.textContent || "").trim())
    .filter(
      (u) =>
        u.startsWith("https://sherow1982.github.io/Kuwait-matjar/products/") &&
        u.endsWith(".html")
    );
  return Array.from(new Set(urls));
}

// Fetch a product page and extract basic data (title, image, price)
async function fetchProductData(url) {
  const res = await fetch(url, { cache: "no-store" });
  const htmlText = await res.text();
  const doc = new DOMParser().parseFromString(htmlText, "text/html");

  const title =
    (doc.querySelector("h1")?.textContent || doc.title || "منتج").trim();
  const img =
    doc.querySelector("main img, img")?.getAttribute("src") ||
    "https://via.placeholder.com/300x300?text=No+Image";

  // Prefer JSON-LD Product for price
  let priceText = "";
  const jsonLdNode = Array.from(
    doc.querySelectorAll('script[type="application/ld+json"]')
  )
    .map((s) => {
      try {
        return JSON.parse(s.textContent || "{}");
      } catch {
        return null;
      }
    })
    .find(
      (o) =>
        o &&
        (o["@type"] === "Product" ||
          (Array.isArray(o["@type"]) && o["@type"].includes("Product")))
    );

  if (jsonLdNode && jsonLdNode.offers) {
    const p = jsonLdNode.offers.price ?? "";
    const c = jsonLdNode.offers.priceCurrency ?? "";
    priceText = [p, c].filter(Boolean).join(" ");
  } else {
    // Fallback: a visible price element
    priceText =
      doc.querySelector("p strong, .price .current")?.textContent?.trim() || "";
  }

  return { url, title, img, priceText };
}

// Render a product card into the container
function renderCard({ url, title, img, priceText }) {
  if (!productsContainer) return;
  const card = document.createElement("article");
  card.className = "product";
  card.innerHTML = `
    <img src="${img}" alt="${title}" loading="lazy" decoding="async">
    <h3>${title}</h3>
    ${priceText ? `<p>${priceText}</p>` : `<p></p>`}
    <a href="${url}" target="_blank" rel="noopener">عرض المنتج</a>
  `;
  productsContainer.appendChild(card);
}

// Submit URLs to IndexNow in one batch (silent failure if key is missing)
async function submitIndexNow(urls) {
  if (!INDEXNOW_KEY || INDEXNOW_KEY === "REPLACE_WITH_YOUR_INDEXNOW_KEY") return;
  const payload = {
    host: HOST,
    key: INDEXNOW_KEY,
    keyLocation: KEY_LOCATION,
    urlList: urls
  };
  try {
    await fetch(INDEXNOW_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload)
    });
  } catch (_) {
    // ignore client-side delivery issues
  }
}

async function main() {
  if (!productsContainer) return;
  productsContainer.textContent = "جاري التحميل...";
  try {
    const xmlText = await fetchFirstAvailable(SITEMAP_CANDIDATES);
    const urls = parseSitemap(xmlText).slice(0, 24); // limit to first 24 cards
    productsContainer.textContent = "";

    const results = await Promise.allSettled(urls.map(fetchProductData));
    const items = results
      .filter((r) => r.status === "fulfilled")
      .map((r) => r.value);

    items.forEach(renderCard);

    if (items.length) {
      // Submit all displayed URLs in a single IndexNow request
      await submitIndexNow(items.map((i) => i.url));
    }
  } catch (err) {
    console.error("Sitemap/products loading error:", err);
    productsContainer.innerHTML = "<p>حدث خطأ أثناء تحميل المنتجات.</p>";
  }
}

main();
