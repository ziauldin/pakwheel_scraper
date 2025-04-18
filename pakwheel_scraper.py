import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE_URL = 'https://www.pakwheels.com'
START_URL = 'https://www.pakwheels.com/accessories-spare-parts/search/-/ct_karachi/'

def get_product_data():
    all_products = []
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1

    while True:
        st.write(f"🔄 Scraping page {page}...")
        url = START_URL + f"?page={page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "html.parser")
        product_divs = soup.find_all("div", class_="search-title-row")

        if not product_divs:
            break

        for div in product_divs:
            try:
                title = div.find("h3", style="white-space: normal;").text.strip()
                link_tag = div.find("a")
                product_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else "N/A"
                price = div.find("div", class_="price-details").text.strip()
                img_tag = div.find("img", class_="lazy pic")
                image_url = img_tag.get("data-original", "N/A") if img_tag else "N/A"

                # Visit product page
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
                st.write(f"Error on page {page}: {e}")
                continue

        page += 1
        time.sleep(1)

    return pd.DataFrame(all_products)

st.title("PakWheels Product Scraper")

st.markdown("""
This tool scrapes product listings from PakWheels Accessories section (Karachi)  
and collects product title, price, image, manufacturer, and details across all pages.
""")

if st.button("Scrape Entire Site"):
    with st.spinner("Scraping all product pages..."):
        df = get_product_data()
        st.success(f"Scraped {len(df)} products.")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "pakwheels_products.csv", "text/csv")
