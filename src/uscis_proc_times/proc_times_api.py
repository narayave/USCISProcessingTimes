import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
# from seleniumwire import webdriver
from pprint import pprint
import time
import datetime
import json

from cosmos_ops import CosmosOps

# NOTE: Selenium help - http://automate-apps.com/how-to-select-option-from-drop-down-using-selenium-web-driver/


class ProcessingTimes:
    def __init__(self, run_date):
        """
        :param run_date: The day of script execution
        """

        self.run_date = run_date

        self.form_ops = CosmosOps("SubmissionOptions")
        self.proc_times_ops = CosmosOps("ProcessingTimes")

        # options = {
        #     'addr': '127.0.0.1',
        #     # Address of the machine running Selenium Wire. Explicitly use 127.0.0.1 rather than localhost if remote session is running locally.
        #     'verify_ssl': False
        # }
        # self.driver = webdriver.Chrome(
        #     # command_executor=url,
        #     seleniumwire_options=options
        # )

        # self.driver = webdriver.Chrome()
        # self.driver = webdriver.Chrome(ChromeDriverManager(version="109.0.5414.25").install(), service=service_object)
        # self.url = "https://egov.uscis.gov/processing-times/"
        # self.driver.get(self.url)

        # self.form_element = self.driver.find_element("id", "selectForm")
        # self.category_element = self.driver.find_element("id", "selectFormCategory")
        # self.office_element = self.driver.find_element("id", "selectOfficeOrCenter")
        # self.form_select = Select(self.form_element)
        # self.category_select = Select(self.category_element)
        # self.office_select = Select(self.office_element)

        # Record the missed time msgs here which can be analyzed later
        self.error_msg_time = []

    def get_all_form_options(self):
        """
        Queries the SubmissionOptions container and gets all values
        :return: Returns a list of documents
        """
        query = """
            SELECT c.id, c.formKey, c.categoryKey, c.officeKey, c.api_url
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

    def upload_submission_restapi_url(self, option_combo, request):

        option_combo["api_url"] = request.url
        option_combo["gather_date"] = datetime.datetime.now().strftime('%Y-%m-%mT%H:%M:%S')
        self.form_ops.db_upsert_write(option_combo)

    def get_proc_api_response(self, option_combo):

        resp = requests.get(
            option_combo["api_url"], headers={"Referer": "https://egov.uscis.gov/processing-times/"}, verify=False
        )

        dict_resp = json.loads(resp.text)

        resp_subtypes = dict_resp["data"]["processing_time"]["subtypes"][0]

        return resp_subtypes

    def record_api_result_proc_time(self, option_combo, resp_dict):

        # NOTE: Creating an id using rundate and id from form container
        # This allows for replaying pipeline and not generating new data every time, just overwrite as necessary
        # Ex: 2022-12-25 for form 14 will be '202212250014'
        fmt_rundate = self.run_date.strftime('%Y%m%d')
        fmt_formid = int(option_combo['id'])
        generated_id = f"{fmt_rundate}{fmt_formid:04d}"

        try:
            time_val = resp_dict["range"][1]['value']
            time_units = resp_dict["range"][1]['unit']

            # Base entry dict
            proc_time_entry = {
                "id": generated_id,
                "rundate": str(self.run_date),
                "formKey": option_combo["formKey"],
                "categoryKey": option_combo["categoryKey"],
                "officeKey": option_combo["officeKey"],
                "publication_date": resp_dict["publication_date"],
                "service_request_date": resp_dict["service_request_date"]
            }

            if time_units == "Weeks":
                # NOTE: Turn weeks into months - this is approximation
                # (Num of weeks * 7 days (in a week)) / divided by 30 (avg days in a month)
                time_val = float(int(time_val) * 7.0) / 30.0
                time_units = "Months"
            elif time_units == "Days":
                # NOTE: If unit is 'Days', divide by 30 (avg days in a month) to record in unit of months
                time_val = float(int(time_val)) / 30.0
                time_units = "Months"

            proc_time_entry["time_val"] = time_val
            proc_time_entry["time_units"] = time_units

        except:
            # One of the above conditions is not met, so we'll record the message instead
            proc_time_entry["form_result_msg"] = "Something happened"

            # Adding it to the list to know how entries are having trouble
            self.error_msg_time.append(proc_time_entry)

        self.proc_times_ops.db_upsert_write(proc_time_entry)

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

        # requests_list = [x for x in self.driver.requests if "/api/processingtime/" in x.url]
        # print(requests_list)
        # request = requests_list[-1]
        # self.upload_submission_restapi_url(option_combo, request)

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

        # Briefly remove the period from a possible numeric value to verify
        digit_check = msg_time_list[0].replace('.', '', 1).isdigit()
        if (len(msg_time_list) == 2) and digit_check:
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
            resp = self.get_proc_api_response(combinations[i])
            self.record_api_result_proc_time(combinations[i], resp)

        print(f"Processing times recording complete for {num_of_combinations} combinations")


if __name__ == '__main__':

    start_time = datetime.datetime.now()
    proc_times = ProcessingTimes(datetime.datetime.now().date())
    form_option_combinations = proc_times.get_all_form_options()
    pprint(form_option_combinations)
    proc_times.iterate_option_combinations(form_option_combinations)

    pprint(proc_times.error_msg_time)
    print(f'Found {len(proc_times.error_msg_time)} errors msgs')
    end_time = datetime.datetime.now()
    print(f'Total runtime was {end_time - start_time}')
