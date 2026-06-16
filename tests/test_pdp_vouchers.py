import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

def test_pdp_open_voucher_popup(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    
    try:
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn, .coupon_item")))
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", voucher_btn)
        driver.execute_script("arguments[0].style.border = '3px solid red';", voucher_btn)
        time.sleep(1.5)
        
        driver.execute_script("arguments[0].click();", voucher_btn)
        
        popup_panel = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.cart-coupon")))
        
        assert "active" in popup_panel.get_attribute("class"), "Popup không có trạng thái active khi mở!"
        
    except Exception as e:
        pytest.fail(f"Lỗi khi tương tác với nút Voucher: {e}")

def test_pdp_close_voucher_via_overlay(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    
    try:
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn")))
        driver.execute_script("arguments[0].click();", voucher_btn)
        
        popup_panel = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.cart-coupon")))
        time.sleep(1) 
        
        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cart-coupon-overlay")))
        
        driver.execute_script("arguments[0].click();", overlay)
        time.sleep(1) 
        
        is_active = "active" in popup_panel.get_attribute("class")
        assert not is_active, "Click vào overlay nhưng bảng voucher không đóng"
        
    except Exception as e:
        pytest.fail(f"Lỗi khi test đóng voucher: {e}")

def test_pdp_verify_voucher_content(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    
    try:
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn")))
        driver.execute_script("arguments[0].click();", voucher_btn)
        time.sleep(1.5)
        
        coupons_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.section_coupons")))
        
        inner_html = coupons_container.get_attribute("innerHTML")
        
        assert len(inner_html.strip()) > 50, "bảng vocher có mà không có voucher"
        
    except Exception as e:
        pytest.fail(f"Lỗi khi kiểm tra nội dung voucher: {e}")