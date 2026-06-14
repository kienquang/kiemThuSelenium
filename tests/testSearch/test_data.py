TEST_CASES = [
    {
        "name": "valid_keyword",
        "query": "ao so mi",
        "expected": ["results"]
    },
    {
        "name": "valid_keyword_vietnamese",
        "query": "áo sơ mi",
        "expected": ["results"]
    },
    {
        "name": "product_code",
        "query": "AKID0211-01",
        "expected": ["results"]
    },
    {
        "name": "empty_space_start_end",
        "query": "  Áo Khoác Vải Dù Chống Tia UV Nam Sun Shield Form Regular    ",
        "expected": ["results"]
    },


    {
        "name": "empty_string",
        "query": "",
        "expected": ["validation", "no_results"]
    },
    {
        "name": "special_characters",
        "query": "@@@###",
        "expected": ["no_results", "validation"]
    },
    {
        "name": "non_existent_item",
        "query": "nonexistentitemxyz",
        "expected": ["no_results"]
    },
    {
        "name": "sql_injection_basic",
        "query": "' OR '1'='1",
        "expected": ["no_results", "validation"]
    },
    {
        "name": "xss_script_tag",
        "query": "<script>alert(1)</script>",
        "expected": ["no_results", "validation"]
    },
    {
        "name": "nosql_injection",
        "query": "{\"$ne\":null}",
        "expected": ["no_results", "validation"]
    },
    {
        "name": "url_encoded_attack",
        "query": "%27%20OR%201%3D1%20--",
        "expected": ["no_results", "validation"]
    },
]