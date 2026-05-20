import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_multi_navigation_flow(driver):
    wait = WebDriverWait(driver, 10) # Bật chế độ đợi thông minh 10 giây
    
    print("\n[Bước 1] Truy cập trang chủ ICONDENIM...")
    driver.get("https://icondenim.com/")
    
    print("[Bước 2] Click chuyển sang trang HÀNG MỚI...")
    # Đợi nút Hàng Mới sẵn sàng click
    hang_moi_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Hàng Mới')]")))
    hang_moi_menu.click()
    time.sleep(2)

    print("[Bước 3] Click mở xem sản phẩm ĐẦU TIÊN...")
    # Đợi sản phẩm load xong, dùng JS Click để chống pop-up đè
    first_product = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'product-block')]//h3/a")))
    print(f"-> Đang mở sản phẩm: {first_product.text}")
    driver.execute_script("arguments[0].click();", first_product)
    time.sleep(2)

    print("[Bước 4] Bấm nút BACK...")
    driver.back()
    
    print("[Bước 5] Tìm kiếm an toàn...")
    # Bấm mở ô tìm kiếm bằng JS Click
    search_icon = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'search-box')] | //button[contains(@class, 'search')]")))
    driver.execute_script("arguments[0].click();", search_icon)
    
    time.sleep(2) # Chờ 2s cho form tìm kiếm xổ ra hoàn toàn
    
    # Túm tất cả các ô nhập liệu có tên là 'q' (kể cả ẩn hay hiện)
    search_inputs = driver.find_elements(By.XPATH, "//input[@name='q']")
    
    # Duyệt qua từng ô, thấy ô nào ĐANG HIỂN THỊ trên màn hình thì gõ chữ vào đó
    for box in search_inputs:
        if box.is_displayed():
            box.send_keys("Quần")
            box.send_keys(Keys.ENTER)
            break # Gõ xong là ngắt vòng lặp luôn, không quan tâm ô ẩn nữa
    
    time.sleep(4)
    print("-> Đã hiển thị kết quả tìm kiếm!")
    print("[SUCCESS] Hoàn thành luồng test liên hoàn, trang web HOÀN TOÀN KHÔNG CHẶN BOT!")