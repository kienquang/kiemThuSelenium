import pytest
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, InvalidElementStateException


PRODUCT_URL = "https://icondenim.com/products/ao-thun-nam-seminal-form-boxy"

QTY_INPUT_ID = "quantity"
BTN_PLUS_CSS = "input.qtyplus"
BTN_MINUS_CSS = "input.qtyminus"
BTN_ADD_CART_XPATH = "//button[@id='add-to-cart'] | //button[contains(translate(., 'thêm vào giỏ', 'THÊM VÀO GIỎ'), 'THÊM VÀO GIỎ')]"

CART_BADGE_CSS = ".js-number-cart-new"
TOAST_ERROR_XPATH = "//div[@id='modal-error']"

# Tất cả size swatch wrapper
SIZE_SWATCH_CSS = "div[data-option-index='1'] .n-sd.swatch-element"

# Radio input bên trong mỗi swatch
SIZE_RADIO_CSS  = "div[data-option-index='1'] input[name='option2']"

# Radio input đang được checked (size đang active)
SIZE_CHECKED_CSS = "div[data-option-index='1'] input[name='option2']:checked"

@pytest.fixture(scope="function")
def wait(driver):
    """Cấu hình bộ quản lý thời gian chờ Explicit Wait (Tối đa 12s)"""
    return WebDriverWait(driver, 12)

def swatch_in_option(option_index: int) -> str:
    return f"div[data-option-index='{option_index}'] .n-sd.swatch-element"

