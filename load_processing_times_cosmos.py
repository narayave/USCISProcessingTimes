import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path # this will get you the path variable
from pprint import pprint
import time
import datetime

import config
from cosmos_ops import CosmosOps


class ProcessingTimes:
    def __init__(self):

        service_object = Service(binary_path)
        self.driver = webdriver.Chrome(service=service_object)
        self.url = "https://egov.uscis.gov/processing-times/"
        self.driver.get(self.url)

        self.form_element = self.driver.find_element("id", "selectForm")
        self.category_element = self.driver.find_element("id", "selectFormCategory")
        self.office_element = self.driver.find_element("id", "selectOfficeOrCenter")

        self.form_ops = CosmosOps("SubmissionOptions")
        self.proc_times_ops = CosmosOps("ProcessingTimes")
