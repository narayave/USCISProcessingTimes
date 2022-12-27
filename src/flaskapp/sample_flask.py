from flask import Flask

from flask import render_template
from flask import request

import json
import pandas as pd
# import pandasql as ps
# import plotly
# from pprint import pprint
# import psycopg2
# from six.moves import configparser
# from sqlalchemy import create_engine
# from sqlalchemy_utils import database_exists
# from sqlalchemy_utils import create_database

# from flaskexample import app

from uscis_proc_times.cosmos_ops import CosmosOps


app = Flask(__name__)

sub_form_cosmos_client = CosmosOps("SubmissionOptions")
proc_times_cosmos_client = CosmosOps("ProcessingTimes")

# print(app.url_map)


@app.route('/')
def index():

    query = f"""
        SELECT DISTINCT VALUE c.formKey
        FROM c
    """

    submission_forms = proc_times_cosmos_client.db_query_items(query)

    return render_template("input.html",
                           title='Home USCIS Tracker', dropdown_list=submission_forms)


@app.route('/output')
def form_output():

    form = request.args.get('formKey')

    query = f"""
        SELECT c.run_date, c.categoryKey, c.officeKey, c.time_val, c.time_units
        FROM c
        WHERE c.formKey = {form}
        GROUP BY c.run_date, c.formKey, c.categoryKey, c.officeKey
        ORDER BY c.run_date, c.categoryKey, c.officeKey
    """

    form_results = proc_times_cosmos_client.db_query_items(query)

    return render_template("output.html", items=form_results)
