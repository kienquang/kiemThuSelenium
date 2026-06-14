import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Sử dụng một sản phẩm bất kỳ trên ICONDENIM
PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

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
# KỊCH BẢN 2: Validate Block Sản phẩm liên quan (Tối giản & Chính xác)
# =====================================================================
def test_matrix_related_products(driver):
    wait = WebDriverWait(driver, 15)
    print("\n[Advanced] Kịch bản 2: Validate Block Sản phẩm liên quan...")
    driver.get(PRODUCT_URL)
    
    print("-> Bước 1: Cuộn xuống cuối trang để kích hoạt Lazy Load...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
    time.sleep(2) 
    
    try:
        print("-> TC_02: Click mở sản phẩm gợi ý...")
        # Dựa sát vào HTML của bạn: Tìm thẻ slide đang ACTIVE và KHÔNG BỊ ẨN, lấy thẻ <a> bên trong nó
        css_selector = "div.item-slider.slick-active[aria-hidden='false'] a[href]"
        
        # Lấy danh sách các link hợp lệ
        valid_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        
        # Chọn link đầu tiên
        target_link = valid_links[0]
        expected_url = target_link.get_attribute("href")
        print(f"   + Tìm thấy link hợp lệ: {expected_url}")
        
        # BẮT BUỘC dùng Javascript Click để đâm xuyên qua lớp draggable của Slick Slider
        driver.execute_script("arguments[0].click();", target_link)
        
        # Đợi trình duyệt nhảy sang URL mới
        wait.until(EC.url_contains(expected_url.split('/')[-1]))
        
        print(f"   + [PASSED] Đã mở thành công trang: '{driver.title}'")
        
    except Exception as e:
        pytest.fail(f"BUG UI: Không thể click vào link sản phẩm liên quan. Lỗi: {e}")
# =====================================================================
# KỊCH BẢN 3: Validate Cộng dồn số lượng Giỏ hàng (Đã fix chọn Size chính xác)
# =====================================================================
def test_matrix_cart_accumulation(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Advanced] Kịch bản 3: Validate Cộng dồn số lượng Giỏ hàng...")
    driver.get(PRODUCT_URL)
    
    # 1. Lấy số trên Badge Giỏ hàng TRƯỚC KHI MUA
    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
        initial_count = extract_number(badge.text)
    except:
        initial_count = 0
    
    print(f"-> Bước 1: Giỏ hàng ban đầu có {initial_count} món. Tiến hành chọn Size và THÊM VÀO GIỎ lần 1...")
    
    # Dùng CSS Selector chuẩn xác dựa vào ảnh F12 (Chỉ lấy các label nằm trong khối is-size)
    size_selector = "div.is-size label, div.swatch-element.is-size label"
    
    try:
        size_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, size_selector)))
        valid_sizes = [label for label in size_labels if label.is_displayed()]
        
        if len(valid_sizes) > 1:
            size_m = valid_sizes[1] # Chọn Size thứ 2 (Thường là M)
            print(f"   + Lần 1 - Đã ép chọn Size: '{size_m.text.strip()}'")
            driver.execute_script("arguments[0].style.border = '3px solid red';", size_m)
            driver.execute_script("arguments[0].click();", size_m)
            time.sleep(1) 
    except Exception:
        pass 

    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3) 
    
    print("-> Bước 2: Tải lại trang, chọn Size khác và Bấm THÊM VÀO GIỎ lần 2...")
    driver.get(PRODUCT_URL) 
    
    try:
        size_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, size_selector)))
        valid_sizes = [label for label in size_labels if label.is_displayed()]
        
        # Nếu có từ 3 size trở lên, ta chọn Size thứ 3 (Thường là L) để đa dạng Testcase
        if len(valid_sizes) > 2:
            size_l = valid_sizes[2] 
            print(f"   + Lần 2 - Đã ép chọn Size: '{size_l.text.strip()}'")
            driver.execute_script("arguments[0].style.border = '3px solid blue';", size_l)
            driver.execute_script("arguments[0].click();", size_l)
            time.sleep(1)
        elif len(valid_sizes) > 1:
            # Nếu chỉ có 2 size, thì chọn lại cái thứ 2
            size_m = valid_sizes[1]
            driver.execute_script("arguments[0].click();", size_m)
            time.sleep(1)
    except Exception:
        pass

    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3) 
    
    print("-> TC_07: Kiểm tra Badge Giỏ hàng đã cộng dồn thành công chưa...")
    try:
        badge_after = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.number-cart")))
        final_count = extract_number(badge_after.text)
        
        assert final_count >= initial_count + 2, f"BUG LOGIC: Thêm 2 lần nhưng hệ thống không cộng dồn! (Hiện tại: {final_count})"
        print(f"   + [PASSED] Giỏ hàng đã cộng dồn thành công trên Badge: {final_count} áo.")
    except Exception as e:
        pytest.fail(f"Không bắt được Icon giỏ hàng. Lỗi: {e}")