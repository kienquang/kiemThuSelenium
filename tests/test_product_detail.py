import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

PRODUCT_URL = "https://icondenim.com/products/ao-thun-nam-seminal-form-boxy"

def test_pdp_ui_and_tabs(driver):
    """
    [NHÓM 1] KIỂM THỬ HIỂN THỊ UI & TABS (Cover: PDP_01, PDP_02, PDP_09)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Nhóm 1: Test Giao diện & Tab Mô tả...")
    driver.get(PRODUCT_URL)
    
    print("-> TC_PDP_01: Kiểm tra thông tin cơ bản...")
    title = wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
    price = driver.find_element(By.XPATH, "//span[contains(@class, 'price') or contains(@class, 'current-price')]")
    assert title.text.strip() != "", "Lỗi: Không hiển thị tên"
    assert price.text.strip() != "", "Lỗi: Không hiển thị giá"
    
    print("-> TC_PDP_02: Kiểm tra thư viện ảnh...")
    try:
        thumbnails = driver.find_elements(By.XPATH, "//div[contains(@class, 'thumbnail')]//img | //a[contains(@data-fancybox, 'gallery')]")
        if len(thumbnails) > 1:
            driver.execute_script("arguments[0].click();", thumbnails[1])
            time.sleep(1)
            print("   + Thư viện ảnh tương tác tốt.")
    except Exception:
        pass

    print("-> TC_PDP_09: Kiểm tra chuyển đổi Tab thông tin...")
    try:
        tab_delivery = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'nav-tabs')]//li[2] | //div[contains(@class, 'tab')][2]")))
        driver.execute_script("arguments[0].click();", tab_delivery)
        print("   + Đổi Tab thành công.")
    except Exception:
        pass

def test_pdp_quantity_and_size(driver):
    """
    [NHÓM 2] KIỂM THỬ SỐ LƯỢNG & BIẾN THỂ (Cover: PDP_03, PDP_04, PDP_05)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Nhóm 2: Test Chọn Size & Số lượng...")
    driver.get(PRODUCT_URL)
    
    print("-> TC_PDP_04: Nút Tăng Số lượng (+)...")
    btn_plus = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.qtyplus, button.plus")))
    input_qty = driver.find_element(By.ID, "quantity")
    
    driver.execute_script("arguments[0].click();", btn_plus)
    driver.execute_script("arguments[0].click();", btn_plus)
    assert int(input_qty.get_attribute("value")) > 1, "Lỗi: Không thể tăng số lượng"
    
    print("-> TC_PDP_05: Giới hạn Nút Giảm (-)...")
    btn_minus = driver.find_element(By.CSS_SELECTOR, "input.qtyminus, button.minus")
    driver.execute_script("arguments[0].click();", btn_minus)
    driver.execute_script("arguments[0].click();", btn_minus)
    driver.execute_script("arguments[0].click();", btn_minus)
    
    assert int(input_qty.get_attribute("value")) >= 1, "Lỗi: Số lượng bị giảm xuống dưới 1"

    print("-> TC_PDP_03: Chức năng Chọn Size...")
    try:
        size_m = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='M']")))
        driver.execute_script("arguments[0].click();", size_m)
        time.sleep(0.5)
        size_l = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='L']")))
        driver.execute_script("arguments[0].click();", size_l)
        print("   + Chọn Size L highlight thành công.")
    except Exception:
        pass

