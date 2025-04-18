import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import concurrent.futures

# --------------------------
# Config
# --------------------------
BASE_URL = 'https://www.pakwheels.com'
START_URL = 'https://www.pakwheels.com/accessories-spare-parts/search/-/ct_karachi/ct_lahore/ct_rawalpindi/ct_islamabad/'
MAX_PAGES = 3  # Set an integer to limit pages (e.g., 3)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------------------
# Image Downloader
# --------------------------
def download_image(image_url, title):
    try:
        Path("images").mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c if c.isalnum() else "_" for c in title)[:50]
        ext = image_url.split('.')[-1].split('?')[0]
        filename = f"images/{safe_title}.{ext}"

        if image_url != "N/A":
            img_data = requests.get(image_url, headers=HEADERS).content
            with open(filename, 'wb') as f:
                f.write(img_data)
            return filename
        else:
            return "N/A"
    except Exception as e:
        print(f"❌ Failed to download image for '{title}': {e}")
        return "N/A"

# --------------------------
# Product Details Scraper
# --------------------------
def scrape_detail(product_url):
    try:
        detail_res = requests.get(product_url, headers=HEADERS, timeout=10)
        detail_soup = BeautifulSoup(detail_res.content, "html.parser")

        manufacturer_tag = detail_soup.find("h5", class_="nomargin")
        manufacturer = manufacturer_tag.text.strip() if manufacturer_tag else "N/A"

        detail_div = detail_soup.find("div", class_="primary-lang")
        details = detail_div.get_text(separator="\n", strip=True) if detail_div else "N/A"

        return manufacturer, details
    except Exception as e:
        print(f"❌ Error in product details: {e}")
        return "N/A", "N/A"

# --------------------------
# Main Scraper Function
# --------------------------
def get_product_data():
    all_products = []
    page = 1

    while True:
        if MAX_PAGES and page > MAX_PAGES:
            print(f"Reached max page limit: {MAX_PAGES}")
            break

        print(f"🔄 Scraping page {page}...")
        url = START_URL + f"?page={page}"
        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            print(f"⚠️ Failed to load page {page}")
            break

        soup = BeautifulSoup(res.content, "html.parser")
        product_divs = soup.find_all("div", class_="search-title-row")

        if not product_divs:
            print("✅ No more products.")
            break

        page_products = []
        detail_urls = []

        for div in product_divs:
            try:
                title_tag = div.find("h3", style="white-space: normal;")
                title = title_tag.text.strip() if title_tag else "N/A"

                link_tag = div.find("a")
                product_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else "N/A"
                detail_urls.append(product_url)

                price_tag = div.find("div", class_="price-details")
                price = price_tag.text.strip() if price_tag else "N/A"

                img_tag = div.find("img", class_="pic")
                image_url = img_tag.get("src", "N/A") if img_tag else "N/A"
                image_path = download_image(image_url, title)

                page_products.append({
                    "title": title,
                    "url": product_url,
                    "price": price,
                    "image": image_path
                })
            except Exception as e:
                print(f"❌ Listing error: {e}")
                continue

        # 🔄 Parallel fetch product details
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            details = list(executor.map(scrape_detail, detail_urls))

        for i, (manufacturer, detail) in enumerate(details):
            page_products[i]["manufacturer"] = manufacturer
            page_products[i]["details"] = detail

        all_products.extend(page_products)
        page += 1
        time.sleep(0.2)  # prevent hammering

    return pd.DataFrame(all_products)

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    df = get_product_data()
    print(f"✅ Scraped {len(df)} products.")
    
    if not df.empty:
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/pakwheels_products.csv", index=False)
        print("💾 Saved: data/pakwheels_products.csv")
    else:
        print("⚠️ No data scraped.")
