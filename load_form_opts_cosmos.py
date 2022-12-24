import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pprint import pprint
import time
import datetime

import config


class FormSubmissionOptions:
    def __init__(self):
        self.url = "https://egov.uscis.gov/processing-times/"
        self.browser = webdriver.Chrome()
        self.browser.get(self.url)

        self.cosmos_database = "USCISFormTimes"
        self.cosmos_container = "SubmissionOptions"

