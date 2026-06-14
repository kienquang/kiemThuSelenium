"# kiemThuSelenium" 
                         
pytest tests/testFilter/test_filter.py -v --html=reports/report.html -s
pytest tests/testSearch/test_search.py -v --html=reports/report.html -s
pytest --html=reports/report.html -s