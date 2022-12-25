from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path         # this will get you the path variable
from webdriver_manager.chrome import ChromeDriverManager
from pprint import pprint
import time
import datetime
import numbers

from cosmos_ops import CosmosOps


class ProcessingTimes:
    def __init__(self, run_date):
        """
        :param run_date: The day of script execution
        """

        self.run_date = run_date

        self.form_ops = CosmosOps("SubmissionOptions")
        self.proc_times_ops = CosmosOps("ProcessingTimes")

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

        # Record the missed time msgs here which can be analyzed later
        self.error_msg_time = []

    def get_all_form_options(self):
        """
        Queries the SubmissionOptions container and gets all values
        :return: Returns a list of documents
        """
        query = """
            SELECT c.id, c.formKey, c.categoryKey, c.officeKey
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
        time.sleep(1.5)

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
        time.sleep(3)

        result = self.driver.find_element(By.CLASS_NAME, "range").text
        return result

    def record_proc_time(self, option_combo, msg_time_units):
        """
        Given the processing time, we format and record it.
            - And id will be generated, so it's unique for a given day
            - If we find a proper processing time result, we record is appropriately
            - If we didn't find a processing time result, then record the msg, to be revisited later on
        :param option_combo: Encapsulated with id, form, category, and office values
        :param msg_time_units: Processing time with units and or msg
        """

        # NOTE: Creating an id using rundate and id from form container
        # This allows for replaying pipeline and not generating new data every time, just overwrite as necessary
        # Ex: 2022-12-25 for form 14 will be '202212250014'
        fmt_rundate = self.run_date.strftime('%Y%m%d')
        fmt_formid = int(option_combo['id'])
        generated_id = f"{fmt_rundate}{fmt_formid:04d}"

        # Set up db dict with time value if present, if not record the full message and proceed
        msg_time_units = msg_time_units.replace("\n", " ")
        msg_time_list = msg_time_units.split(" ")

        # Base entry dict
        proc_time_entry = {
            "id": generated_id,
            "rundate": str(self.run_date),
            "formKey": option_combo["formKey"],
            "categoryKey": option_combo["categoryKey"],
            "officeKey": option_combo["officeKey"]
        }

        print(msg_time_list)
        print(len(msg_time_list))
        print(type(eval(msg_time_list[0])))

        if (len(msg_time_list) == 2) and isinstance(eval(msg_time_list[0]), numbers.Number):
            # If list has 2 items and first item is of type int, it means we read things properly
            time_val = msg_time_list[0]
            units = msg_time_list[1]

            if units == "Weeks":
                # NOTE: Turn weeks into months - this is approximation
                # (Num of weeks * 7 days (in a week)) / divided by 30 (avg days in a month)
                time_val = float(int(time_val) * 7.0) / 30.0
                units = "Months"
            elif units == "Days":
                # NOTE: If unit is 'Days', divide by 30 (avg days in a month) to record in unit of months
                time_val = float(int(time_val)) / 30.0
                units = "Months"

            proc_time_entry["time_val"] = time_val
            proc_time_entry["time_units"] = units

        else:
            # One of the above conditions is not met, so we'll record the message instead
            proc_time_entry["form_result_msg"] = msg_time_units

            # Adding it to the list to know how entries are having trouble
            self.error_msg_time.append(proc_time_entry)

        self.proc_times_ops.db_upsert_write(proc_time_entry)

    def iterate_option_combinations(self, combinations):
        """
        :param combinations: Has the form, category, and office values in each entry
        """

        num_of_combinations = len(combinations)
        print(f"Total number of combinations to run through is {num_of_combinations}")
        for i in range(0, num_of_combinations):
            msg_time_units = self.get_processing_time(combinations[i])
            self.record_proc_time(combinations[i], msg_time_units)

        print(f"Processing times recording complete for {num_of_combinations} combinations")


if __name__ == '__main__':
    proc_times = ProcessingTimes(datetime.datetime.now().date())
    form_option_combinations = proc_times.get_all_form_options()
    proc_times.iterate_option_combinations(form_option_combinations)

    pprint(proc_times.error_msg_time)
    print(f'Found {len(proc_times.error_msg_time)} errors msgs')
