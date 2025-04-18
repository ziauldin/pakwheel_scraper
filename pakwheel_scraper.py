# pakwheel_scraper.py

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

BASE_URL = 'https://www.pakwheels.com'
START_URL = 'https://www.pakwheels.com/accessories-spare-parts/search/-/ct_karachi/ct_lahore/ct_rawalpindi/ct_islamabad/'

MAX_PAGES = 1  # 👈 Limit scraping to first 3 pages (set to None to scrape all)

def get_product_data():
    all_products = []
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1

    while True:
        if MAX_PAGES and page > MAX_PAGES:
            print(f"Reached max page limit: {MAX_PAGES}")
            break

        print(f"Scraping page {page}...")
        url = START_URL + f"?page={page}"
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            print(f"Failed to fetch page {page}, status: {res.status_code}")
            break

        soup = BeautifulSoup(res.content, "html.parser")
        product_divs = soup.find_all("div", class_="search-title-row")

        if not product_divs:
            print("No more products found.")
            break

        for div in product_divs:
            try:
                title_tag = div.find("h3", style="white-space: normal;")
                title = title_tag.text.strip() if title_tag else "N/A"

                link_tag = div.find("a")
                product_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else "N/A"

                price_tag = div.find("div", class_="price-details")
                price = price_tag.text.strip() if price_tag else "N/A"

                img_tag = div.find("img", class_="lazy pic")
                image_url = img_tag.get("data-original", "N/A") if img_tag else "N/A"

                # Detail page
                detail_res = requests.get(product_url, headers=headers)
                detail_soup = BeautifulSoup(detail_res.content, "html.parser")

                manufacturer_tag = detail_soup.find("h5", class_="nomargin")
                manufacturer = manufacturer_tag.text.strip() if manufacturer_tag else "N/A"

                detail_div = detail_soup.find("div", class_="primary-lang")
                details = detail_div.get_text(separator="\n", strip=True) if detail_div else "N/A"

                all_products.append({
                    "title": title,
                    "url": product_url,
                    "price": price,
                    "image": image_url,
                    "manufacturer": manufacturer,
                    "details": details
                })

            except Exception as e:
                print(f"Error on product: {e}")
                continue

        page += 1
        time.sleep(1)

    return pd.DataFrame(all_products)

# Run and save to CSV
if __name__ == "__main__":
    df = get_product_data()
    print(f"✅ Scraped {len(df)} products in total.")
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/pakwheels_products.csv", index=False)
    print("📁 CSV saved to data/pakwheels_products.csv")
