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
        self.form_element = self.browser.find_element("id", "selectForm")
        self.category_element = self.browser.find_element("id", "selectFormCategory")
        self.office_element = self.browser.find_element("id", "selectOfficeOrCenter")

        self.cosmos_database = "USCISFormTimes"
        self.cosmos_container = "SubmissionOptions"
        host = config.settings['host']

        master_key = config.settings['master_key']
        self.cosmos_client = cosmos_client.CosmosClient(host, {'masterKey': master_key},
                                                        user_agent="CosmosDBPythonQuickstart",
                                                        user_agent_overwrite=True)
        self.db_client = None
        self.container_client = None
        self.db_setup()

    def db_setup(self):

        try:
            # setup database for this sample
            try:
                self.db_client = self.cosmos_client.create_database(id=self.cosmos_database)
                print(f"Database with id '{self.cosmos_database}' created")

            except exceptions.CosmosResourceExistsError:
                self.db_client = self.cosmos_client.get_database_client(self.cosmos_database)
                print(f"Database with id '{self.cosmos_database}' was found")

            # setup container for this sample
            try:
                self.container_client = self.db_client.create_container(id=self.cosmos_container,
                                                                        partition_key=PartitionKey(path='/form'))
                print(f"Container with id '{self.cosmos_container}' created")

            except exceptions.CosmosResourceExistsError:
                self.container_client = self.db_client.get_container_client(self.cosmos_container)
                print(f"Container with id '{self.cosmos_container}' was found")

        except exceptions.CosmosHttpResponseError as e:
            print('\nrun_sample has caught an error. {0}'.format(e.message))

        finally:
            print("CosmosDb setup complete")

    @staticmethod
    def get_form_options(element):
        """
        Given a dropdown element, this function gets list values of drop down options
        :param element: element can be for form option, category, or office
        :return:
        """

        dropdown_options = [x.text for x in element.find_elements(By.TAG_NAME, "option")][1:]
        return dropdown_options

    def db_write(self, entry):
        print('Going to write to database the following entry - ')
        pprint(entry)
        self.container_client.create_item(entry)

    def load_db(self):

        form_options = self.get_form_options(self.form_element)
        form_select = Select(self.form_element)
        category_select = Select(self.category_element)
        office_select = Select(self.office_element)

        final_options_combos = []
        pprint(form_options)
        id_counter = 0

        for f in form_options:
            print(f'\n\nGoing to work on form - {f}')
            form_opts_prefix = f.split(' | ')[0]

            form_select.select_by_visible_text(f)
            time.sleep(1)

            category_options = self.get_form_options(self.category_element)
            pprint(category_options)
            for c in category_options:
                print(f'\nGoing to work on category - {c}')
                category_select.select_by_visible_text(c)
                time.sleep(1)

                office_options = self.get_form_options(self.office_element)
                pprint(office_options)
                for o in office_options:
                    print(f'Going to work on office - {o}')
                    office_select.select_by_visible_text(o)
                    time.sleep(1)

                    # Add entries to a table in a flattened way
                    # Can be looped through later to get processing times
                    id_counter += 1
                    entry = {
                        "id": str(id_counter),
                        "formKey": f,
                        "categoryKey": c,
                        "officeKey": o,
                        "gather_date": datetime.datetime.now().strftime('%Y-%m-%mT%H:%M:%S')
                    }
                    final_options_combos.append(entry)

                    self.db_write(entry)

        print(f'Total options - {len(final_options_combos)}')

        print('End of script')


dbLoader = FormSubmissionOptions()
dbLoader.load_db()
