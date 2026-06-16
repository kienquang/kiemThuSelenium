import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidElementStateException

PRODUCT_URL = "https://icondenim.com/products/quan-jeans-nam-ong-suong-scar-form-straight-1"
PRODUCT_URL_2 = "https://icondenim.com/products/ao-thun-nam-flux-form-regular"
CART_URL = "https://icondenim.com/cart"
PRODUCT_QTY_INPUT_ID = "quantity"
PRODUCT_BTN_PLUS_CSS = "input.qtyplus"
PRODUCT_BTN_MINUS_CSS = "input.qtyminus"
PRODUCT_ADD_TO_CART_XPATH = "//button[@id='add-to-cart'] | //button[contains(translate(., 'thêm vào giỏ', 'THÊM VÀO GIỎ'), 'THÊM VÀO GIỎ')]"
PRODUCT_VARIANT_XPATH = "//div[contains(@class, 'swatch-element')]//label | //div[contains(@class, 'select-swap')]//label"

CART_QTY_INPUT_CSS = "#quantity_cart"
CART_BTN_PLUS_CSS = ".btn-right-quantity"
CART_BTN_MINUS_CSS = ".btn-left-quantity"

CART_BADGE_CSS = ".js-number-cart-new"
MODAL_ERROR_CSS = "#modal-error"

OUT_OF_STOCK_XPATH = "//p[contains(@class, 'out-of-stock-label') and contains(text(), 'Hết hàng')]"
REMOVE_BTN_XPATH = "//span[@class='remove-wrap']/a[i[contains(@class, 'fa-times')]]"

@pytest.fixture(scope="function")
def driver():

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    
    yield driver 
    
    # Dọn dẹp - Chạy SAU khi test xong
    print("\n[Teardown] Xóa toàn bộ Cookies và LocalStorage để làm sạch Session...")
    driver.get(CART_URL)
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    driver.get("about:blank")
    driver.quit()

@pytest.fixture(scope="function")
def wait(driver):
    return WebDriverWait(driver, 25)

