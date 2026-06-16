
import re
import time
import unicodedata
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from tests.testFilter.constants import *

SPECIAL_MAP = {'đ': 'd', 'Đ': 'd'}

def vi_sort_key(text: str) -> str:

    text = str(text).lower().strip()
    text = ''.join(SPECIAL_MAP.get(c, c) for c in text)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return text

def is_sorted_vi(data: list[str], reverse: bool = False) -> bool:
    keys = [vi_sort_key(name.split()[0]) for name in data]
    for i in range(len(keys) - 1):
        if not reverse and keys[i] > keys[i + 1]:
            print(f"  [FAIL tại] '{data[i]}' đứng trước '{data[i+1]}'")
            return False
        if reverse and keys[i] < keys[i + 1]:
            print(f"  [FAIL tại] '{data[i]}' đứng trước '{data[i+1]}'")
            return False
    return True
def open_website() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(URL)

    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_LIST_CSS))
    )
    return driver

def get_sort_dropdown(driver: webdriver.Chrome) -> Select:
    el = WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SORT_DROPDOWN_CSS))
    )
    return Select(el)

def select_sort_option(driver: webdriver.Chrome, select_obj: Select, index: int) -> str:
    option = select_obj.options[index]
    option_text = option.text.strip()
    select_obj.select_by_index(index)
    return option_text

def get_first_item_text(driver: webdriver.Chrome, is_price_sort: bool) -> str:
    css = PRICE_SPAN_CSS if is_price_sort else NAME_TEXT_CSS
    els = driver.find_elements(By.CSS_SELECTOR, css)
    return els[0].text.strip() if els else ""

def wait_for_sort_completed(driver: webdriver.Chrome, prev_text: str, is_price_sort: bool) -> None:

    wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT, poll_frequency=0.4,
                         ignored_exceptions=[StaleElementReferenceException])
    try:
        wait.until(lambda d: get_first_item_text(d, is_price_sort) != prev_text)
    except TimeoutException:
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_LIST_CSS))
        )

def _parse_price_from_text(raw: str, category: str) -> int | None:
    raw = raw.strip()
    if not raw:
        return None

    if "~" in raw:
        parts = raw.split("~")
        if len(parts) != 2:
            return None
        target = parts[1].strip() if category == "price_desc" else parts[0].strip()
    else:
        target = raw

    cleaned = re.sub(r"[^\d]", "", target)
    return int(cleaned) if cleaned.isdigit() else None

def get_prices(driver: webdriver.Chrome, category: str) -> list[int]:
    prices = []
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_BLOCK_CSS))
    )
    product_blocks = driver.find_elements(By.CSS_SELECTOR, PRODUCT_BLOCK_CSS)
    
    for block in product_blocks:
        if block.is_displayed():
            try:
                price_el = block.find_element(By.CSS_SELECTOR, PRICE_SPAN_CSS)
                text = price_el.text.strip()
                if not any(char.isdigit() for char in text):
                    continue
                numeric_price = _parse_price_from_text(text, category)
                if numeric_price is not None:
                    prices.append(numeric_price)
            except NoSuchElementException:
                continue
    #print("gia san pham",prices)
    return prices

def get_names(driver: webdriver.Chrome) -> list[str]:
    names = []
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_BLOCK_CSS))
    )
    product_blocks = driver.find_elements(By.CSS_SELECTOR, PRODUCT_BLOCK_CSS)

    for block in product_blocks:
        if block.is_displayed():
            try:
                name_el = block.find_element(By.CSS_SELECTOR, NAME_TEXT_CSS)
                raw = name_el.text.strip()
                normalized = unicodedata.normalize('NFC', raw.lower())
                names.append(normalized)
            except NoSuchElementException:
                continue
    return names

def classify_option(option_text: str, option_value: str) -> str:
    val = str(option_value).strip().lower()
    
    if val == PRICE_ASC_VALUE:  return "price_asc"
    if val == PRICE_DESC_VALUE: return "price_desc"
    if val == NAME_ASC_VALUE:   return "name_asc"
    if val == NAME_DESC_VALUE:  return "name_desc"
    
    return "skip"

def run_test(category: str, data: list) -> str:
    if not data:
        return "FAIL (không có dữ liệu)"
    
    if category == "price_asc": 
        expected = sorted(data)
        if data != expected:
            print(f"\n[DEBUG price_asc] Thực tế: {data[:5]}... \n[DEBUG price_asc] Mong đợi: {expected[:5]}...")
        return "PASS" if data == expected else "FAIL"
        
    if category == "price_desc": 
        expected = sorted(data, reverse=True)
        if data != expected:
            print(f"\n[DEBUG price_desc] Thực tế: {data[:5]}... \n[DEBUG price_desc] Mong đợi: {expected[:5]}...")
        return "PASS" if data == expected else "FAIL"
        
    if category == "name_asc": return "PASS" if is_sorted_vi(data, reverse=False) else "FAIL"
    if category == "name_desc": return "PASS" if is_sorted_vi(data, reverse=True) else "FAIL"
    
