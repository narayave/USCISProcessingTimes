import time
from selenium import webdriver
from selenium.webdriver.common.by import By

print("Begin...")

browser = webdriver.Chrome()
url = "https://egov.uscis.gov/processing-times/"
browser.get(url)

print("Waiting to load page... (Delay 3 seconds)")

time.sleep(3)

print("Searching for elements")

form = browser.find_element("id", "selectForm")
category = browser.find_element("id", "selectFormCategory")
office = browser.find_element("id", "selectOfficeOrCenter")

# print(form)
# print(category)
# print(office)

form_options = [x for x in form.find_elements(By.TAG_NAME, "option")]
# print(form_options)

for element in form_options:
    print(element)

# print("Set fields, delay 3 seconds between input")
#
# search_journal = "Relatorios dos Presidentes dos Estados Brasileiros (BA)"
# search_timeRange = "1890 - 1899"
# search_text = "Milho"
#
# journal.send_keys(search_journal)
# time.sleep(3)
# timeRange.send_keys(search_timeRange)
# time.sleep(3)
# searchTerm.send_keys(search_text)
#
# print("Perform search")
#
# submitButton = button.find_element_by_id("PesquisarBtn1_input")
# submitButton.click()