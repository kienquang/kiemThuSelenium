import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

def test_pdp_store_location_text(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    
    try:
        time.sleep(2)
        
        info_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.location-store span, div.localtion-info span")))
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", info_span)
        driver.execute_script("arguments[0].style.border = '2px solid red';", info_span)
        
        text_content = info_span.text.strip()
        
        assert "cửa hàng" in text_content.lower() or "hết hàng" in text_content.lower(), \
            f" Text thông báo tồn kho cửa hàng sai định dạng ({text_content})"
            
    except Exception as e:
        pytest.fail(f"Lỗi khi tìm text thông báo cửa hàng: {e}")

def test_pdp_store_location_expand_and_count(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(2) 
    
    try:
        info_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.location-store span")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", info_span)
        
        text_content = info_span.text
        numbers = re.findall(r'\d+', text_content)
        expected_count = int(numbers[0]) if numbers else 0
        
        if expected_count == 0:
            pytest.skip("Sản phẩm hết hàng tại các chi nhánh.")

        toggle_btn = driver.find_element(By.CSS_SELECTOR, "button#toggle-location, div.location-store")
        driver.execute_script("arguments[0].click();", toggle_btn)
        time.sleep(1.5) 
        
        all_store_containers = driver.find_elements(By.CSS_SELECTOR, "div.store-container")
        total_dom_count = len(all_store_containers)
        
        if total_dom_count > 0 and total_dom_count == expected_count * 2:
            actual_count = int(total_dom_count / 2)
        else:
            actual_count = total_dom_count
        
        assert expected_count == actual_count, f"Bên ngoài báo {expected_count} nhưng bên trong tính ra {actual_count}!"
        
    except Exception as e:
        pytest.fail(f"Lỗi kịch bản đếm cửa hàng: {e}")

def test_pdp_store_location_data_attributes(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(2)
    
    try:
        toggle_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button#toggle-location, div.location-store")))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", toggle_btn)
        driver.execute_script("arguments[0].click();", toggle_btn)
        time.sleep(1.5)
        
        all_store_containers = driver.find_elements(By.CSS_SELECTOR, "div.store-container")
        if len(all_store_containers) > 0:
            half_length = int(len(all_store_containers) / 2) if len(all_store_containers) >= 2 else len(all_store_containers)
            valid_stores = all_store_containers[:half_length]
        else:
            valid_stores = []
             
        assert len(valid_stores) > 0, "Không lấy được danh sách cửa hàng hợp lệ nào"
        
        check_limit = min(3, len(valid_stores))
        for i in range(check_limit):
            store = valid_stores[i]
            tinh = store.get_attribute("data-tinh")
            quan = store.get_attribute("data-quan")
            
            assert tinh and tinh.strip() != "", f"BUG DATA: Cửa hàng thứ {i+1} mất dữ liệu Tỉnh!"
            assert quan and quan.strip() != "", f"BUG DATA: Cửa hàng thứ {i+1} mất dữ liệu Quận!"
            
    except Exception as e:
        pytest.fail(f"Lỗi kiểm tra dữ liệu cửa hàng: {e}")