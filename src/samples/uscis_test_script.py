import time

from selenium.webdriver import DesiredCapabilities
# from selenium import webdriver

# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pprint import pprint
from seleniumwire import webdriver
import json
# DesiredCapabilities handlSSLErr = DesiredCapabilities.chrome ()
# handlSSLErr.setCapability (CapabilityType.ACCEPT_SSL_CERTS, true)
# WebDriver driver = new ChromeDriver (handlSSLErr);

print("Begin...")

url = "https://egov.uscis.gov/processing-times/"
# browser = webdriver.Chrome()
options = {
    'addr': '127.0.0.1',  # Address of the machine running Selenium Wire. Explicitly use 127.0.0.1 rather than localhost if remote session is running locally.
    'verify_ssl': False
}
browser = webdriver.Chrome(
    # command_executor=url,
    seleniumwire_options=options
)

browser.get(url)
# browser = driver

print("Waiting to load page... (Delay 3 seconds)")

time.sleep(3)

print("Searching for elements")

form = browser.find_element("id", "selectForm")
category = browser.find_element("id", "selectFormCategory")
office = browser.find_element("id", "selectOfficeOrCenter")

form_check_key = 'I-129F'
category_inner_key = 'K1/K2/K3/K4 - Fiance(e) or spouse and/or dependent children'
service_center_key = 'Potomac Service Center'

# form_check_key = 'I-765'
# category_inner_key = 'Based on an approved, concurrently filed, I-821D [(c)(33)]'

print("Set fields, delay 1 seconds between input")

form_options = [x.text for x in form.find_elements(By.TAG_NAME, "option")][1:]
form_opts_dict = {x.split(' | ')[0]: x for x in form_options}
print(f'There are {len(form_options)} forms to choose from')
# Creating a dictionary, so I can quickly call what I want - yay
pprint(form_options)
form.send_keys(form_opts_dict[form_check_key])
time.sleep(2)

category_options = [x.text for x in category.find_elements(By.TAG_NAME, "option")][1:]
# catg_opts_dict = {x.split(' | ')[0]: x for x in category_options}
print(f'There are {len(category_options)} categories to choose from')
print(category_options)
category.send_keys(category_inner_key)
time.sleep(2)

office_options = [x.text for x in office.find_elements(By.TAG_NAME, "option")][1:]
office_opts_dict = {x.split(' ')[0]: x for x in office_options}
print(f'There are {len(office_options)} offices to choose from\n\n')
pprint(office_opts_dict)


print('\n\n')


office_select = Select(office)
for i in office_opts_dict.keys():
    print(office_opts_dict[i])

    office_select.select_by_visible_text(office_opts_dict[i])
    # office.send_keys(service_center_key)
    time.sleep(2)

    submitButton = browser.find_element(By.ID, "getProcTimes")
    submitButton.click()
    time.sleep(3)

    pprint(browser.requests)
    requests_list = [x for x in browser.requests if "/api/processingtime/" in x.url]
    print(requests_list)
    request = requests_list[-1]

    # for request in browser.requests:
    if request.response:
        print(
            request.url,
        )
        # pprint(request.response.body)
        pprint(json.loads(request.response.body.decode()))
    time.sleep(1)

    result = browser.find_element(By.CLASS_NAME, "range").text.replace('\n', ' ')
    print(f'===result - {result}')
    # # Final class text has a newline character, and we're removing it here
    # final = result.text.replace('\n', ' ')
    # print(f"This form's estimated processing time today at {office_opts_dict[i]} is {final}.")

browser.quit()
