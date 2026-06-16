import logging
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    UnexpectedAlertPresentException,
)

BASE_URL = "https://icondenim.com/"

logger = logging.getLogger(__name__)


SEARCH_BUTTON_LOCATORS = [
    (By.CSS_SELECTOR, "a.search.toggle_form_search"),
]
SEARCH_PANEL_LOCATORS = [
    (By.CSS_SELECTOR, "#header-search.active"),
]
SEARCH_INPUT_LOCATORS = [
    (By.CSS_SELECTOR, "input.searchinput.input-search.search-input"),
]
RESULTS_PAGE_INPUT_LOCATORS = [
    (By.CSS_SELECTOR, "form.search-page input[name='q']"),
    (By.CSS_SELECTOR, "form.search-page input.searchinput.input-search.search-input"),
]
SEARCH_SUBMIT_LOCATORS = [
    (By.ID, "search-header-btn"),
    (By.CSS_SELECTOR, "form.wanda-mxm-search button[type='submit']"),
]
RESULT_ITEM_LOCATORS = [
    (By.CSS_SELECTOR, ".content-product-list.product-list > div"),
]
NO_RESULTS_LOCATORS = [
    (By.CSS_SELECTOR, ".heading-page.text-center"),
]
VALIDATION_LOCATORS = [
    (By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'please enter')]"),
]



def _locator_to_str(locator):
    return f"{locator[0]} -> {locator[1]}"

def _dismiss_any_alert(driver, timeout=2):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        logger.info("Dismissed alert: %s", alert_text)
        return True, alert_text
    except Exception:
        return False, None

def _find_first(driver, wait, locators, label, predicate):
    logger.debug("Finding %s", label)

    def _check(_driver):
        for locator in locators:
            elements = _driver.find_elements(*locator)
            if not elements:
                continue
            for element in elements:
                if predicate(element):
                    logger.debug("Matched %s using locator: %s", label, _locator_to_str(locator))
                    return element
        return False

    try:
        return wait.until(_check)
    except TimeoutException as exc:
        raise TimeoutException(f"Timeout: Could not find {label}") from exc

def _find_first_clickable(driver, wait, locators, label):
    return _find_first(driver, wait, locators, label,
                       lambda el: el.is_displayed() and el.is_enabled())

def _find_first_visible(driver, wait, locators, label):
    return _find_first(driver, wait, locators, label,
                       lambda el: el.is_displayed())

def _wait_for_outcome(wait):
    def _check(_driver):
        try:
            alert = _driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            logger.info("Alert detected in outcome wait: %s", alert_text)
            return "validation", []
        except Exception:
            pass

        for locator in RESULT_ITEM_LOCATORS:
            items = _driver.find_elements(*locator)
            if items:
                return "results", items

        for locator in NO_RESULTS_LOCATORS:
            items = _driver.find_elements(*locator)
            if any(item.is_displayed() for item in items):
                return "no_results", items

        for locator in VALIDATION_LOCATORS:
            items = _driver.find_elements(*locator)
            if any(item.is_displayed() for item in items):
                return "validation", items

        return False

    return wait.until(_check)

def _wait_for_search_panel(driver, wait):
    def _check(_driver):
        for locator in SEARCH_PANEL_LOCATORS:
            if any(el.is_displayed() for el in _driver.find_elements(*locator)):
                return True
        return False
    wait.until(_check)

def _is_search_panel_active(driver):
    for locator in SEARCH_PANEL_LOCATORS:
        if any(el.is_displayed() for el in driver.find_elements(*locator)):
            return True
    return False

def _scroll_to_top(driver):
    try:
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception as exc:
        logger.debug("scroll_to_top failed: %s", exc)

def _focus_input(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        driver.execute_script("arguments[0].focus();", element)
    except Exception as exc:
        logger.debug("focus via JS failed: %s", exc)
    try:
        element.click()
    except ElementClickInterceptedException as exc:
        logger.debug("click intercepted, using JS click: %s", exc)
        driver.execute_script("arguments[0].click();", element)

def _try_submit_search(driver):
    for locator in SEARCH_SUBMIT_LOCATORS:
        for element in driver.find_elements(*locator):
            if element.is_displayed() and element.is_enabled():
                driver.execute_script("arguments[0].click();", element)
                logger.debug("Submitted search via locator: %s", _locator_to_str(locator))
                return True
    logger.debug("No submit button found.")
    return False

def _resolve_empty_query_outcome(driver):
    if _is_search_panel_active(driver):
        return "validation", []
    if "/search" in driver.current_url:
        for locator in RESULT_ITEM_LOCATORS:
            items = driver.find_elements(*locator)
            if items:
                return "results", items
        return "no_results", []
    return "validation", []

def _capture_debug_artifacts(driver, case_name):
    try:
        logger.debug("URL: %s | title: %s | readyState: %s",
                     driver.current_url, driver.title,
                     driver.execute_script("return document.readyState"))
    except Exception as exc:
        logger.debug("page-state collection failed: %s", exc)
    try:
        artifacts_dir = os.path.join(os.path.dirname(__file__), "..", "reports", "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        path = os.path.join(artifacts_dir, f"search_{case_name}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        driver.save_screenshot(path)
        logger.debug("Screenshot saved: %s", path)
    except Exception as exc:
        logger.debug("screenshot failed: %s", exc)

def _clear_input(input_el):
    input_el.clear()
    input_el.send_keys(Keys.CONTROL + "a")
    input_el.send_keys(Keys.DELETE)

def _type_with_alert_watch(driver, input_el, query, alert_wait_secs=0.3):
    for i, char in enumerate(query):
        try:
            input_el.send_keys(char)
        except UnexpectedAlertPresentException:
            logger.debug("send_keys raised UnexpectedAlertPresentException on char %d ('%s')", i, char)
            caught, alert_text = _dismiss_any_alert(driver, timeout=1)
            if not caught:
                alert_text = "<already dismissed>"
            logger.info("Alert caught via send_keys exception (char %d): %s", i, alert_text)
            return True, alert_text

        caught, alert_text = _dismiss_any_alert(driver, timeout=alert_wait_secs)
        if caught:
            logger.info("Alert caught after char %d ('%s'): %s", i, char, alert_text)
            return True, alert_text

    return False, None