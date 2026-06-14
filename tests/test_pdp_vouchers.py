import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

# =====================================================================
# TC_VOUCHER_01: Mở Popup Voucher thành công
# =====================================================================
def test_pdp_open_voucher_popup(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Voucher] Kịch bản 1: Mở bảng Mã Giảm Giá...")
    driver.get(PRODUCT_URL)
    
    try:
        # 1. Tìm khu vực chứa Voucher dựa vào class bạn cung cấp
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn, .coupon_item")))
        
        # Cuộn màn hình đến khu vực đó và khoanh viền đỏ
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", voucher_btn)
        driver.execute_script("arguments[0].style.border = '3px solid red';", voucher_btn)
        time.sleep(1.5)
        
        # 2. Click để mở Popup
        driver.execute_script("arguments[0].click();", voucher_btn)
        print("   + Đã click vào nút xem Voucher.")
        
        # 3. Chờ Popup trượt ra (dựa vào class cart-coupon và trạng thái active)
        popup_panel = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.cart-coupon")))
        
        # Khẳng định Popup phải chứa class 'active' như trong ảnh F12 của bạn
        assert "active" in popup_panel.get_attribute("class"), "BUG UI: Popup không có trạng thái 'active' khi mở!"
        print("   + [PASSED] Bảng Mã Giảm Giá đã trượt ra và hiển thị thành công.")
        
    except Exception as e:
        pytest.fail(f"Lỗi khi tương tác với nút Voucher: {e}")

# =====================================================================
# TC_VOUCHER_02: Đóng Popup bằng cách click vào khoảng không (Overlay)
# =====================================================================
def test_pdp_close_voucher_via_overlay(driver):
    """
    Tiêu chuẩn UX: Khi một popup trượt ra, người dùng click ra vùng tối bên ngoài (overlay)
    thì popup phải tự động đóng lại.
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Voucher] Kịch bản 2: Đóng bảng bằng cách click vào vùng mờ (Overlay)...")
    driver.get(PRODUCT_URL)
    
    try:
        # Bỏ qua các bước chờ rườm rà, dùng JS click thẳng vào nút mở
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn")))
        driver.execute_script("arguments[0].click();", voucher_btn)
        
        # Chờ panel hiện lên
        popup_panel = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.cart-coupon")))
        time.sleep(1) # Chờ animation trượt xong
        
        # Tìm lớp Overlay (Vùng tối bên ngoài)
        overlay = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cart-coupon-overlay")))
        
        print("   + Đang click vào vùng Overlay bên ngoài để đóng bảng...")
        driver.execute_script("arguments[0].click();", overlay)
        time.sleep(1) # Chờ animation thu vào
        
        # Khẳng định Popup đã mất class 'active' hoặc bị ẩn đi
        is_active = "active" in popup_panel.get_attribute("class")
        assert not is_active, "BUG UX: Click vào Overlay nhưng Bảng Voucher không chịu đóng!"
        print("   + [PASSED] Bảng Voucher đã đóng lại mượt mà.")
        
    except Exception as e:
        pytest.fail(f"Lỗi khi test đóng Voucher: {e}")

# =====================================================================
# TC_VOUCHER_03: Kiểm tra nội dung bên trong Bảng Voucher không bị trống
# =====================================================================
def test_pdp_verify_voucher_content(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Voucher] Kịch bản 3: Xác minh dữ liệu bên trong Bảng Voucher...")
    driver.get(PRODUCT_URL)
    
    try:
        # Mở popup
        voucher_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-coupons.coupon-toggle-btn")))
        driver.execute_script("arguments[0].click();", voucher_btn)
        time.sleep(1.5)
        
        # Dựa vào ảnh thứ 2, khu vực chứa danh sách mã là class: section_coupons
        coupons_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.section_coupons")))
        
        # Đếm xem có bao nhiêu mã giảm giá bên trong
        # Thường mỗi mã sẽ nằm trong một div hoặc item
        inner_html = coupons_container.get_attribute("innerHTML")
        
        # Khẳng định bảng này phải chứa text hoặc code bên trong, không được trống rỗng trắng bóc
        assert len(inner_html.strip()) > 50, "BUG DATA: Bảng Voucher trượt ra nhưng KHÔNG CÓ mã giảm giá nào bên trong!"
        print("   + [PASSED] Bảng Voucher có tải dữ liệu danh sách mã giảm giá.")
        
    except Exception as e:
        pytest.fail(f"Lỗi khi kiểm tra nội dung Voucher: {e}")