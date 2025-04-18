# streamlit_app.py
import streamlit as st
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = 'https://www.pakwheels.com'
START_URL = 'https://www.pakwheels.com/accessories-spare-parts/search/-/ct_karachi/ct_lahore/ct_rawalpindi/ct_islamabad/'
MAX_PAGES = 1  # Keep small for demo

@st.cache_data(show_spinner=False)
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_product_links(driver, max_pages=1):
    current_page = 1
    all_products = []

    while True:
        if max_pages and current_page > max_pages:
            break

        paginated_url = START_URL + f'?page={current_page}'
        try:
            driver.get(paginated_url)
        except:
            current_page += 1
            continue

        time.sleep(random.uniform(1.5, 2.5))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_divs = soup.find_all('div', class_='search-title-row')

        if not product_divs:
            break

        for div in product_divs:
            try:
                title_tag = div.find('h3', style="white-space: normal;")
                title = title_tag.text.strip() if title_tag else 'N/A'
                link_tag = div.find('a')
                product_link = urljoin(BASE_URL, link_tag['href']) if link_tag else 'N/A'
                price_div = div.find('div', class_='price-details')
                price = price_div.get_text(strip=True) if price_div else 'N/A'
                img_tag = div.find('img', class_='lazy pic')
                image_url = img_tag['data-original'] if img_tag and 'data-original' in img_tag.attrs else 'N/A'

                all_products.append({
                    'title': title,
                    'url': product_link,
                    'price': price,
                    'image': image_url
                })

            except:
                continue

        current_page += 1

    return all_products

def get_product_details(driver, url):
    try:
        driver.get(url)
        time.sleep(random.uniform(1, 2))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        detail_div = soup.find('div', class_='primary-lang')
        product_details = detail_div.get_text(separator='\n', strip=True) if detail_div else 'N/A'
        manufacturer_tag = soup.find('h5', class_='nomargin')
        manufacturer = manufacturer_tag.text.strip() if manufacturer_tag else 'N/A'
        return product_details, manufacturer
    except:
        return 'N/A', 'N/A'

st.title("PakWheels Product Scraper")

if st.button("Scrape Now"):
    with st.spinner("Scraping in progress..."):
        driver = create_driver()
        products = get_product_links(driver, MAX_PAGES)

        for product in products:
            details, manufacturer = get_product_details(driver, product['url'])
            product['details'] = details
            product['manufacturer'] = manufacturer

        driver.quit()
        df = pd.DataFrame(products)
        st.success("Scraping complete!")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "pakwheels_products.csv", "text/csv")

