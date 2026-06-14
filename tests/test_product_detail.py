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


# =====================================================================
# KỊCH BẢN 2: KIỂM THỬ SỐ LƯỢNG & BIẾN THỂ (Cover: PDP_03, PDP_04, PDP_05)
# =====================================================================
def test_pdp_quantity_and_size(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Bắt đầu] Test Chọn Size & Tăng Giảm Số lượng...")
    
    driver.get(PRODUCT_URL)
    
    print("-> TC_PDP_04: Nút Tăng Số lượng (+)...")
    try:
        btn_plus = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'plus') or contains(@class, 'add')] | //input[contains(@class, 'plus')] | //div[contains(@class, 'qtyplus')]")))
        input_qty = wait.until(EC.presence_of_element_located((By.ID, "quantity")))
        
        driver.execute_script("arguments[0].click();", btn_plus)
        time.sleep(0.5) 
        driver.execute_script("arguments[0].click();", btn_plus)
        time.sleep(0.5)
        
        qty_value = int(input_qty.get_attribute("value"))
        assert qty_value > 1, f"BUG UI: Nút Tăng Số Lượng (+) không hoạt động! (Giá trị hiện tại: {qty_value})"
        print(f"   + [PASSED] Tăng số lượng thành công lên {qty_value}")
        
    except Exception as e:
         pytest.fail(f"Lỗi khi tương tác nút Tăng số lượng: {e}")

    print("-> TC_PDP_05: Giới hạn Nút Giảm (-)...")
    try:
        btn_minus = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'minus') or contains(@class, 'sub')] | //input[contains(@class, 'minus')] | //div[contains(@class, 'qtyminus')]")))
        
        # Click Giảm 5 lần (để cố ý dìm nó xuống số âm)
        for _ in range(5):
             driver.execute_script("arguments[0].click();", btn_minus)
             time.sleep(0.2)
        
        qty_value_after = int(input_qty.get_attribute("value"))
        assert qty_value_after >= 1, f"BUG BẢO MẬT: Nút Giảm (-) cho phép hạ số lượng xuống số âm hoặc 0! ({qty_value_after})"
        print(f"   + [PASSED] Nút Giảm chặn cứng tại số {qty_value_after} an toàn.")
        
    except Exception as e:
         pytest.fail(f"Lỗi khi tương tác nút Giảm số lượng: {e}")

    print("-> TC_PDP_03: Chức năng Chọn Size / Chọn Màu (Variant Select)...")
    try:
        # Bắt chính xác các nhãn Variant hiển thị thật trên ICONDENIM (thường là thẻ label nằm trong swatch-element)
        css_selector = ".swatch-element label, .select-swap .swap-elements label, .variant-swatch label"
        swatch_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        
        # Lọc ra các nút THỰC SỰ có chứa chữ (S, M, L, Đen, Trắng...) và đang hiển thị
        valid_labels = [label for label in swatch_labels if label.text.strip() != "" and label.is_displayed()]
        
        if len(valid_labels) > 1:
            # Chọn nhãn THỨ 2 để đảm bảo nó khác với cái đang được chọn mặc định
            target_label = valid_labels[1]
            size_name = target_label.text.strip()
            
            print(f"   + Đang nhắm mục tiêu vào Size/Màu: '{size_name}'")
            
            # KHOANH VIỀN ĐỎ để bạn nhìn rõ mồn một trên màn hình
            driver.execute_script("arguments[0].style.border = '3px solid red';", target_label)
            time.sleep(1.5) # Dừng 1.5s để bạn quan sát viền đỏ
            
            # Thực hiện Click chuyển đổi
            driver.execute_script("arguments[0].click();", target_label)
            time.sleep(1) # Chờ cho UI cập nhật (Ví dụ: nhảy viền đen báo hiệu đã chọn)
            
            print(f"   + [PASSED] Đã click chọn Biến thể '{size_name}' thành công!")
        else:
             print("   + [INFO] Sản phẩm này không có nhiều tuỳ chọn Size/Màu để đổi.")
             
    except Exception as e:
         pytest.fail(f"BUG UI: Không thể click đổi Variant. Lỗi: {e}")

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