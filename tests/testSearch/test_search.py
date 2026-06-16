import logging
import time
import pytest
from unidecode import unidecode  # IMPORT THƯ VIỆN UNIDECODE

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    UnexpectedAlertPresentException,
)

from tests.testSearch.test_data import TEST_CASES
from tests.testSearch.search_helpers import (
    BASE_URL,
    SEARCH_BUTTON_LOCATORS,
    SEARCH_INPUT_LOCATORS,
    _get_result_product_names,  # Gọi đúng tên hàm helper của bạn
    _dismiss_any_alert,
    _scroll_to_top,
    _find_first_clickable,
    _wait_for_search_panel,
    _find_first_visible,
    _focus_input,
    _clear_input,
    _type_with_alert_watch,
    _try_submit_search,
    _wait_for_outcome,
    _resolve_empty_query_outcome,
    _capture_debug_artifacts
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

test_names = [case["name"] for case in TEST_CASES]

@pytest.mark.parametrize("case", TEST_CASES, ids=test_names)
def test_search_multiple_cases(driver, case):
    wait = WebDriverWait(driver, 15)
    logger.info("=== START case: %s ===", case["name"])
    logger.debug("Query: '%s' | Expected: %s", case["query"], case["expected"])

    _dismiss_any_alert(driver)

    driver.get(BASE_URL)
    driver.delete_all_cookies()
    wait.until(lambda d: d.find_element(By.TAG_NAME, "body").is_displayed())
    _scroll_to_top(driver)

    search_button = _find_first_clickable(driver, wait, SEARCH_BUTTON_LOCATORS, "search button")
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", search_button)
    _wait_for_search_panel(driver, wait)

    search_input = _find_first_visible(driver, wait, SEARCH_INPUT_LOCATORS, "search input")
    _focus_input(driver, search_input)
    _clear_input(search_input)

    outcome = None
    elements = []

    if case["query"]:
        alert_fired, alert_text = _type_with_alert_watch(driver, search_input, case["query"])
        if alert_fired:
            logger.info("Mid-typing alert detected → outcome=validation. Alert: %s", alert_text)
            outcome = "validation"

    if outcome is None:
        try:
            search_input.send_keys(Keys.ENTER)
        except UnexpectedAlertPresentException:
            caught, alert_text = _dismiss_any_alert(driver, timeout=1)
            logger.info("Alert on ENTER key: %s", alert_text)
            outcome = "validation"

        if outcome is None:
            _try_submit_search(driver)
            try:
                outcome, elements = _wait_for_outcome(wait)
            except UnexpectedAlertPresentException:
                caught, alert_text = _dismiss_any_alert(driver, timeout=1)
                logger.info("Alert during _wait_for_outcome: %s", alert_text)
                outcome = "validation"
            except TimeoutException:
                if case["query"] == "":
                    outcome, elements = _resolve_empty_query_outcome(driver)
                else:
                    _capture_debug_artifacts(driver, case["name"])
                    raise

    if outcome == "results":
        logger.info("[PASSED] %s result items found.", len(elements))
    elif outcome == "no_results":
        logger.info("[PASSED] No-results message displayed.")
    else:
        logger.info("[PASSED] Validation behaviour confirmed.")

    assert outcome in case["expected"], (
        f"[{case['name']}] Expected one of {case['expected']}, got '{outcome}'"
    )

    if outcome == "results" and case["name"] in ["valid_keyword", "valid_keyword_vietnamese", "empty_space_start_end"]:
        actual_names = _get_result_product_names(driver)
        assert actual_names, "LỖI: Kết quả trả về 'results' nhưng mảng sản phẩm rỗng."
        
        clean_query = unidecode(case["query"].lower().strip())
        query_words = clean_query.split()

        has_at_least_one_correct_product = any(
            all(word in unidecode(name.lower().strip()) for word in query_words)
            for name in actual_names
        )
        
        if not has_at_least_one_correct_product:
            print(f"\n[FAIL] Không có bất kỳ sản phẩm nào trong danh sách {actual_names} liên quan đến từ khóa '{case['query']}'")

        assert has_at_least_one_correct_product, (
            f"LỖI: Trang tìm kiếm không trả về bất kỳ sản phẩm nào "
            f"khớp với từ khóa '{case['query']}'."
        )
        
        logger.info("[PASSED] Đã xác nhận có sản phẩm khớp với từ khóa tìm kiếm hiển thị trên giao diện.")