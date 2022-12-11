import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from pprint import pprint

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

form_options = [x.text for x in form.find_elements(By.TAG_NAME, "option")][1:]
print(f'There are {len(form_options)} forms to choose from')

# Creating a dictionary, so I can quickly call what I want - yay
form_opts_dict = {x.split(' | ')[0]: x for x in form_options}
pprint(form_opts_dict)

print("Set fields, delay 1 seconds between input")

form_check_key = 'I-129F'
category_inner_key = 'K1/K2/K3/K4 - Fiance(e) or spouse and/or dependent children'
service_center_key = 'Potomac Service Center'

form.send_keys(form_opts_dict[form_check_key])
time.sleep(1)
category.send_keys(category_inner_key)
time.sleep(1)
office.send_keys(service_center_key)

print("Perform search")

submitButton = browser.find_element(By.ID, "getProcTimes")
submitButton.click()

print("Form has been submitted!")
# time.sleep(3)
#
# result = browser.find_element(By.ID, "range")
# result_unit = browser.find_element(By.ID, "unit")
# print(f"This form's estimated processing time today is {result.text} {result_unit.text}.")
