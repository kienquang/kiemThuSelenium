# ==========================================
# constants.py
# ==========================================

URL = "https://icondenim.com/collections/tat-ca-san-pham"
PAGE_LOAD_TIMEOUT = 30

# Selectors
SORT_DROPDOWN_CSS = "select.sort-by.custom-dropdown__select"
PRODUCT_LIST_CSS  = "div.content-product-list.product-list.filter.d-flex.row-left-list"
PRODUCT_BLOCK_CSS = "div.product-block.item"

# Selector lấy giá trị
PRICE_SPAN_CSS    = "div.box-pro-prices p.pro-price span"
# LƯU Ý: Cần thay đổi selector này theo đúng class chứa tên sản phẩm trên web
NAME_TEXT_CSS     = "h3.pro-name a" 

# Keywords để phân loại kiểu sắp xếp
PRICE_ASC_KEYWORDS  = ["price-ascending", "price asc", "low to high", "tăng dần"]
PRICE_DESC_KEYWORDS = ["price-descending", "price desc", "high to low", "giảm dần"]

NAME_ASC_KEYWORDS   = ["title-ascending", "name asc", "a-z", "từ a-z"]
NAME_DESC_KEYWORDS  = ["title-descending", "name desc", "z-a", "từ z-a"]