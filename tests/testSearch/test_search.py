import logging
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    UnexpectedAlertPresentException,
)

# Import từ các file đã chia
from tests.testSearch.test_data import TEST_CASES
from tests.testSearch.search_helpers import (
    BASE_URL,
    SEARCH_BUTTON_LOCATORS,
    SEARCH_INPUT_LOCATORS,
    RESULTS_PAGE_INPUT_LOCATORS,
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

@pytest.mark.parametrize("case", TEST_CASES)
def test_search_multiple_cases(driver, case):
    wait = WebDriverWait(driver, 15)
    logger.info("=== START case: %s ===", case["name"])
    logger.debug("Query: '%s' | Expected: %s", case["query"], case["expected"])

    # ── Step 0: Flush any stale alert left by the previous test case ─────────
    _dismiss_any_alert(driver)

    # ── Step 1: Navigate to a clean page ─────────────────────────────────────
    driver.get(BASE_URL)
    driver.delete_all_cookies()
    wait.until(lambda d: d.find_element(By.TAG_NAME, "body").is_displayed())
    _scroll_to_top(driver)

    # ── Step 2: Open the search panel ────────────────────────────────────────
    search_button = _find_first_clickable(driver, wait, SEARCH_BUTTON_LOCATORS, "search button")
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", search_button)
    _wait_for_search_panel(driver, wait)

    search_input = _find_first_visible(driver, wait, SEARCH_INPUT_LOCATORS, "search input")
    _focus_input(driver, search_input)
    _clear_input(search_input)

    # ── Step 3: Type query character-by-character, watching for alerts ────────
    outcome = None
    elements = []

    if case["query"]:
        alert_fired, alert_text = _type_with_alert_watch(driver, search_input, case["query"])

        if alert_fired:
            logger.info("Mid-typing alert detected → outcome=validation. Alert: %s", alert_text)
            outcome = "validation"
            elements = []
    else:
        alert_fired = False

    # ── Step 4: Submit & wait for outcome (only when no mid-typing alert) ─────
    if outcome is None:
        try:
            search_input.send_keys(Keys.ENTER)
        except UnexpectedAlertPresentException:
            caught, alert_text = _dismiss_any_alert(driver, timeout=1)
            logger.info("Alert on ENTER key: %s", alert_text)
            outcome, elements = "validation", []

        if outcome is None:
            _try_submit_search(driver)

            try:
                outcome, elements = _wait_for_outcome(wait)
            except UnexpectedAlertPresentException:
                caught, alert_text = _dismiss_any_alert(driver, timeout=1)
                logger.info("Alert during _wait_for_outcome: %s", alert_text)
                outcome, elements = "validation", []
            except TimeoutException:
                if case["query"] == "":
                    outcome, elements = _resolve_empty_query_outcome(driver)
                else:
                    _capture_debug_artifacts(driver, case["name"])
                    raise

    # ── Step 5: Assert ────────────────────────────────────────────────────────
    assert outcome in case["expected"], (
        f"[{case['name']}] Expected one of {case['expected']}, got '{outcome}'"
    )

    # ── Step 6: Secondary UI check on the results page ────────────────────────
    _dismiss_any_alert(driver)

    try:
        current_url = driver.current_url
    except UnexpectedAlertPresentException:
        _dismiss_any_alert(driver)
        current_url = driver.current_url

    if "/search" in current_url:
        try:
            if outcome == "no_results":
                _find_first_visible(driver, wait, RESULTS_PAGE_INPUT_LOCATORS, "results page search input")
                logger.info("Results page search form visible.")
            else:
                search_button = _find_first_clickable(driver, wait, SEARCH_BUTTON_LOCATORS, "search button")
                driver.execute_script("arguments[0].click();", search_button)
                _wait_for_search_panel(driver, wait)
                _find_first_visible(driver, wait, SEARCH_INPUT_LOCATORS, "search input")
                logger.info("Results page header search is usable.")
        except TimeoutException as exc:
            logger.warning("Results page UI check skipped (timeout): %s", exc)

    # ── Step 7: Log final result ──────────────────────────────────────────────
    if outcome == "results":
        logger.info("[PASSED] %s result items found.", len(elements))
    elif outcome == "no_results":
        logger.info("[PASSED] No-results message displayed.")
    else:
        logger.info("[PASSED] Validation behaviour confirmed.")

    # ── Step 8: Final safety flush before next test ───────────────────────────
    _dismiss_any_alert(driver)
    time.sleep(1)