from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

import time
import pandas as pd
import os

def setup_driver():
    options = Options()
    options.add_argument("--lang=id")
    options.add_argument('accept_language=id-ID,id')
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def get_all_product_links(driver, url):
    driver.get(url)
    time.sleep(5)

    all_links = set()
    wait = WebDriverWait(driver, 10)

    while True:
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        try:
            container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'css-tjjb18')))
            product_anchors = container.find_elements(By.TAG_NAME, 'a')

            for link in product_anchors:
                href = link.get_attribute('href')
                if href:
                    all_links.add(href)
        except Exception as e:
            print("Gagal mengambil link di halaman ini:", e)

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="btnShopProductPageNext"]')
            if next_button.is_displayed():
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
            else:
                break
        except:
            break

    return list(all_links)

def get_product_data(driver, url):
    data = {'Title': None, 'Price': None, 'Description': None, 'Image URL': None, 'Link': url, 'Type': None}
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    time.sleep(2)

    try:
        data['Title'] = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//h1[contains(@data-testid, "lblPDPDetailProductName")]'))).text
    except: pass

    try:
        data['Price'] = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[contains(@data-testid, "lblPDPDetailProductPrice")]'))).text
    except: pass

    try:
        see_more = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="btnPDPSeeMore"]')))
        see_more.click()
        time.sleep(1)
    except TimeoutException:
        pass

    try:
        data['Description'] = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[data-testid="lblPDPDescriptionProduk"]'))).text
    except: pass

    try:
        data['Image URL'] = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'img[data-testid="PDPMainImage"]'))).get_attribute("src")
    except: pass

    try:
        breadcrumb_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//ol[@data-unify="Breadcrumb"]//a')))
        breadcrumbs = [el.text for el in breadcrumb_elements]
        data['Type'] = breadcrumbs
    except: pass

    return data


def extract_all_data(output_folder='raw_data', urls = None):
    os.makedirs(output_folder, exist_ok=True)
    driver = setup_driver()

    for brand, url in urls.items():
        print(f"[🚀] Scraping brand: {brand.upper()}")
        product_links = get_all_product_links(driver, url)
        print(f"[✓] Ditemukan {len(product_links)} produk")

        raw_data = []
        for i, link in enumerate(product_links):
            print(f"[{i+1}] Ambil data dari: {link}")
            data = get_product_data(driver, link)
            data['Brand'] = brand
            raw_data.append(data)
            time.sleep(1)

        # Simpan hasil mentah per brand
        df_raw = pd.DataFrame(raw_data)
        df_raw.to_csv(f"{output_folder}/raw_{brand}.csv", index=False)
        print(f"[💾] Data mentah disimpan di: {output_folder}/raw_{brand}.csv")

    driver.quit()
    print("[✔] Semua brand selesai diproses.")
