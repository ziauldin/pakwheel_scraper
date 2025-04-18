import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = 'https://www.pakwheels.com'
START_URL = 'https://www.pakwheels.com/accessories-spare-parts/search/-/ct_karachi/ct_lahore/ct_rawalpindi/ct_islamabad/'
MAX_PAGES = None  # Set to None for all pages, or an integer like 3
RESTART_BROWSER_EVERY = 100

def create_driver():
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver = create_driver()
driver.maximize_window()

def get_all_product_links():
    global driver
    current_page = 1
    all_products = []

    while True:
        if MAX_PAGES and current_page > MAX_PAGES:
            print("Reached max page limit.")
            break

        print(f"Scraping page {current_page}...")
        paginated_url = START_URL + f'?page={current_page}'

        try:
            driver.get(paginated_url)
        except Exception as e:
            print(f"Timeout or error on page {current_page}: {e}")
            current_page += 1
            continue

        time.sleep(random.uniform(2, 4))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_divs = soup.find_all('div', class_='search-title-row')

        if not product_divs:
            print("No more products found.")
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

                print(f"Added: {title}")

            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

        current_page += 1

        if RESTART_BROWSER_EVERY and current_page % RESTART_BROWSER_EVERY == 0:
            print("Restarting browser to free memory...")
            driver.quit()
            driver = create_driver()
            driver.maximize_window()

    return all_products

def scrape_product_detail(url):
    try:
        driver.get(url)
        time.sleep(random.uniform(1.5, 3))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        detail_div = soup.find('div', class_='primary-lang')
        product_details = detail_div.get_text(separator='\n', strip=True) if detail_div else 'N/A'

        manufacturer_tag = soup.find('h5', class_='nomargin')
        manufacturer = manufacturer_tag.text.strip() if manufacturer_tag else 'N/A'

        return product_details, manufacturer
    except Exception as e:
        print(f"Failed to scrape detail from {url}: {e}")
        return 'N/A', 'N/A'

def main():
    all_products = get_all_product_links()
    print(f"Total products found: {len(all_products)}")

    for idx, product in enumerate(all_products):
        print(f"Scraping detail ({idx+1}/{len(all_products)}): {product['title']}")
        details, manufacturer = scrape_product_detail(product['url'])
        product['details'] = details
        product['manufacturer'] = manufacturer

    driver.quit()

    df = pd.DataFrame(all_products)
    df.to_csv('pakwheels_products.csv', index=False)
    print("Saved as pakwheels_products.csv")
    print("Data Preview:")
    print(df.head())

if __name__ == "__main__":
    main()