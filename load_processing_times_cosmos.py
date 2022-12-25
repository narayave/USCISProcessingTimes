import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path         # this will get you the path variable
from webdriver_manager.chrome import ChromeDriverManager
from pprint import pprint
import time
import datetime

import config
from cosmos_ops import CosmosOps


class ProcessingTimes:
    def __init__(self, run_date):
        """
        :param run_date: The day of script execution
        """

        self.run_date = run_date

        self.form_ops = CosmosOps("SubmissionOptions")
        self.proc_times_ops = CosmosOps("ProcessingTimes")

        self.max_id = self._get_cont_max_id()

        # service_object = Service(binary_path)
        self.driver = webdriver.Chrome()
        # self.driver = webdriver.Chrome(ChromeDriverManager(version="109.0.5414.25").install(), service=service_object)
        self.url = "https://egov.uscis.gov/processing-times/"
        self.driver.get(self.url)

        self.form_element = self.driver.find_element("id", "selectForm")
        self.category_element = self.driver.find_element("id", "selectFormCategory")
        self.office_element = self.driver.find_element("id", "selectOfficeOrCenter")
        self.form_select = Select(self.form_element)
        self.category_select = Select(self.category_element)
        self.office_select = Select(self.office_element)

    def _get_cont_max_id(self):
        """
        Read the max id value from container and return that
        :return:
        """
        query = """
            SELECT VALUE max(StringToNumber(c.id))
            FROM c
        """
        id_result = self.proc_times_ops.db_query_items(query)
        max_id = id_result[0]
        print(f'Current max id read is {max_id}')
        return max_id

    def get_all_form_options(self):
        """
        Queries the SubmissionOptions container and gets all values
        :return: Returns a list of documents
        """
        query = """
            SELECT c.formKey, c.categoryKey, c.officeKey
            FROM c
        """
        form_combinations = self.form_ops.db_query_items(query)
        pprint(form_combinations)
        return form_combinations

    @staticmethod
    def select_dropdown_value(selector, drop_down_value):
        """
        Making this a separate function, so we can wait a second after selecting drop down value

        :param selector: drop down selector to be passed
        :param drop_down_value: The value to be selected
        :return: None
        """
        selector.select_by_visible_text(drop_down_value)
        time.sleep(2)

    def get_processing_time(self, option_combo):
        """
        Submit option combo
        :param option_combo:
        :return:
        """

        self.select_dropdown_value(self.form_select, option_combo["formKey"])
        self.select_dropdown_value(self.category_select, option_combo["categoryKey"])
        self.select_dropdown_value(self.office_select, option_combo["officeKey"])

        submit_button = self.driver.find_element(By.ID, "getProcTimes")
        submit_button.click()
        time.sleep(5)

        result = self.driver.find_element(By.CLASS_NAME, "range")
        # Final class text has a newline character, and we're removing it here
        time_units = result.text.split('\n')
        time_val = time_units[0]
        units = time_units[1]

        return time_val, units

    def record_proc_time(self, option_combo, time_val, units):
        """
        Given the processing time, we format and record it
        :param option_combo: Encapsulated with form, category, and office values
        :param time_val: Processing time - a fixed value
        :param units: Associated units for the, could be months or weeks or etc?
        :return:
        """

        self.max_id += 1
        max_id = str(self.max_id)

        # NOTE: Turn weeks into months - this is approximation
        # (Num of weeks * 7 days (in a week)) / divided by 30 (avg days in a month)
        if units == "Weeks":
            time_val = float(int(time_val) * 7.0) / 30.0
            units = "Months"

        proc_time_entry = {
            "id": max_id,
            "rundate": self.run_date,
            "formKey": option_combo["formKey"],
            "categoryKey": option_combo["categoryKey"],
            "officeKey": option_combo["officeKey"],
            "time_val": time_val,
            "time_units": units
        }

        self.proc_times_ops.db_upsert_write(proc_time_entry)
        print("."),

    def iterate_option_combinations(self, combinations):
        """
        :param combinations: Has the form, category, and office values in each entry
        """

        num_of_combinations = len(combinations)
        print(f"Total number of combinations to run through is {num_of_combinations}")
        for i in range(0, num_of_combinations):
            time_val, units = self.get_processing_time(combinations[i])
            self.record_proc_time(combinations[i], time_val, units)

        print(f"Processing times recording complete for {num_of_combinations} combinations")


if __name__ == '__main__':
    proc_times = ProcessingTimes(str(datetime.datetime.now().date()))
    form_option_combinations = proc_times.get_all_form_options()
    proc_times.iterate_option_combinations(form_option_combinations)
