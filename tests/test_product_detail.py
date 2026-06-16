import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from tests.test_pdp_advanced import extract_number

PRODUCT_URL = "https://icondenim.com/products/ao-thun-nam-seminal-form-boxy"

@pytest.fixture(autouse=True, scope="module")
def setup_basic_pdp(driver):
    driver.get(PRODUCT_URL)
    time.sleep(2)

def test_tc_pdp_001_hien_thi_thong_tin_co_ban(driver):
    wait = WebDriverWait(driver, 10)
    try:
        title = wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
        price = driver.find_element(By.XPATH, "//span[contains(@class, 'price') or contains(@class, 'current-price')]")
        assert title.text.strip() != "", "Lỗi: Không hiển thị tên sản phẩm"
        assert price.text.strip() != "", "Lỗi: Không hiển thị giá sản phẩm"
    except Exception as e:
        pytest.fail(f"Lỗi hiển thị UI: {e}")

def test_tc_pdp_004_chuyen_doi_tab_thong_tin(driver):
    wait = WebDriverWait(driver, 10)
    try:
        tab_delivery = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'nav-tabs')]//li[2] | //div[contains(@class, 'tab')][2]")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tab_delivery)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", tab_delivery)
        time.sleep(0.5)
        panel_active = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".tab-pane.active, .tab-content .active")
        ))
        assert panel_active.text.strip() != "", "Nội dung tab không hiển thị"
    except Exception:
        pytest.skip("Giao diện không có cấu trúc Tab truyền thống để test.")

def test_tc_pdp_005_tang_so_luong(driver):
    wait = WebDriverWait(driver, 10)
    try:
        btn_plus = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'plus') or contains(@class, 'add')] | //input[contains(@class, 'plus')] | //div[contains(@class, 'qtyplus')]")))
        input_qty = wait.until(EC.presence_of_element_located((By.ID, "quantity")))
        driver.execute_script("arguments[0].value = '1';", input_qty)
        driver.execute_script("arguments[0].click();", btn_plus)
        time.sleep(0.5) 
        driver.execute_script("arguments[0].click();", btn_plus)
        time.sleep(0.5)
        qty_value = int(input_qty.get_attribute("value"))
        assert qty_value >= 3, f"BUG UI: Nút Tăng Số Lượng (+) không hoạt động! (Giá trị hiện tại: {qty_value})"
    except Exception as e:
        pytest.fail(f"Lỗi tương tác nút (+): {e}")

def test_tc_pdp_006_giam_so_luong_am(driver):
    wait = WebDriverWait(driver, 10)
    try:
        btn_minus = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'minus') or contains(@class, 'sub')] | //input[contains(@class, 'minus')] | //div[contains(@class, 'qtyminus')]")))
        input_qty = wait.until(EC.presence_of_element_located((By.ID, "quantity")))
        for _ in range(5):
             driver.execute_script("arguments[0].click();", btn_minus)
             time.sleep(0.2)
        qty_value_after = int(input_qty.get_attribute("value"))
        assert qty_value_after >= 1, "BUG BẢO MẬT: Nút Giảm (-) cho phép hạ xuống số âm!"
    except Exception as e:
        pytest.fail(f"Lỗi: {e}")

def test_tc_pdp_007_thay_doi_bien_the_size(driver):
    wait = WebDriverWait(driver, 10)
    try:
        css_selector = ".swatch-element label, .select-swap .swap-elements label, .variant-swatch label"
        swatch_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        valid_labels = [label for label in swatch_labels if label.text.strip() != "" and label.is_displayed()]
        if len(valid_labels) > 1:
            target_label = valid_labels[1] 
            driver.execute_script("arguments[0].style.border = '3px solid red';", target_label)
            time.sleep(1) 
            driver.execute_script("arguments[0].click();", target_label)
            time.sleep(1) 
            class_attr = target_label.get_attribute("class") 
            assert "sd" in class_attr.split(), "Size không được chọn "
        else:
             pytest.skip("Sản phẩm không có nhiều tuỳ chọn Size/Màu để đổi.")
    except Exception as e:
         pytest.fail(f"BUG UI: Không thể click đổi Variant. Lỗi: {e}")

def test_tc_pdp_012_bat_loi_quen_chon_size(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(1.5)
    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
        initial_count = extract_number(badge.text)
    except:
        initial_count = 0
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn_add)
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(2)
    badge_after = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
    final_count = extract_number(badge_after.text)
    
    assert final_count == initial_count + 1, \
        f"Giỏ hàng không tăng"

def test_tc_pdp_013_them_vao_gio_hang(driver):
    wait = WebDriverWait(driver, 10)
    try:
        size_l = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.is-size label, .swatch-element label")))
        driver.execute_script("arguments[0].click();", size_l)
        time.sleep(0.5)
    except:
        pass
    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
        initial_count = extract_number(badge.text)
    except:
        initial_count = 0
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]")))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3)
    badge_after = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
    final_count = extract_number(badge_after.text)
    assert final_count == initial_count + 1, \
        f"Giỏ hàng không tăng"

def test_tc_pdp_014_mua_ngay_chuyen_huong(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(1.5)
    try:
        size_m = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.is-size label, .swatch-element label")))
        driver.execute_script("arguments[0].click();", size_m)
        time.sleep(0.5)
    except:
        pass
    btn_buy_now = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@id='buy-now'] | //button[contains(., 'MUA NGAY')]")))
    driver.execute_script("arguments[0].click();", btn_buy_now)
    time.sleep(4)
    current_url = driver.current_url.lower()
    if "checkout" not in current_url and "cart" not in current_url:
        pytest.fail("Lỗi: Nút Mua Ngay không hoạt động hoặc không chuyển trang!")

@pytest.mark.parametrize("invalid_input", [
    ("0"),       
    ("-5"),      
    ("abc"),     
    ("@#$")      
])
def test_tc_pdp_data_driven_quantity_input(driver, invalid_input):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(1)
    input_qty = wait.until(EC.presence_of_element_located((By.ID, "quantity")))
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", input_qty)
    input_qty.send_keys(Keys.CONTROL + "a")
    input_qty.send_keys(Keys.BACKSPACE)
    time.sleep(0.5)
    input_qty.send_keys(invalid_input)
    input_qty.send_keys(Keys.ENTER)
    time.sleep(1)
    current_value = input_qty.get_attribute("value")
    try:
        numeric_value = int(current_value)
        assert numeric_value >= 1, f"BUG BẢO MẬT: Web nhận số lượng = {numeric_value}"
    except ValueError:
        pytest.fail(f"BUG UI: Ô số lượng đang cho phép nhập chữ/ký tự: '{current_value}'")