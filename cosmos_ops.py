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


class CosmosOps:
    def __init__(self, container_name):
        self.cosmos_database = "USCISFormTimes"
        self.cosmos_container = container_name
        host = config.settings['host']

        master_key = config.settings['master_key']
        self.cosmos_client = cosmos_client.CosmosClient(host, {'masterKey': master_key},
                                                        user_agent="CosmosDBPythonQuickstart",
                                                        user_agent_overwrite=True)
        self.db_client = None
        self.container_client = None
        self._db_setup()

    def _db_setup(self):

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

    def db_upsert_write(self, entry):
        print('Going to write to database the following entry - ')
        pprint(entry)
        self.container_client.upsert_item(entry)

    def db_query_items(self, query) -> list:

        print(f'Running query - \n {query}')
        items = list(self.container_client.query_items(query, enable_cross_partition_query=True))
        print(f'Found {len(items)} items from query')
        return items
