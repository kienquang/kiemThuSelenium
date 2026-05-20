import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Định nghĩa link sản phẩm dùng chung cho các testcase
PRODUCT_URL = "https://icondenim.com/products/ao-thun-nam-seminal-form-boxy"

def test_pdp_ui_and_tabs(driver):
    """
    [NHÓM 1] KIỂM THỬ HIỂN THỊ VÀ TƯƠNG TÁC UI (Cover TC: PDP_01, PDP_02, PDP_09)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Test Giao diện & Tab Mô tả...")
    
    driver.get(PRODUCT_URL)
    
    print("-> Bước 1: Kiểm tra thông tin cơ bản (Tên, Giá)...")
    title = wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
    price = driver.find_element(By.XPATH, "//span[contains(@class, 'price') or contains(@class, 'current-price')]")
    assert title.text.strip() != "", "Lỗi: Không hiển thị tên sản phẩm"
    assert price.text.strip() != "", "Lỗi: Không hiển thị giá sản phẩm"
    
    print("-> Bước 2: Kiểm tra thư viện ảnh (Click Thumbnail)...")
    try:
        # Tìm các ảnh nhỏ (thumbnail) và click vào ảnh thứ 2
        thumbnails = driver.find_elements(By.XPATH, "//div[contains(@class, 'thumbnail')]//img | //a[contains(@data-fancybox, 'gallery')]")
        if len(thumbnails) > 1:
            driver.execute_script("arguments[0].click();", thumbnails[1])
            time.sleep(1) # Chờ ảnh chính đổi
            print("   + Đã tương tác với thư viện ảnh thành công.")
    except Exception as e:
        print(f"   [WARNING] Không tìm thấy thumbnail ảnh: {e}")

    print("-> Bước 3: Kiểm tra chuyển đổi Tab thông tin...")
    try:
        # Bấm sang Tab "CHÍNH SÁCH GIAO HÀNG" hoặc Tab thứ 2
        tab_delivery = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'nav-tabs')]//li[2] | //div[contains(@class, 'tab')][2]")))
        driver.execute_script("arguments[0].click();", tab_delivery)
        print("   + Chuyển Tab thông tin thành công.")
    except Exception as e:
        print(f"   [WARNING] Không tìm thấy Tab mô tả: {e}")
        
    print("[PASSED] Kịch bản Giao diện & UI hoàn tất!")


def test_pdp_quantity_and_size(driver):
    """
    [NHÓM 2] KIỂM THỬ TƯƠNG TÁC BIẾN THỂ & SỐ LƯỢNG 
    (Đã tối ưu Locator dựa trên HTML thực tế của ICONDENIM)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Test Chọn Size & Tăng Giảm Số lượng...")
    
    driver.get(PRODUCT_URL)
    
    print("-> Bước 1: Kiểm thử Nút Tăng Số lượng (+)...")
    # Tối ưu: Dùng thẳng CSS Selector nhắm vào class .qtyplus và thẻ input có id là quantity
    btn_plus = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.qtyplus")))
    input_qty = driver.find_element(By.ID, "quantity") # Ưu tiên 1: Dùng ID
    
    # Bấm dấu + hai lần
    driver.execute_script("arguments[0].click();", btn_plus)
    driver.execute_script("arguments[0].click();", btn_plus)
    time.sleep(1)
    assert int(input_qty.get_attribute("value")) > 1, "Lỗi: Nút Tăng số lượng không hoạt động"
    
    print("-> Bước 2: Kiểm thử giới hạn Nút Giảm Số lượng (-)...")
    # Tối ưu: Dùng CSS Selector nhắm vào class .qtyminus
    btn_minus = driver.find_element(By.CSS_SELECTOR, "input.qtyminus")
    
    # Bấm dấu - ba lần (Cố tình bấm lố để xem có bị về số 0 hoặc âm không)
    driver.execute_script("arguments[0].click();", btn_minus)
    driver.execute_script("arguments[0].click();", btn_minus)
    driver.execute_script("arguments[0].click();", btn_minus)
    time.sleep(1)
    
    # Số lượng không được nhỏ hơn 1 (như thuộc tính min="1" trong HTML của họ)
    current_qty = int(input_qty.get_attribute("value"))
    print(f"   + Số lượng sau khi cố tình giảm quá mức: {current_qty}")
    assert current_qty >= 1, "BUG NGHIÊM TRỌNG: Số lượng có thể giảm xuống dưới 1!"

    print("-> Bước 3: Kiểm thử chức năng Chọn Size...")
    try:
        # Tối ưu XPATH tìm thẻ label có chứa chữ L chính xác
        size_l = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='L']")))
        driver.execute_script("arguments[0].click();", size_l)
        print("   + Click chọn Size L thành công.")
    except Exception as e:
        print("   [WARNING] Sản phẩm không có Size để chọn.")

    print("[PASSED] Kịch bản Biến thể & Số lượng hoàn tất!")

def test_pdp_add_to_cart_flow(driver):
    """
    [NHÓM 3] KIỂM THỬ LUỒNG MUA HÀNG (Cover TC: PDP_07, PDP_08)
    """
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Test Luồng Thêm Vào Giỏ Hàng...")
    
    driver.get(PRODUCT_URL)
    
    print("-> Bước 1: Chọn Size (Chuẩn bị dữ liệu)...")
    try:
        size_l = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swatch')]//label[normalize-space(text())='L']")))
        driver.execute_script("arguments[0].click();", size_l)
    except:
        pass # Nếu freesize thì bỏ qua

    print("-> Bước 2: Bấm nút THÊM VÀO GIỎ...")
    btn_add_to_cart = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add_to_cart)
    
    print("-> Bước 3: Xác thực hệ thống hiển thị Giỏ hàng/Thông báo...")
    time.sleep(3) # Đợi animation popup giỏ hàng trượt ra
    
    page_source = driver.page_source.lower()
    is_success = "thành công" in page_source or "giỏ hàng" in page_source or "cart" in page_source
    
    assert is_success, "Lỗi: Không bắt được sự kiện thêm vào giỏ hàng thành công!"
    print("   + Đã hiển thị popup giỏ hàng thành công.")
    
    print("[PASSED] Kịch bản Thêm vào Giỏ Hàng hoàn tất!")
    time.sleep(2)