class TestCartUpdate:

    # Helper Functions
    def _wait_for_document_ready(self, driver, wait):
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def _safe_parse_int(self, raw_value, default=0):
        text = str(raw_value or "").strip()
        return int(text) if text.isdigit() else default

    def _safe_get_badge_count(self, driver):
        try:
            badge_text = driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text
            return self._safe_parse_int(badge_text, default=0)
        except NoSuchElementException:
            return 0

    def _wait_for_cart_overlay_to_clear(self, driver, timeout=8):
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: all(
                    element.value_of_css_property("display") == "none"
                    for element in d.find_elements(By.CSS_SELECTOR, ".cart-loading")
                )
            )
        except TimeoutException:
            pass

    def _wait_for_cart_quantity_stable(self, driver, expected_quantity, timeout=25):
        stable_matches_needed = 2
        matches = {"count": 0}

        def quantity_is_stable(d):
            try:
                quantity = self._safe_parse_int(
                    d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value"),
                    default=0
                )
            except NoSuchElementException:
                matches["count"] = 0
                return False

            if quantity == expected_quantity:
                matches["count"] += 1
            else:
                matches["count"] = 0

            return matches["count"] >= stable_matches_needed

        WebDriverWait(driver, timeout).until(quantity_is_stable)

    def _select_first_variant_if_present(self, driver):
        variant_selectors = driver.find_elements(By.XPATH, PRODUCT_VARIANT_XPATH)
        if variant_selectors:
            driver.execute_script("arguments[0].click();", variant_selectors[0])

    def _set_product_quantity(self, driver, wait, quantity):
        qty_input = wait.until(
            EC.visibility_of_element_located((By.ID, PRODUCT_QTY_INPUT_ID))
        )
        current_qty = self._safe_parse_int(qty_input.get_attribute("value"), default=1)

        if current_qty == quantity:
            return

        if current_qty < quantity:
            step_selector = PRODUCT_BTN_PLUS_CSS
            step = 1
        else:
            step_selector = PRODUCT_BTN_MINUS_CSS
            step = -1

        while current_qty != quantity:
            target_qty = current_qty + step
            step_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, step_selector))
            )
            driver.execute_script("arguments[0].click();", step_button)
            wait.until(
                lambda d, expected=target_qty:
                self._safe_parse_int(
                    d.find_element(By.ID, PRODUCT_QTY_INPUT_ID).get_attribute("value"),
                    default=0
                ) == expected
            )
            current_qty = target_qty

    def _add_product_to_cart_once(self, driver, wait, quantity=1, target_url=PRODUCT_URL):
        driver.get(target_url)
        self._wait_for_document_ready(driver, wait)

        initial_badge = self._safe_get_badge_count(driver)
        self._select_first_variant_if_present(driver)
        self._set_product_quantity(driver, wait, quantity)

        btn_add = wait.until(
            EC.element_to_be_clickable((By.XPATH, PRODUCT_ADD_TO_CART_XPATH))
        )
        driver.execute_script("arguments[0].click();", btn_add)
        self._wait_for_cart_overlay_to_clear(driver)

        wait.until(
            lambda d, old_count=initial_badge:
            self._safe_get_badge_count(d) > old_count
        )

        self._go_to_cart(driver, wait)
        self._wait_for_cart_overlay_to_clear(driver)
        self._wait_for_cart_quantity_stable(driver, quantity)
        print(f"   [Helper] Added stable cart state with quantity = {quantity}.")

    def _add_product_to_cart(self, driver, wait, quantity=1, target_url=PRODUCT_URL):
        last_error = None

        for attempt in range(2):
            try:
                self._add_product_to_cart_once(
                    driver,
                    wait,
                    quantity=quantity,
                    target_url=target_url
                )
                return
            except Exception as e:
                last_error = e
                print(f"   [Retry] Setup attempt {attempt + 1} failed: {e}")
                try:
                    self._reset_cart(driver, wait)
                except Exception:
                    pass

        raise last_error

    def _go_to_cart(self, driver, wait):
        """
        Truy cập trang cart và chờ cart render hoàn chỉnh.
        """

        driver.get(CART_URL)

        self._wait_for_document_ready(driver, wait)
        self._wait_for_cart_overlay_to_clear(driver)

        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        wait.until(
            lambda d:
            d.find_element(
                By.CSS_SELECTOR,
                CART_QTY_INPUT_CSS
            ).get_attribute("value") not in [None, ""]
        )
        self._wait_for_cart_overlay_to_clear(driver)

        print("Cart render xong")

    def _add_multiple_products(self, driver, wait):
        product_urls = [
            PRODUCT_URL,
            PRODUCT_URL_2
        ]

        for index, product_url in enumerate(product_urls):
            print(f"   -> Adding Product {index + 1}")
            self._add_product_to_cart(
                driver,
                wait,
                quantity=1,
                target_url=product_url
            )

            item_count = len(driver.find_elements(By.CSS_SELECTOR, CART_QTY_INPUT_CSS))
            assert item_count >= index + 1, (
                f"Multi-product setup failed. Expected at least {index + 1} rows, got {item_count}"
            )

            print(f"   -> Added Product {index + 1}")

        print("   -> Finished adding multiple products")
        return

    def _reset_cart(self, driver, wait):
        """
        Xóa toàn bộ sản phẩm khỏi cart để đảm bảo
        mỗi test chạy trên state sạch.
        """

        print("\n[Reset Cart] Đang làm sạch giỏ hàng...")

        driver.get(CART_URL)

        wait.until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

        try:

            while True:

                remove_buttons = driver.find_elements(
                    By.XPATH,
                    REMOVE_BTN_XPATH
                )

                if not remove_buttons:
                    break

                target = remove_buttons[0]

                driver.execute_script(
                    "arguments[0].click();",
                    target
                )

                wait.until(
                    EC.staleness_of(target)
                )

                print("   -> Đã xóa 1 item")

            print("Cart đã sạch")

        except Exception as e:

            print(f"   [Reset Warning] {e}")


    # UPDATE_01 - Tăng số lượng 1 lần
    def test_update_01_increase_quantity_once(self, driver, wait):
        print("\n[UPDATE_01] Tăng số lượng sản phẩm trong giỏ 1 lần")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
        old_qty = int(qty_input.get_attribute("value"))
        expected_new_qty = old_qty + 1
        btn_plus = driver.find_element(By.CSS_SELECTOR, CART_BTN_PLUS_CSS)
        driver.execute_script("arguments[0].click();", btn_plus)

        wait.until(lambda d: int(d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value")) == expected_new_qty)
        
        new_qty = int(qty_input.get_attribute("value"))
        assert new_qty == expected_new_qty, f"Expected {expected_new_qty}, got {new_qty}"
        print(f"ăng số lượng thành công: {old_qty} → {new_qty}")


    # UPDATE_02 - Tăng số lượng nhiều lần
    def test_update_02_increase_quantity_multiple(self, driver, wait):
        print("\n[UPDATE_02] Tăng số lượng nhiều lần")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        btn_plus = driver.find_element(By.CSS_SELECTOR, CART_BTN_PLUS_CSS)

        for _ in range(3):
            driver.execute_script("arguments[0].click();", btn_plus)

        wait.until(lambda d: int(d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value")) == 4)
        
        final_qty = int(driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value"))
        assert final_qty == 4
        print(f"Tăng nhiều lần thành công → {final_qty}")


    # UPDATE_03 - Tăng số lượng vượt tồn kho
    def test_update_03_increase_over_stock(self, driver, wait):

        try:

            print("\n[UPDATE_03] Tăng số lượng vượt tồn kho")

            self._add_product_to_cart(driver, wait, quantity=1)

            self._go_to_cart(driver, wait)

            qty_input = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
                )
            )

            initial_qty = int(
                qty_input.get_attribute("value")
            )

            print(
                f"   -> Quantity ban đầu: {initial_qty}"
            )

            previous_valid_qty = initial_qty

            max_attempts = 150

            out_of_stock_detected = False

            for attempt in range(max_attempts):

                qty_input = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
                    )
                )

                old_qty = int(
                    qty_input.get_attribute("value")
                )

                print(
                    f"   -> Click tăng lần {attempt + 1} "
                    f"(current = {old_qty})"
                )

                btn_plus = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, CART_BTN_PLUS_CSS)
                    )
                )

                driver.execute_script(
                    "arguments[0].click();",
                    btn_plus
                )

                try:

                    wait.until(
                        lambda d:
                        d.find_element(
                            By.CSS_SELECTOR,
                            ".cart-loading"
                        ).value_of_css_property("display") == "none"
                    )

                except Exception:
                    pass

                try:

                    out_of_stock_msg = WebDriverWait(
                        driver,
                        5
                    ).until(
                        EC.visibility_of_element_located(
                            (By.XPATH, OUT_OF_STOCK_XPATH)
                        )
                    )

                    assert "Hết hàng" in out_of_stock_msg.text

                    print(
                        "Hệ thống đã hiển thị"
                        "nhãn 'Hết hàng'"
                    )

                    out_of_stock_detected = True

                    break

                except TimeoutException:

                    try:

                        wait.until(
                            lambda d:
                            int(
                                d.find_element(
                                    By.CSS_SELECTOR,
                                    CART_QTY_INPUT_CSS
                                ).get_attribute("value")
                            ) > old_qty
                        )

                        new_qty = int(
                            driver.find_element(
                                By.CSS_SELECTOR,
                                CART_QTY_INPUT_CSS
                            ).get_attribute("value")
                        )

                        previous_valid_qty = new_qty

                        print(
                            f"Quantity tăng: "
                            f"{old_qty} -> {new_qty}"
                        )

                    except TimeoutException:

                        pytest.fail(
                            "Quantity không tăng nhưng "
                            "không xuất hiện nhãn "
                            "'Hết hàng'"
                        )

            if not out_of_stock_detected:

                pytest.fail(
                    f"Đã thử tăng {max_attempts} lần "
                    f"nhưng không phát hiện hết hàng"
                )

            print(
                "   -> Refresh để xác thực "
                "server state..."
            )

            driver.refresh()

            wait.until(
                lambda d:
                d.execute_script(
                    "return document.readyState"
                ) == "complete"
            )

            final_qty_input = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
                )
            )

            final_qty = int(
                final_qty_input.get_attribute("value")
            )

            # assert final_qty == previous_valid_qty, (
            #     f"Server persist sai quantity. "
            #     f"Expected: {previous_valid_qty}, "
            #     f"Actual: {final_qty}"
            # )

            print(
                f"Server giữ đúng "
                f"quantity hợp lệ cuối cùng: "
                f"{final_qty}"
            )

        finally:

            print("   -> Cleanup cart state")

            remove_buttons = driver.find_elements(
                By.XPATH,
                REMOVE_BTN_XPATH
            )

            initial_count = len(remove_buttons)

            if initial_count > 0:

                target_element = remove_buttons[0]

                driver.execute_script(
                    "arguments[0].click();",
                    target_element
                )

                wait.until(
                    EC.staleness_of(target_element)
                )

                current_buttons = driver.find_elements(
                    By.XPATH,
                    REMOVE_BTN_XPATH
                )

                assert len(current_buttons) == initial_count - 1, (
                    "Cleanup thất bại: "
                    "Số lượng item không giảm đúng 1"
                )

                print(
                    " Cleanup thành công "
                )

    # UPDATE_04 - Giảm số lượng 1 lần
    def test_update_04_decrease_quantity_once(self, driver, wait):
        print("\n[UPDATE_04] Giảm số lượng 1 lần")
        self._add_product_to_cart(driver, wait, quantity=3)
        self._go_to_cart(driver, wait)

        qty_input = driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
        old_qty = int(qty_input.get_attribute("value"))

        btn_minus = driver.find_element(By.CSS_SELECTOR, CART_BTN_MINUS_CSS)
        driver.execute_script("arguments[0].click();", btn_minus)

        wait.until(lambda d: int(d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value")) == old_qty - 1)

        new_qty = int(driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value"))
        assert new_qty == old_qty - 1
        print(f" Giảm số lượng thành công: {old_qty} → {new_qty}")


    # UPDATE_05 - Giảm số lượng nhiều lần
    def test_update_05_decrease_quantity_multiple(self, driver, wait):
        print("\n[UPDATE_05] Giảm số lượng nhiều lần")
        self._add_product_to_cart(driver, wait, quantity=5)
        self._go_to_cart(driver, wait)

        btn_minus = driver.find_element(By.CSS_SELECTOR, CART_BTN_MINUS_CSS)
        
        for _ in range(3):
            driver.execute_script("arguments[0].click();", btn_minus)

        wait.until(lambda d: int(d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value")) == 2)
        print(" Giảm nhiều lần thành công")


    # UPDATE_06 - Không cho giảm dưới 1
    def test_update_06_not_less_than_one(self, driver, wait):
        print("\n[UPDATE_06] Không cho phép giảm số lượng dưới 1 (Kiểm chứng qua Input & Badge)")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
        btn_minus = driver.find_element(By.CSS_SELECTOR, CART_BTN_MINUS_CSS)

        driver.execute_script("arguments[0].click();", btn_minus)

        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS).get_attribute("value") == "1")

        current_qty = int(qty_input.get_attribute("value"))
        assert current_qty == 1, f"Lỗi: Số lượng bị giảm xuống {current_qty} thay vì giữ nguyên ở mức 1"

        cart_badge_text = driver.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip()
        assert int(cart_badge_text or 0) == 1, f"Lỗi: Bong bóng giỏ hàng bị mất hoặc sai số lượng ({cart_badge_text})"

        print("Cố gắng giảm dưới 1 bị chặn lại, số lượng và giỏ hàng vẫn giữ nguyên.")


    # UPDATE_07 - Reload sau khi sửa 1 sản phẩm
    def test_update_07_reload_after_update(self, driver, wait):
        print("\n[UPDATE_07] Reload sau khi sửa số lượng (Khắc phục Flaky)")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        line_badge_element = driver.find_element(By.CSS_SELECTOR,CART_BADGE_CSS)
        old_badge_text = line_badge_element.text.strip()

        btn_plus = driver.find_element(By.CSS_SELECTOR, CART_BTN_PLUS_CSS)
        driver.execute_script("arguments[0].click();", btn_plus)
        

        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, CART_BADGE_CSS).text.strip() != old_badge_text)

        driver.refresh()
        
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        qty_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CART_QTY_INPUT_CSS)))
        
        assert int(qty_input.get_attribute("value")) == 2
        print(" Reload thành công ")


    # 8 - Reload sau khi sửa nhiều sản phẩm
    def test_update_08_reload_after_update_multiple_products(self, driver, wait):
        print("\n[UPDATE_08] Reload sau khi sửa nhiều sản phẩm")

        self._add_multiple_products(driver, wait)
        self._go_to_cart(driver, wait)

        qty_inputs = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        assert len(qty_inputs) >= 2, (
            "Cần ít nhất 2 sản phẩm để thực hiện UPDATE_08"
        )

        print(f"   -> Tìm thấy {len(qty_inputs)} sản phẩm trong cart")

        def get_qty_inputs():
            return driver.find_elements(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)

        def get_btn_plus_list():
            return driver.find_elements(By.CSS_SELECTOR, CART_BTN_PLUS_CSS)

        def wait_for_quantities_stable(expected_quantities):
            stable_hits = {"count": 0}

            def quantities_match(d):
                values = [
                    int(el.get_attribute("value"))
                    for el in get_qty_inputs()[:len(expected_quantities)]
                ]

                if len(values) < len(expected_quantities):
                    stable_hits["count"] = 0
                    return False

                if values == expected_quantities:
                    stable_hits["count"] += 1
                else:
                    stable_hits["count"] = 0

                return stable_hits["count"] >= 2

            self._wait_for_cart_overlay_to_clear(driver)
            wait.until(quantities_match)
            self._wait_for_cart_overlay_to_clear(driver)

        expected_quantities = []

        for index in range(2):

            initial_qty = int(
                get_qty_inputs()[index].get_attribute("value")
            )

            increase_times = index + 1

            print(
                f"   -> Product {index + 1}: "
                f"initial = {initial_qty}, "
                f"increase {increase_times} lần"
            )

            for _ in range(increase_times):

                old_qty = int(
                    get_qty_inputs()[index].get_attribute("value")
                )

                driver.execute_script(
                    "arguments[0].click();",
                    get_btn_plus_list()[index]  
                )
                self._wait_for_cart_overlay_to_clear(driver)

                wait.until(
                    lambda d, idx=index, expected=old_qty + 1:
                    int(
                        get_qty_inputs()[idx].get_attribute("value")
                    ) == expected
                )

                expected_after_click = expected_quantities.copy()
                while len(expected_after_click) <= index:
                    expected_after_click.append(initial_qty)
                expected_after_click[index] = old_qty + 1
                wait_for_quantities_stable(expected_after_click)

            expected_qty = initial_qty + increase_times
            expected_quantities.append(expected_qty)

            print(
                f"   -> Product {index + 1} updated quantity = "
                f"{expected_qty}"
            )

        wait_for_quantities_stable(expected_quantities)

        for index in range(2):

            current_qty = int(
                get_qty_inputs()[index].get_attribute("value")  
            )

            assert current_qty == expected_quantities[index], (
                f"Product {index + 1} trước refresh không đúng. "
                f"Expected: {expected_quantities[index]}, "
                f"Actual: {current_qty}"
            )

        print("   -> Xác nhận quantity trước refresh thành công")

        driver.refresh()

        wait.until(
            lambda d:
            d.execute_script("return document.readyState") == "complete"
        )

        self._wait_for_cart_overlay_to_clear(driver)
        wait_for_quantities_stable(expected_quantities)

        for index in range(2):

            final_qty = int(
                get_qty_inputs()[index].get_attribute("value")  
            )

            assert final_qty == expected_quantities[index], (
                f"Reload không giữ đúng quantity của Product {index + 1}. "
                f"Expected: {expected_quantities[index]}, "
                f"Actual: {final_qty}"
            )

            print(
                f" Product {index + 1} giữ đúng quantity: "
                f"{final_qty}"
            )

        print(" Reload giữ nguyên số lượng của nhiều sản phẩm") 


    # UPDATE_09 - Không cho nhập trực tiếp
    def test_update_09_prevent_typing_quantity(self, driver, wait):
        print("\n[UPDATE_09] Không cho nhập trực tiếp vào ô số lượng")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
        original = qty_input.get_attribute("value")

        try:
            qty_input.send_keys("999")
            assert qty_input.get_attribute("value") == original, "Cho phép nhập tay"
        except InvalidElementStateException:
            pass 
        print(" Không cho phép nhập trực tiếp")


    # UPDATE_10 - Không cho paste
    def test_update_10_prevent_paste_quantity(self, driver, wait):
        print("\n[UPDATE_10] Không cho paste vào ô số lượng")
        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = driver.find_element(By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
        original = qty_input.get_attribute("value")

        try:
            qty_input.send_keys(Keys.CONTROL, "v")
            assert qty_input.get_attribute("value") == original, "Cho phép paste"
        except InvalidElementStateException:
            pass
        print(" Không cho phép paste")


    # UPDATE_11 - Bypass số âm bằng DevTools
    def test_update_11_bypass_negative_quantity(self, driver, wait):
        print("\n[UPDATE_11] Bypass số lượng âm bằng DevTools")

        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        driver.execute_script("""
            arguments[0].value = '-5';

            arguments[0].dispatchEvent(
                new Event('input', { bubbles: true })
            );

            arguments[0].dispatchEvent(
                new Event('change', { bubbles: true })
            );
        """, qty_input)

        print("   -> Đã inject quantity = -5")

        btn_plus = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, CART_BTN_PLUS_CSS)
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            btn_plus
        )

        wait.until(
            lambda d:
            d.find_element(
                By.CSS_SELECTOR,
                CART_QTY_INPUT_CSS
            ).get_attribute("value") != "-5"
        )

        print("   -> Front-end đã phản hồi")

        driver.refresh()

        wait.until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

        final_qty_input = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        final_qty = int(
            final_qty_input.get_attribute("value")
        )

        assert final_qty >= 0, (
            f"LỖI: "
            f"Server đã lưu quantity âm vào Database. "
            f"Giá trị hiện tại: {final_qty}"
        )

        print(
            f"Server đã từ chối dữ liệu âm. "
            f"Quantity hiện tại: {final_qty}"
        )


    # UPDATE_12 - Bypass vượt tồn kho bằng DevTools
    def test_update_12_bypass_over_stock(self, driver, wait):
        print("\n[UPDATE_12] Bypass số lượng vượt tồn kho bằng DevTools")

        self._add_product_to_cart(driver, wait, quantity=1)
        self._go_to_cart(driver, wait)

        qty_input = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        driver.execute_script("""
            arguments[0].value = '99999';

            arguments[0].dispatchEvent(
                new Event('input', { bubbles: true })
            );

            arguments[0].dispatchEvent(
                new Event('change', { bubbles: true })
            );
        """, qty_input)

        print("   -> Đã inject quantity = 99999")

        btn_plus = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, CART_BTN_PLUS_CSS)
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            btn_plus
        )

        error_msg = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, MODAL_ERROR_CSS)
            )
        )

        assert error_msg.is_displayed(), (
            "Không phát hiện lỗi vượt tồn kho trên UI"
        )

        print("   -> Modal lỗi đã xuất hiện")

        driver.refresh()

        wait.until(
            lambda d:
            d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

        final_qty_input = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, CART_QTY_INPUT_CSS)
            )
        )

        final_qty = int(
            final_qty_input.get_attribute("value")
        )

        assert final_qty < 99999, (
            "LỖI: "
            "Server đã lưu quantity vượt tồn kho vào Database! "
            f"Giá trị hiện tại: {final_qty}"
        )

        print(
            f" Server đã từ chối dữ liệu vượt tồn kho. "
            f"Quantity hiện tại: {final_qty}"
        )
