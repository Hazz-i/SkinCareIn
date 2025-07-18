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
    data = {'Title': None, 'Price': None, 'Description': None, 'Image URL': None, 'Link': None, 'Type': None}
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get(url)
        time.sleep(2)
    except Exception as e:
        print(f"[❌] Gagal mengakses URL: {url} - Error: {str(e)}")
        return None

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
    
    try:
        share_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-testid="pdpShareButton"]')))
        share_button.click()
        time.sleep(1)
        
        # Cari semua button dengan kelas mOH6j3FxZNPpiZ6Kl2GyiA==
        buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div.mOH6j3FxZNPpiZ6Kl2GyiA\\=\\=')))
        
        # Pilih button urutan ke-6 (index 5)
        if len(buttons) >= 6:
            sixth_button = buttons[5]
            driver.execute_script("arguments[0].click();", sixth_button)
            time.sleep(2)  # Tunggu setelah klik button pertama
            
            # Cari dan klik element dengan kelas tmwUJHwvgxw6U3MxW1VE1A== di dalamnya
            copy_element = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'div.tmwUJHwvgxw6U3MxW1VE1A\\=\\=')))
            copy_element = copy_element[5]
            copy_element.click()
            time.sleep(2)  # Tunggu sampai button diklik
            
            if copy_element.is_displayed():
                meta_element = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                data['Link'] = meta_element.get_attribute("content")
        else:
            meta_element = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
            data['Link'] = meta_element.get_attribute("content")
    
    except: 
        meta_element = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
        data['Link'] = meta_element.get_attribute("content")
        

    return data


def extract_all_data(output_folder='raw_data', urls = None):
    os.makedirs(output_folder, exist_ok=True)
    driver = setup_driver()

    for brand, url in urls.items():
        print(f"[🚀] Scraping brand: {brand.upper()}")
        product_links = get_all_product_links(driver, url)
        print(f"[✓] Ditemukan {len(product_links)} produk")

        raw_data = []
        successful_scrapes = 0
        failed_scrapes = 0
        
        for i, link in enumerate(product_links):
            print(f"[{i+1}/{len(product_links)}] Ambil data dari: {link}")
            try:
                data = get_product_data(driver, link)
                if data is not None:  # Jika berhasil mengakses link
                    data['Brand'] = brand
                    raw_data.append(data)
                    successful_scrapes += 1
                    print(f"[✓] Berhasil mengambil data produk")
                else:  # Jika gagal mengakses link
                    failed_scrapes += 1
                    print(f"[⚠] Link dilewati karena tidak dapat diakses")
            except Exception as e:
                failed_scrapes += 1
                print(f"[❌] Error saat scraping: {str(e)}")
                print(f"[⚠] Melanjutkan ke link berikutnya...")
                continue
            
            time.sleep(1)
        
        print(f"[📊] Ringkasan: {successful_scrapes} berhasil, {failed_scrapes} gagal dari {len(product_links)} total link")

        # Simpan hasil mentah per brand
        if raw_data:  # Hanya simpan jika ada data yang berhasil di-scrape
            df_raw = pd.DataFrame(raw_data)
            df_raw.to_csv(f"{output_folder}/raw_{brand}.csv", index=False)
            print(f"[💾] Data mentah disimpan di: {output_folder}/raw_{brand}.csv")
        else:
            print(f"[⚠] Tidak ada data yang berhasil di-scrape untuk brand {brand}")

    driver.quit()
    print("[✔] Semua brand selesai diproses.")
