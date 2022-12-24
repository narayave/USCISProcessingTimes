import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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

form_check_key = 'I-129F'
category_inner_key = 'K1/K2/K3/K4 - Fiance(e) or spouse and/or dependent children'
service_center_key = 'Potomac Service Center'

print("Set fields, delay 1 seconds between input")

form_options = [x.text for x in form.find_elements(By.TAG_NAME, "option")][1:]
form_opts_dict = {x.split(' | ')[0]: x for x in form_options}
print(f'There are {len(form_options)} forms to choose from')
# Creating a dictionary, so I can quickly call what I want - yay
print(form_opts_dict)
form.send_keys(form_opts_dict[form_check_key])
time.sleep(1)

category_options = [x.text for x in category.find_elements(By.TAG_NAME, "option")][1:]
# catg_opts_dict = {x.split(' | ')[0]: x for x in category_options}
print(f'There are {len(category_options)} categories to choose from')
print(category_options)
category.send_keys(category_inner_key)
time.sleep(1)

office_options = [x.text for x in office.find_elements(By.TAG_NAME, "option")][1:]
office_opts_dict = {x.split(' ')[0]: x for x in office_options}
print(f'There are {len(office_options)} offices to choose from\n\n')
pprint(office_opts_dict)


print('\n\n')


office_select = Select(office)

for i in office_opts_dict.keys():
    # print(office_opts_dict[i])

    office_select.select_by_visible_text(office_opts_dict[i])
    # office.send_keys(service_center_key)
    time.sleep(1)

    submitButton = browser.find_element(By.ID, "getProcTimes")
    submitButton.click()
    time.sleep(3)

    result = browser.find_element(By.CLASS_NAME, "range")
    # Final class text has a newline character, and we're removing it here
    final = result.text.replace('\n', ' ')
    print(f"This form's estimated processing time today at {office_opts_dict[i]} is {final}.")

browser.quit()
