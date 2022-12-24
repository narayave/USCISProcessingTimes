import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pprint import pprint
import time
import datetime

from cosmos_ops import CosmosOps
import config


class FormSubmissionOptions:
    def __init__(self):
        self.url = "https://egov.uscis.gov/processing-times/"
        self.browser = webdriver.Chrome()
        self.browser.get(self.url)
        self.form_element = self.browser.find_element("id", "selectForm")
        self.category_element = self.browser.find_element("id", "selectFormCategory")
        self.office_element = self.browser.find_element("id", "selectOfficeOrCenter")

        self.cosmos_ops = CosmosOps("SubmissionOptions")

    @staticmethod
    def get_form_options(element):
        """
        Given a dropdown element, this function gets list values of drop down options
        :param element: element can be for form option, category, or office
        :return:
        """

        dropdown_options = [x.text for x in element.find_elements(By.TAG_NAME, "option")][1:]
        return dropdown_options

    def load_db(self):

        form_options = self.get_form_options(self.form_element)
        form_select = Select(self.form_element)
        category_select = Select(self.category_element)
        office_select = Select(self.office_element)

        final_options_combos = []
        pprint(form_options)
        id_counter = 0

        for form in form_options:
            print(f'\n\nGoing to work on form - {form}')
            form_opts_prefix = form.split(' | ')[0]

            form_select.select_by_visible_text(form)
            time.sleep(1)

            category_options = self.get_form_options(self.category_element)
            pprint(category_options)
            for catg in category_options:
                print(f'\nGoing to work on category - {catg}')
                category_select.select_by_visible_text(catg)
                time.sleep(1)

                office_options = self.get_form_options(self.office_element)
                pprint(office_options)
                for office in office_options:
                    print(f'Going to work on office - {office}')
                    office_select.select_by_visible_text(office)
                    time.sleep(1)

                    # Add entries to a table in a flattened way
                    # Can be looped through later to get processing times
                    id_counter += 1
                    entry = {
                        "id": str(id_counter),
                        "formKey": form,
                        "categoryKey": catg,
                        "officeKey": office,
                        "gather_date": datetime.datetime.now().strftime('%Y-%m-%mT%H:%M:%S')
                    }
                    final_options_combos.append(entry)

                    self.cosmos_ops.db_write(entry)

        print(f'Total options - {len(final_options_combos)}')

        print('End of script')


if __name__ == '__main__':
    dbLoader = FormSubmissionOptions()
    dbLoader.load_db()