class TestAddToCart:

    # ADD_01 - Thêm 1 sản phẩm 
    def test_add_01_add_single_product_to_cart(self, driver, wait):
        print("\n[ADD_01] Thêm 1 sản phẩm vào giỏ hàng")
        driver.get(PRODUCT_URL)
        
        try:
            badge_text = driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
            initial_count = int(badge_text) if badge_text.isdigit() else 0
        except NoSuchElementException:
            initial_count = 0
            
        btn_add = wait.until(EC.element_to_be_clickable((By.XPATH, BTN_ADD_CART_XPATH)))
        driver.execute_script("arguments[0].click();", btn_add)
        
        def is_cart_updated(d):
            try:
                current_text = d.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
                return int(current_text) > initial_count if current_text.isdigit() else False
            except (NoSuchElementException, ValueError):
                return False

        wait.until(is_cart_updated)
        
        final_count = int(driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip())
        assert final_count > initial_count, f"Lỗi Đồng Bộ: Giỏ hàng không nảy số (Initial: {initial_count}, Final: {final_count})"
        print(f" Bong bóng giỏ hàng đã cập nhật số lượng ({initial_count} → {final_count}).")

    # ADD_02 - Thêm số lượng lớn sản phẩm vào giỏ
    def test_add_02_add_large_quantity_to_cart(self, driver, wait):
        print("\n[ADD_02] Thêm số lượng lớn vào giỏ")
        driver.get(PRODUCT_URL)
        
        try:
            badge_text = driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
            initial_count = int(badge_text) if badge_text.isdigit() else 0
        except NoSuchElementException:
            initial_count = 0

        input_qty = wait.until(EC.presence_of_element_located((By.ID, QTY_INPUT_ID)))
        btn_plus = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, BTN_PLUS_CSS)))
        
        click_count = 10
        for i in range(click_count):
            current_qty = int(driver.find_element(By.ID, QTY_INPUT_ID).get_attribute("value"))
            driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, BTN_PLUS_CSS))
            wait.until(lambda d, expected=current_qty + 1:
                int(d.find_element(By.ID, QTY_INPUT_ID).get_attribute("value")) == expected
            )

        added_qty = int(driver.find_element(By.ID, QTY_INPUT_ID).get_attribute("value"))  
        
        btn_add = driver.find_element(By.XPATH, BTN_ADD_CART_XPATH)
        driver.execute_script("arguments[0].click();", btn_add)
        
        expected_final_count = initial_count + added_qty
        
        def is_exact_cart_updated(d):
            try:
                current_text = d.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
                return int(current_text) == expected_final_count if current_text.isdigit() else False
            except (NoSuchElementException, ValueError):
                return False

        wait.until(is_exact_cart_updated)
        print(f"(Tổng: {expected_final_count}).")
   
    # ADD_03 - Thêm số lượng vượt tồn kho 
    def test_add_03_add_over_stock_limit(self, driver, wait):
        print("\n[ADD_05] Thử thêm số lượng vượt tồn kho")
        driver.get(PRODUCT_URL)
        
        input_qty = wait.until(EC.presence_of_element_located((By.ID, QTY_INPUT_ID)))
        driver.execute_script("arguments[0].value='9999';", input_qty)
        
        btn_add = wait.until(EC.presence_of_element_located((By.XPATH, BTN_ADD_CART_XPATH)))
        driver.execute_script("arguments[0].click();", btn_add)
        
        error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, TOAST_ERROR_XPATH)))
        assert error_msg.is_displayed(), "Lỗi: không chặn vượt tồn kho."
        print(" Backend đã chặn số lượng vượt tồn kho. ")

    # ADD_04 - Không cho giảm dưới 1
    def test_add_04_quantity_not_less_than_one(self, driver, wait):
        print("\n[ADD_04] Không cho giảm dưới 1")
        driver.get(PRODUCT_URL)
        
        input_qty = wait.until(EC.presence_of_element_located((By.ID, QTY_INPUT_ID)))
        btn_minus = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, BTN_MINUS_CSS)))
        
        for _ in range(3):
            driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, BTN_MINUS_CSS))
            wait.until(lambda d: int(d.find_element(By.ID, QTY_INPUT_ID).get_attribute("value")) >= 1)

        final_qty = int(driver.find_element(By.ID, QTY_INPUT_ID).get_attribute("value"))  
        assert final_qty == 1, f" số lượng bị giảm xuống dưới 1 (hiện tại: {final_qty})"

    # ADD_05 - Thêm vào giỏ hàng khi thay đổi thuộc tính sản phẩm
    def test_add_05_add_to_cart_with_changed_variant(self, driver, wait):

        print("\n[ADD_05] Thêm vào giỏ hàng khi thay đổi thuộc tính sản phẩm")

        driver.get(PRODUCT_URL)

        try:
            badge_text = driver.find_element(
                By.CSS_SELECTOR,
                CART_BADGE_CSS
            ).text.strip()

            initial_count = (
                int(badge_text)
                if badge_text.isdigit()
                else 0
            )

        except NoSuchElementException:
            initial_count = 0

        print(f"   -> Badge ban đầu: {initial_count}")

        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, SIZE_SWATCH_CSS)
            )
        )

        try:
            checked_radio = driver.find_element(
                By.CSS_SELECTOR,
                SIZE_CHECKED_CSS
            )

            default_size = checked_radio.get_attribute("value")

        except NoSuchElementException:

            first_radio = driver.find_element(
                By.CSS_SELECTOR,
                SIZE_RADIO_CSS
            )

            default_size = first_radio.get_attribute("value")

        print(f"   -> Size mặc định: {default_size}")

        all_swatches = driver.find_elements(
            By.CSS_SELECTOR,
            SIZE_SWATCH_CSS
        )

        target_swatch = None
        selected_size = None

        for swatch in all_swatches:

            classes = swatch.get_attribute("class") or ""
            value = swatch.get_attribute("data-value")

            if (
                value != default_size
                and "sold-out" not in classes
                and "disabled" not in classes
                and "unavailable" not in classes
            ):

                target_swatch = swatch
                selected_size = value
                break

        assert target_swatch is not None, (
            "Không tìm được size khả dụng khác."
        )

        target_radio = target_swatch.find_element(
            By.CSS_SELECTOR,
            "input[type='radio']"
        )

        target_label = target_swatch.find_element(
            By.TAG_NAME,
            "label"
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            target_label
        )

        wait.until(
            EC.element_to_be_clickable(target_label)
        )

        target_label.click()

        print(f"   -> Đã click size: {selected_size}")

        wait.until(
            lambda d: target_radio.is_selected()
        )

        print(
            f"   -> Xác nhận size "
            f"'{selected_size}' đã selected"
        )

        btn_add = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, BTN_ADD_CART_XPATH)
            )
        )

        btn_add.click()

        print("   -> Đã click Thêm vào giỏ")

        def is_cart_updated(d):

            try:
                current_text = d.find_element(
                    By.CSS_SELECTOR,
                    CART_BADGE_CSS
                ).text.strip()

                return (
                    int(current_text) > initial_count
                    if current_text.isdigit()
                    else False
                )

            except (NoSuchElementException, ValueError):
                return False

        wait.until(is_cart_updated)

        final_count = int(
            driver.find_element(
                By.CSS_SELECTOR,
                CART_BADGE_CSS
            ).text.strip()
        )

        assert final_count > initial_count, (
            f"Lỗi: Không thêm được size "
            f"'{selected_size}' vào giỏ hàng "
            f"(Initial: {initial_count}, "
            f"Final: {final_count})"
        )

        print(
            f"  đã Xác thực: "
            f"Size '{selected_size}' "
            f"đã được thêm vào giỏ hàng "
            f"({initial_count} → {final_count})"
        )

    # ADD_06 - số âm bằng DevTools
    def test_add_06_negative_quantity_bypass(self, driver, wait):
        print("\n[ADD_14] Thử nghiệm xuyên thủng UI bằng số âm (XSS/JS Injection)")
        driver.get(PRODUCT_URL)
        
        input_qty = wait.until(EC.presence_of_element_located((By.ID, QTY_INPUT_ID)))
        
        driver.execute_script("arguments[0].value='-10';", input_qty)
        
        btn_add = wait.until(EC.element_to_be_clickable((By.XPATH, BTN_ADD_CART_XPATH)))
        driver.execute_script("arguments[0].click();", btn_add)
        
        error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, TOAST_ERROR_XPATH)))
        assert error_msg.is_displayed(), "Lỗi: Backend chấp nhận nạp số lượng âm."
        print(" Backend đã chặn số lượng âm ")


    # ADD_07 - vượt tồn kho bằng DevTools
    def test_add_07_bypass_over_stock_quantity(self, driver, wait):
        print("\n[ADD_15] Thử nghiệm ép tải Database bằng số lượng cực đại")
        driver.get(PRODUCT_URL)
        
        try:
            badge_text = driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
            initial_count = int(badge_text) if badge_text.isdigit() else 0
        except NoSuchElementException:
            initial_count = 0
            
        input_qty = wait.until(EC.presence_of_element_located((By.ID, QTY_INPUT_ID)))
        driver.execute_script("arguments[0].value='999999';", input_qty)
        
        btn_add = wait.until(EC.element_to_be_clickable((By.XPATH, BTN_ADD_CART_XPATH)))
        driver.execute_script("arguments[0].click();", btn_add)
        
        try:
            wait_short = WebDriverWait(driver, 2)
            wait_short.until(lambda d: int(d.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()) > initial_count)
            raise AssertionError("Lỗi: Backend chấp nhận đơn hàng vượt tồn kho.")
        except TimeoutException:
            print("  Backend đã chặn số lượng vượt tồn kho. ")
            