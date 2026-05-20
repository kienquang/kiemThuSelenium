from selenium import webdriver

# Selenium 4 tự động tìm và cấu hình ChromeDriver phù hợp với Chrome v148 của bạn
driver = webdriver.Chrome()

# Thử nghiệm truy cập trang web
driver.get("https://topcv.vn")
print("Tiêu đề trang:", driver.title)

# Giữ trình duyệt lại 5 giây để bạn kịp nhìn, tránh việc "chớp mắt rồi tắt ngay"
import time
time.sleep(5)

driver.quit()