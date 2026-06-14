import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

# =====================================================================
# TC_STORE_01: Kiểm tra thông báo số lượng cửa hàng còn hàng
# =====================================================================
def test_pdp_store_location_text(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Store Location] Kịch bản 1: Kiểm tra dòng text báo số lượng cửa hàng...")
    driver.get(PRODUCT_URL)
    
    try:
        # Chờ 2 giây để AJAX call API tồn kho xong xuôi, tránh bị Re-render làm chết Element
        time.sleep(2)
        
        # Bắt đầu tìm thẻ sau khi web đã ổn định
        info_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.location-store span, div.localtion-info span")))
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", info_span)
        driver.execute_script("arguments[0].style.border = '2px solid red';", info_span)
        
        # FIX STALE ELEMENT: Lấy text ngay lập tức mà không sleep
        text_content = info_span.text.strip()
        print(f"   + Tìm thấy dòng thông báo: '{text_content}'")
        
        assert "cửa hàng" in text_content.lower() or "hết hàng" in text_content.lower(), \
            f"BUG UI: Text thông báo tồn kho cửa hàng sai định dạng ({text_content})"
            
        print("   + [PASSED] Định dạng text tồn kho hiển thị chuẩn xác.")
        
    except Exception as e:
        pytest.fail(f"Lỗi khi tìm text thông báo cửa hàng: {e}")

# =====================================================================
# TC_STORE_02: Mở danh sách và đối chiếu số lượng cửa hàng thực tế
# =====================================================================
def test_pdp_store_location_expand_and_count(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Store Location] Kịch bản 2: Đếm đối chiếu danh sách cửa hàng...")
    driver.get(PRODUCT_URL)
    time.sleep(2) 
    
    try:
        # 1. Lấy số trên Text
        info_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.location-store span")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", info_span)
        
        text_content = info_span.text
        numbers = re.findall(r'\d+', text_content)
        expected_count = int(numbers[0]) if numbers else 0
        print(f"   + Theo thông báo, số lượng cửa hàng dự kiến là: {expected_count}")
        
        if expected_count == 0:
            pytest.skip("Sản phẩm hết hàng tại các chi nhánh.")

        # 2. Bấm nút Mở rộng
        toggle_btn = driver.find_element(By.CSS_SELECTOR, "button#toggle-location, div.location-store")
        driver.execute_script("arguments[0].click();", toggle_btn)
        time.sleep(1.5) 
        
        # 3. ĐẾM THẲNG TỪ DOM (TOÁN HỌC BÙ TRỪ)
        all_store_containers = driver.find_elements(By.CSS_SELECTOR, "div.store-container")
        total_dom_count = len(all_store_containers)
        
        # Nếu tổng số thẻ gấp đôi con số dự kiến (Bản PC + Bản Mobile)
        if total_dom_count > 0 and total_dom_count == expected_count * 2:
            actual_count = int(total_dom_count / 2)
            print(f"   + [INFO] Web sinh ra {total_dom_count} thẻ (PC + Mobile). Đã lọc lấy {actual_count} thẻ hợp lệ.")
        else:
            actual_count = total_dom_count
            print(f"   + Thực tế DOM sinh ra {actual_count} thẻ cửa hàng.")
        
        assert expected_count == actual_count, f"BUG LOGIC DATA: Bên ngoài báo {expected_count} nhưng bên trong tính ra {actual_count}!"
        print("   + [PASSED] Dữ liệu số lượng cửa hàng khớp nhau 100%.")
        
    except Exception as e:
        pytest.fail(f"Lỗi kịch bản đếm cửa hàng: {e}")

# =====================================================================
# TC_STORE_03: Kiểm tra tính toàn vẹn của Dữ liệu Tỉnh/Quận
# =====================================================================
def test_pdp_store_location_data_attributes(driver):
    wait = WebDriverWait(driver, 10)
    print("\n[Store Location] Kịch bản 3: Kiểm tra thuộc tính Dữ liệu Tỉnh/Quận của cửa hàng...")
    driver.get(PRODUCT_URL)
    time.sleep(2)
    
    try:
        toggle_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button#toggle-location, div.location-store")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", toggle_btn)
        driver.execute_script("arguments[0].click();", toggle_btn)
        time.sleep(1.5)
        
        # Cắt lấy 1 nửa danh sách nếu web nhân đôi DOM
        all_store_containers = driver.find_elements(By.CSS_SELECTOR, "div.store-container")
        if len(all_store_containers) > 0:
            half_length = int(len(all_store_containers) / 2) if len(all_store_containers) >= 2 else len(all_store_containers)
            valid_stores = all_store_containers[:half_length]
        else:
            valid_stores = []
             
        assert len(valid_stores) > 0, "BUG FAILED THẬT: Không lấy được danh sách cửa hàng hợp lệ nào!"
        
        check_limit = min(3, len(valid_stores))
        for i in range(check_limit):
            store = valid_stores[i]
            tinh = store.get_attribute("data-tinh")
            quan = store.get_attribute("data-quan")
            print(f"   + Check Item {i+1}: Tỉnh/TP = '{tinh}' | Quận/Huyện = '{quan}'")
            
            assert tinh and tinh.strip() != "", f"BUG DATA: Cửa hàng thứ {i+1} mất dữ liệu Tỉnh!"
            assert quan and quan.strip() != "", f"BUG DATA: Cửa hàng thứ {i+1} mất dữ liệu Quận!"
            
        print("   + [PASSED] Dữ liệu địa chỉ (Tỉnh/Quận) của các cửa hàng hợp lệ.")
        
    except Exception as e:
        pytest.fail(f"Lỗi kiểm tra dữ liệu cửa hàng: {e}")