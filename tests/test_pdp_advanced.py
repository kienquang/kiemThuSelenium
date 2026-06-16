import time
import re
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PRODUCT_URL = "https://icondenim.com/products/ao-so-mi-nam-tay-ngan-sandstorm-form-relaxed"

def extract_number(text):
    if not text:
        return 0
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(''.join(numbers))
    return 0

@pytest.fixture(autouse=True, scope="module")
def setup_advanced_pdp(driver):
    driver.get(PRODUCT_URL)
    time.sleep(2)

def test_tc_pdp_002_validate_currency_format(driver):
    wait = WebDriverWait(driver, 10)
    
    current_price_el = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//span[contains(@class, 'current-price') or contains(@class, 'price')]")
    ))
    price_text = current_price_el.text
    
    valid_symbols = ["đ", "₫", "vnd"]
    has_valid_currency = any(symbol in price_text.lower() for symbol in valid_symbols)
    
    assert has_valid_currency, f" Giá tiền không có định dạng tiền tệ hợp lệ ({price_text})"

def test_tc_pdp_003_validate_gallery_thumbnail_click(driver):
    wait = WebDriverWait(driver, 10)
    
    try:
        css_thumbnails = "#slider-thumb .slick-slide:not(.slick-cloned), .product-gallery__thumb:not(.slick-cloned)"
        all_thumbnails = driver.find_elements(By.CSS_SELECTOR, css_thumbnails)
        
        visible_thumbs = [thumb for thumb in all_thumbnails if thumb.is_displayed()]
        
        if len(visible_thumbs) > 1:
            css_main_image = ".slick-current img.product-image-feature, div#slider-product .slick-current img, .slick-current img#product-featured-image, .product-gallery__image img, .main-image img"
            
            main_image = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_main_image)))
            old_src = main_image.get_attribute("src")
            
            is_changed = False
            
            for target_thumb in visible_thumbs[1:]:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_thumb)
                driver.execute_script("arguments[0].style.border = '3px solid red';", target_thumb)
                time.sleep(1)
                
                try:
                    clickable_child = target_thumb.find_element(By.CSS_SELECTOR, "a, img")
                    driver.execute_script("arguments[0].click();", clickable_child)
                except:
                    driver.execute_script("arguments[0].click();", target_thumb)
                
                try:
                    def check_image_changed(d):
                        try:
                            curr_src = d.find_element(By.CSS_SELECTOR, css_main_image).get_attribute("src")
                            return curr_src != old_src and curr_src is not None
                        except:
                            return False
                            
                    WebDriverWait(driver, 3).until(check_image_changed)
                    is_changed = True
                    break 
                except:
                    pass 
            
            assert is_changed, "Đã click qua các Thumbnail nhưng hình ảnh lớn ở giữa không chịu đổi URL"
        else:
            pytest.skip(f"Bot quét thấy {len(all_thumbnails)} ảnh trong DOM nhưng chỉ có {len(visible_thumbs)} ảnh hiển thị hợp lệ.")
            
    except Exception as e:
        pytest.fail(f"Lỗi hệ thống khi tương tác thư viện ảnh: {e}")

def test_tc_pdp_016_validate_related_products_navigation(driver):
    wait = WebDriverWait(driver, 15)
    
    if driver.current_url != PRODUCT_URL:
        driver.get(PRODUCT_URL)
        time.sleep(1)
        
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.75);")
    time.sleep(2) 
    
    try:
        css_selector = "div.item-slider.slick-active[aria-hidden='false'] a[href]"
        valid_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        
        target_link = valid_links[0]
        expected_url = target_link.get_attribute("href")
        
        driver.execute_script("arguments[0].click();", target_link)
        wait.until(EC.url_contains(expected_url.split('/')[-1]))
        
    except Exception as e:
        pytest.fail(f"Không thể click vào sản phẩm liên quan: {e}")

def test_tc_pdp_015_validate_cart_accumulation(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(PRODUCT_URL)
    time.sleep(1.5)
    
    try:
        badge = driver.find_element(By.CSS_SELECTOR, "span.number-cart")
        initial_count = extract_number(badge.text)
    except:
        initial_count = 0
    
    size_selector = "div.is-size label, div.swatch-element.is-size label"
    btn_add_xpath = "//button[@id='add-to-cart'] | //button[contains(., 'THÊM VÀO GIỎ')]"
    
    try:
        size_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, size_selector)))
        valid_sizes = [label for label in size_labels if label.is_displayed()]
        if len(valid_sizes) > 1:
            driver.execute_script("arguments[0].click();", valid_sizes[1])
            time.sleep(0.5)
    except: pass 
    
    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, btn_add_xpath)))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3) 
    
    driver.get(PRODUCT_URL)
    time.sleep(1.5)
    try:
        size_labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, size_selector)))
        valid_sizes = [label for label in size_labels if label.is_displayed()]
        if len(valid_sizes) > 2:
            driver.execute_script("arguments[0].click();", valid_sizes[2])
        elif len(valid_sizes) > 1:
            driver.execute_script("arguments[0].click();", valid_sizes[1])
        time.sleep(0.5)
    except: pass

    btn_add = wait.until(EC.presence_of_element_located((By.XPATH, btn_add_xpath)))
    driver.execute_script("arguments[0].click();", btn_add)
    time.sleep(3)
    
    try:
        badge_after = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.number-cart")))
        final_count = extract_number(badge_after.text)
        
        assert final_count >= initial_count + 2, f"Badge giỏ hàng không cộng dồn đúng"
        
    except Exception as e:
        pytest.fail(f"Lỗi kiểm thử giỏ hàng: {e}")