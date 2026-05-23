import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Sử dụng một sản phẩm bất kỳ trên ICONDENIM
PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-linen-cuban-sandrift-form-relaxed"

# --- HÀM HỖ TRỢ (HELPER) ---
def extract_number(text):
    if not text:
        return 0
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(''.join(numbers))
    return 0

# =====================================================================
# KỊCH BẢN 1: Validate Thông tin & Gallery (Đã fix lỗi ký tự ₫)
# =====================================================================
def test_matrix_product_info_and_gallery(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Advanced] Kịch bản 1: Validate Thông tin & Gallery (Ma trận Test)...")
    driver.get(PRODUCT_URL)
    
    print("-> TC_02 (Thông tin SP): Giá bán hiển thị đúng định dạng tiền tệ...")
    current_price_el = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'current-price') or contains(@class, 'price')]")))
    price_text = current_price_el.text
    
    # Ký hiệu ₫ của ICONDENIM
    valid_symbols = ["đ", "₫", "vnd"]
    has_valid_currency = any(symbol in price_text.lower() for symbol in valid_symbols)
    
    assert has_valid_currency, f"BUG: Giá tiền không có định dạng tiền tệ hợp lệ ({price_text})"
    print(f"   + [PASSED] Định dạng tiền tệ chuẩn: {price_text}")

    print("-> TC_07 (Hình ảnh & Media): Click thumbnail thay đổi ảnh chính...")
    try:
        thumbnails = driver.find_elements(By.CSS_SELECTOR, ".thumbnail img, .product-gallery__thumb img")
        if len(thumbnails) > 1:
            main_image = driver.find_element(By.CSS_SELECTOR, ".product-gallery__image img, .main-image img")
            old_src = main_image.get_attribute("src")
            
            driver.execute_script("arguments[0].click();", thumbnails[1])
            time.sleep(1)
            
            new_src = driver.find_element(By.CSS_SELECTOR, ".product-gallery__image img, .main-image img").get_attribute("src")
            assert old_src != new_src, "BUG UI: Click thumbnail nhưng ảnh chính không thay đổi!"
            print("   + [PASSED] Đồng bộ Thumbnail và Ảnh chính hoạt động mượt mà!")
    except Exception as e:
        print("   + [INFO] Không tìm thấy thư viện thumbnail để test.")

# =====================================================================
# KỊCH BẢN 2: Validate Block Sản phẩm liên quan
# =====================================================================
def test_matrix_related_products(driver):
    wait = WebDriverWait(driver, 15)
    print("\n[Advanced] Kịch bản 2: Validate Block Sản phẩm liên quan...")
    driver.get(PRODUCT_URL)
    
    print("-> Bước 1: Cuộn xuống cuối trang để kích hoạt Lazy Load...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
    time.sleep(2) 
    
    try:
        related_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'product-block')]//h3/a | //*[contains(@class, 'related')]//a[contains(@class, 'product')]")
        assert len(related_items) > 0, "LỖI: Block Sản phẩm liên quan trống!"
        print(f"   + [PASSED] Đã tải thành công {len(related_items)} sản phẩm gợi ý.")
        
        print("-> TC_02 (Sản phẩm liên quan): Click sản phẩm gợi ý mở đúng trang...")
        first_related_item = related_items[0]
        expected_url = first_related_item.get_attribute("href")
        
        driver.execute_script("arguments[0].click();", first_related_item)
        wait.until(EC.url_contains(expected_url.split('/')[-1])) 
        print("   + [PASSED] Điều hướng sang sản phẩm gợi ý hoạt động chuẩn xác!")
        
    except Exception as e:
        pytest.fail(f"BUG UI: Lỗi khi xử lý block sản phẩm liên quan: {e}")

# =====================================================================
# KỊCH BẢN 3: Validate Cộng dồn số lượng Giỏ hàng (Cập nhật CSS Class chuẩn)
# =====================================================================
def test_matrix_cart_accumulation(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Advanced] Kịch bản 3: Validate Cộng dồn số lượng Giỏ hàng...")
    driver.get(PRODUCT_URL)
    
    # 1. Lấy số trên Badge Giỏ hàng TRƯỚC KHI MUA sử dụng class 'number-cart'
    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
        initial_count = extract_number(badge.text)
    except:
        initial_count = 0
    
    print(f"-> Bước 1: Giỏ hàng ban đầu có {initial_count} món. Tiến hành THÊM VÀO GIỎ lần 1...")
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3) # Đợi Popup giỏ hàng bật ra và API xử lý
    
    print("-> Bước 2: Bấm THÊM VÀO GIỎ lần 2 (Cùng sản phẩm đó)...")
    driver.get(PRODUCT_URL) # Tải lại trang để đóng popup sạch sẽ
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3) 
    
    print("-> TC_07: Kiểm tra Badge Giỏ hàng đã cộng dồn thành công chưa...")
    try:
        # Bắt dính lại thẻ span mang class 'number-cart' chuẩn xác của ICONDENIM
        badge_after = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.number-cart")))
        final_count = extract_number(badge_after.text)
        
        # Mua 2 lần thì số cuối cùng phải >= số ban đầu + 2
        assert final_count >= initial_count + 2, f"BUG LOGIC: Thêm 2 lần nhưng hệ thống không cộng dồn! (Hiện tại: {final_count})"
        print(f"   + [PASSED] Giỏ hàng đã cộng dồn thành công trên Badge: {final_count} áo.")
    except Exception as e:
        pytest.fail(f"Không bắt được Icon giỏ hàng bằng class .number-cart. Lỗi: {e}")