import pytest
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from tests.testFilter.constants import *
from tests.testFilter.filter_helpers import (
    open_website,
    get_sort_dropdown,
    select_sort_option,
    get_first_item_text,
    wait_for_sort_completed,
    get_prices,
    get_names,
    classify_option,
    run_test
)

@pytest.fixture
def driver():
    driver_instance = open_website()
    yield driver_instance
    driver_instance.quit()
OPTION_NAMES = [
    "Gia_Tang_Dan", 
    "Gia_Giam_Dan", 
    "Ten_A_Z", 
    "Ten_Z_A", 
]

@pytest.mark.parametrize("idx", [ 1, 2, 3, 4, ], ids=OPTION_NAMES)
def test_sorting_options(driver, idx):
    try:
        sort_select = get_sort_dropdown(driver)
        
        if idx >= len(sort_select.options):
            pytest.skip(f"Dropdown không có phần tử tại index {idx}")

        option = sort_select.options[idx]
        option_text = option.text.strip()
        option_value = option.get_attribute("value") or ""

        category = classify_option(option_text, option_value)

        if category == "skip":
            pytest.skip(f"Bỏ qua tuỳ chọn mặc định/không hỗ trợ: {option_text}")

        is_price_sort = "price" in category
        prev_text = get_first_item_text(driver, is_price_sort)

        select_sort_option(driver, sort_select, idx)
        wait_for_sort_completed(driver, prev_text, is_price_sort)

        if is_price_sort:
            data = get_prices(driver, category)
        else:
            data = get_names(driver)

        result = run_test(category, data)

        assert result == "PASS", f"FAIL: Dữ liệu sắp xếp sai tại tuỳ chọn '{option_text}'"

    except (TimeoutException, NoSuchElementException) as exc:
        pytest.fail(f"Lỗi Exception tại option {idx}: {type(exc).__name__} - {exc}")