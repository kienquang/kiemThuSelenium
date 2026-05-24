import time
import pytest
from selenium.common.exceptions import JavascriptException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# CENTRALIZED CONFIGURATION
# ==========================================
PRODUCT_URLS = [
    "https://icondenim.com/products/ao-thun-nam-seminal-form-boxy",
    "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-linen-cuban-sandrift-form-relaxed"
]
CART_URL = "https://icondenim.com/cart"

# Bộ định vị phần tử
REMOVE_BTN_XPATH = "//span[@class='remove-wrap']/a[i[contains(@class, 'fa-times')]]"
EMPTY_CART_MSG_XPATH = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'giỏ hàng trống') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'không có sản phẩm')]"

@pytest.fixture(scope="function")
def wait(driver):
    """Cấu hình bộ quản lý thời gian chờ Explicit Wait (Tối đa 12s)"""
    return WebDriverWait(driver, 12)

class TestCartDelete:

    # =========================================================
    # DELETE_01 - Xóa 1 sản phẩm khỏi giỏ hàng chứa nhiều sản phẩm
    # =========================================================
    def test_delete_01_remove_one_product(self, driver, wait):
        print("\n[DELETE_01] Xóa 1 sản phẩm khỏi giỏ hàng")
        # Sửa lỗi: Truyền danh sách URL
        self._add_multiple_products(driver, wait, PRODUCT_URLS) 
        
        driver.get(CART_URL)
        
        remove_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, REMOVE_BTN_XPATH)))
        initial_count = len(remove_buttons)
        
        if initial_count > 0:
            target_element = remove_buttons[0]
            # Sửa lỗi: Click chính xác vào element đầu tiên
            driver.execute_script("arguments[0].click();", target_element)
            
            # Tối ưu hóa đỉnh cao: Chờ chính xác element vừa bị click biến mất khỏi DOM (Staleness)
            wait.until(EC.staleness_of(target_element))
        
        # Rào chắn kiểm chứng
        current_buttons = driver.find_elements(By.XPATH, REMOVE_BTN_XPATH)
        assert len(current_buttons) == initial_count - 1, "Lỗi Đồng Bộ: Số lượng phần tử không giảm đúng 1 đơn vị."
        print("   ✓ Xác thực: Đã xóa 1 mặt hàng, giỏ hàng vẫn bảo toàn sản phẩm còn lại.")

    # =========================================================
    # DELETE_02 - Xóa hàng loạt sản phẩm (Dynamic Loop)
    # =========================================================
    def test_delete_02_remove_multiple_products(self, driver, wait):
        print("\n[DELETE_02] Xóa toàn bộ sản phẩm bằng vòng lặp động")
        self._add_multiple_products(driver, wait, PRODUCT_URLS)
        driver.get(CART_URL)
        
        # Sử dụng While loop để dọn sạch giỏ hàng bất kể số lượng ban đầu
        while True:
            remove_buttons = driver.find_elements(By.XPATH, REMOVE_BTN_XPATH)
            if not remove_buttons:
                break # Thoát vòng lặp khi không còn nút xóa nào
                
            target_element = remove_buttons[0]
            driver.execute_script("arguments[0].click();", target_element)
            wait.until(EC.staleness_of(target_element))
        
        # Chờ Empty State
        wait.until(EC.presence_of_element_located((By.XPATH, EMPTY_CART_MSG_XPATH)))
        print("   ✓ Xác thực: Thao tác xóa đa nhiệm quét sạch giỏ hàng mượt mà.")

    # =========================================================
    # DELETE_03 - Xóa sản phẩm cuối cùng (Kiểm chứng Empty State)
    # =========================================================
    def test_delete_03_remove_last_product(self, driver, wait):
        print("\n[DELETE_03] Xóa sản phẩm cuối cùng → Giỏ hàng trống")
        self._add_product_to_cart(driver, wait, PRODUCT_URLS[0])
        driver.get(CART_URL)
        
        remove_btn = wait.until(EC.element_to_be_clickable((By.XPATH, REMOVE_BTN_XPATH)))
        driver.execute_script("arguments[0].click();", remove_btn)
        
        # Tối ưu: Định vị thẳng vào Node thông báo thay vì quét toàn bộ page_source
        empty_msg_element = wait.until(EC.visibility_of_element_located((By.XPATH, EMPTY_CART_MSG_XPATH)))
        
        assert empty_msg_element.is_displayed(), "Lỗi Giao Diện: Không hiển thị Empty State."
        print("   ✓ Xác thực: Giao diện Empty State được kích hoạt chính xác.")

    # =========================================================
    # DELETE_04 - Reload trang kiểm tra tính toàn vẹn 
    # =========================================================
    def test_delete_04_reload_after_delete_one(self, driver, wait):
        print("\n[DELETE_04] Reload trang sau khi xóa sản phẩm duy nhất")
        self._add_product_to_cart(driver, wait, PRODUCT_URLS[0])
        driver.get(CART_URL)
        
        remove_btn = wait.until(EC.element_to_be_clickable((By.XPATH, REMOVE_BTN_XPATH)))
        driver.execute_script("arguments[0].click();", remove_btn)
        
        wait.until(EC.visibility_of_element_located((By.XPATH, EMPTY_CART_MSG_XPATH)))
        
        driver.refresh()
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # Assert lại sau khi reload
        elements = driver.find_elements(By.XPATH, EMPTY_CART_MSG_XPATH)
        assert len(elements) > 0, "Lỗi Đồng Bộ: Mặt hàng bị lặp lại (Ghost Item) xuất hiện sau khi reload trang."
        print("   ✓ Xác thực: Phiên làm việc đồng bộ nhất quán sau khi tải lại trang.")
    # =========================================================
    # DELETE_05 - Reload trang sau khi xóa nhiều sản phẩm
    # =========================================================
    def test_delete_05_reload_after_delete_multiple(self, driver, wait):
        print("\n[DELETE_05] Reload trang sau khi dọn dẹp hàng loạt")
        # 1. Tiền điều kiện: Nạp nhiều sản phẩm (Đã sửa lỗi tham số PRODUCT_URLS)
        self._add_multiple_products(driver, wait, PRODUCT_URLS)
        driver.get(CART_URL)
        
        # 2. Vòng lặp xóa động: Quét cạn giỏ hàng bằng EC.staleness_of
        while True:
            remove_buttons = driver.find_elements(By.XPATH, REMOVE_BTN_XPATH)
            if not remove_buttons:
                break # Phá vỡ vòng lặp khi mảng rỗng (DOM không còn nút xóa)
                
            target_element = remove_buttons[0]
            driver.execute_script("arguments[0].click();", target_element)
            
            # Chờ phần tử bị click tiêu biến hoàn toàn khỏi cấu trúc DOM
            wait.until(EC.staleness_of(target_element))
        
        # 3. Chốt chặn State-Mutation: Đảm bảo UI chuyển sang trạng thái trống trước khi reload
        wait.until(EC.visibility_of_element_located((By.XPATH, EMPTY_CART_MSG_XPATH)))
        
        # 4. Reload page và đợi luồng Document tải xong
        driver.refresh()
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # 5. Xác thực (Assertion): Kiểm chứng tính nhất quán của Database/Session sau khi reload
        elements = driver.find_elements(By.XPATH, EMPTY_CART_MSG_XPATH)
        assert len(elements) > 0, \
            "Lỗi Đồng Bộ Backend: Các mặt hàng đã bị xóa lại hiện về (Ghost Items) sau khi reload trang."
    # =========================================================
    # Helper Functions
    # =========================================================
    def _add_product_to_cart(self, driver, wait, target_url, ui_delay=1.0):
        """
        Helper nạp sản phẩm vào giỏ kết hợp Explicit Wait và Hard Sleep.
        :param ui_delay: Thời gian chờ (giây) sau mỗi action để UI kịp render các animation/transition.
        """
        driver.get(target_url)
        # time.sleep(ui_delay) # [1] Chờ toàn bộ layout, DOM và các script khởi tạo ban đầu ổn định
        
        cart_badge_css = ".js-number-cart-new"
        
        try:
            # 1. Xử lý Variant (Size/Color)
            variant_selectors = driver.find_elements(
                By.XPATH, 
                "//div[contains(@class, 'swatch-element')]//label | //div[contains(@class, 'select-swap')]//label"
            )
            if variant_selectors:
                driver.execute_script("arguments[0].click();", variant_selectors[0])
                # time.sleep(ui_delay) # [2] Chờ animation đổi màu viền size hoặc load ảnh biến thể mới

            # 2. Lấy số lượng hiện tại (Safe Parse)
            try:
                cart_badge = driver.find_element(By.CSS_SELECTOR, cart_badge_css)
                text_val = cart_badge.text.strip()
                initial_count = int(text_val) if text_val.isdigit() else 0
            except NoSuchElementException:
                initial_count = 0

            # 3. Click Thêm Vào Giỏ
            btn_add = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@id='add-to-cart'] | //button[contains(translate(., 'thêm vào giỏ', 'THÊM VÀO GIỎ'), 'THÊM VÀO GIỎ')]")
            ))
            driver.execute_script("arguments[0].click();", btn_add)
            # time.sleep(ui_delay) # [3] Chờ request XHR bắn đi và UI bắt đầu hiển thị trạng thái loading/blocking
            
            # 4. EXPLICIT WAIT: Chờ data thực sự thay đổi
            def is_cart_updated(d):
                try:
                    badge_text = d.find_element(By.CSS_SELECTOR, cart_badge_css).text.strip()
                    return int(badge_text) > initial_count if badge_text.isdigit() else False
                except (NoSuchElementException, ValueError):
                    return False

            wait.until(is_cart_updated)
            # time.sleep(ui_delay) # [4] Chờ các Toast message/Popup báo thành công trượt lên và biến mất hoàn toàn
            
            print(f"   → Đã nạp thành công mặt hàng: {target_url.split('/')[-1]}")
            
        except TimeoutException:
            print(f"   [WARNING] Timeout: Không thấy giỏ hàng cập nhật tại ({target_url}).")
        except JavascriptException as je:
            print(f"   [ERROR] Lỗi thực thi JS khi click tại ({target_url}). Chi tiết: {je.msg}")
        except Exception as e:
            print(f"   [ERROR] Thất bại không xác định tại ({target_url}): {str(e)}")


    def _add_multiple_products(self, driver, wait, product_urls: list, ui_delay=1.0):
        """Helper nạp đồng thời nhiều sản phẩm, truyền ui_delay xuyên suốt."""
        if not isinstance(product_urls, list) or not product_urls:
            print("   [WARNING] Danh sách sản phẩm rỗng.")
            return

        for url in product_urls:
            self._add_product_to_cart(driver, wait, url, ui_delay=ui_delay)