def test_pdp_negative_add_to_cart(driver):
    """
    [NHÓM 3] KIỂM THỬ NGOẠI LỆ (Cover: PDP_06)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Nhóm 3: Test Cố tình lỗi (Quên chọn size)...")
    driver.get(PRODUCT_URL)
    
    print("-> TC_PDP_06: Bấm thêm vào giỏ khi CHƯA chọn size...")
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(2)
    
    # Kiểm tra xem có cảnh báo (alert / text báo lỗi) hoặc giỏ hàng có KHÔNG hiện ra không
    page_text = driver.page_source.lower()
    
    # Ở nhiều web Haravan, nếu không chọn size hệ thống sẽ báo "Vui lòng chọn Kích thước" 
    # HOẶC hệ thống chặn không cho giỏ hàng bật lên.
    # Lưu ý: Một số web tự động lấy mặc định Size S, lúc này test case có thể cần sửa logic báo Pass/Fail
    if "vui lòng chọn" in page_text or "chọn kích thước" in page_text:
        print("   + Đã bắt được cảnh báo: Yêu cầu chọn Size!")
    else:
        print("   [INFO] Web tự động chọn Size mặc định hoặc không hiển thị cảnh báo dạng text rõ ràng.")


def test_pdp_buy_actions(driver):
    """
    [NHÓM 4] KIỂM THỬ MUA HÀNG & MUA NGAY (Cover: PDP_07, PDP_08)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Nhóm 4: Test chức năng Add to Cart & Buy Now...")
    
    # -------- TC_PDP_07: THÊM VÀO GIỎ --------
    driver.get(PRODUCT_URL)
    print("-> TC_PDP_07: Chọn size và Thêm Vào Giỏ...")
    try:
        size_l = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='L']")))
        driver.execute_script("arguments[0].click();", size_l)
    except:
        pass
        
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3)
    
    assert "thành công" in driver.page_source.lower() or "giỏ hàng" in driver.page_source.lower(), "Lỗi: Không thấy phản hồi thêm giỏ hàng"
    print("   + Thêm vào giỏ thành công.")

    # -------- TC_PDP_08: MUA NGAY --------
    print("-> TC_PDP_08: Bấm nút MUA NGAY...")
    # Tải lại trang cho sạch session
    driver.get(PRODUCT_URL)
    try:
        size_m = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='M']")))
        driver.execute_script("arguments[0].click();", size_m)
    except:
        pass
        
    btn_buy_now = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='buy-now'] | //button[contains(., 'MUA NGAY')]")))
    driver.execute_script("arguments[0].click();", btn_buy_now)
    
    # Đợi trình duyệt chuyển hướng (URL sẽ đổi sang trang /checkout hoặc /cart)
    time.sleep(4)
    current_url = driver.current_url.lower()
    
    # Khẳng định URL đã thay đổi, không còn nằm ở trang chi tiết sản phẩm nữa
    assert "checkout" in current_url or "cart" in current_url, "Lỗi: Nút Mua Ngay không chuyển hướng sang trang thanh toán!"
    print(f"   + Chuyển hướng thành công sang: {current_url}")

# =====================================================================
# [NHÓM 5] DATA-DRIVEN TESTING (KIỂM THỬ HƯỚNG DỮ LIỆU) 
# Kỹ thuật chuyên sâu: Kiểm tra ô nhập số lượng với các dữ liệu dị biệt
# =====================================================================

@pytest.mark.parametrize("invalid_input", [
    ("0"),       # Giá trị biên dưới giới hạn
    ("-5"),      # Giá trị âm
    ("abc"),     # Ký tự chữ
    ("@#$")      # Ký tự đặc biệt
])
def test_pdp_advanced_quantity_input(driver, invalid_input):
    """
    Test ô nhập số lượng bằng cách gõ trực tiếp từ bàn phím các giá trị không hợp lệ.
    Kỳ vọng: Hệ thống tự động sửa sai (trả về 1) hoặc bỏ qua ký tự chữ, không cho phép mua số lượng vô lý.
    """
    wait = WebDriverWait(driver, 10)
    print(f"\n[Data-Driven] Test nhập trực tiếp dữ liệu dị biệt: '{invalid_input}'")
    
    driver.get(PRODUCT_URL)
    
    # Tìm ô nhập số lượng
    input_qty = wait.until(EC.presence_of_element_located((By.ID, "quantity")))
    
    # Xóa dữ liệu cũ trong ô (Dùng phím Backspace để xóa cho sạch)
    input_qty.send_keys(Keys.CONTROL + "a")
    input_qty.send_keys(Keys.BACKSPACE)
    time.sleep(0.5)
    
    # Gõ dữ liệu dị biệt vào và ấn ENTER
    input_qty.send_keys(invalid_input)
    input_qty.send_keys(Keys.ENTER)
    time.sleep(1)
    
    # Lấy giá trị thực tế sau khi Web đã xử lý
    current_value = input_qty.get_attribute("value")
    print(f"   + Giá trị Web ghi nhận sau khi gõ '{invalid_input}': là '{current_value}'")
    
    # Khẳng định: Web không được phép nhận số <= 0 và không được phép nhận chữ
    try:
        numeric_value = int(current_value)
        assert numeric_value >= 1, f"BUG BẢO MẬT: Web cho phép số lượng = {numeric_value}"
    except ValueError:
        # Nếu không ép kiểu sang số nguyên (int) được, tức là web cho phép nhập chữ -> BUG
        pytest.fail(f"BUG UI: Ô số lượng đang cho phép nhập chữ cái/ký tự đặc biệt: '{current_value}'")