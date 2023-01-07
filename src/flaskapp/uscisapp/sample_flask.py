from flask import Flask

from flask import render_template
from flask import request

import json
import pandas as pd
import plotly
import plotly.express as px
from pprint import pprint

# import pandasql as ps
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

@app.route('/')
def index():

    query = f"""
        SELECT DISTINCT VALUE c.formKey
        FROM c
    """

    submission_forms = proc_times_cosmos_client.db_query_items(query)

    return render_template("input.html",
                           title='Home USCIS Tracker', dropdown_list=submission_forms)


@app.route('/results')
def form_output():

    form_key = request.args.get('form_names')
    print(f'Selecting form - {form_key}')

    query = f"""
        SELECT c.rundate, CONCAT(c.categoryKey, ' - ', c.officeKey) AS catg_office_key, c.time_val, c.time_units
        FROM c
        WHERE c.formKey = '{form_key}'
        ORDER BY c.rundate
    """

    form_results = proc_times_cosmos_client.db_query_items(query)
    # pprint(form_results)

    form_pdf = pd.json_normalize(form_results)
    pd.set_option('max_colwidth', None)
    form_pdf['time_val'] = form_pdf['time_val'].astype('float')
    print(form_pdf)

    graphs = px.line(form_pdf, x='rundate', y='time_val', color='catg_office_key', markers=True)
    graphs.show()

    # Add "ids" to each of the graphs to pass up to the client for templating
    ids = ['Result:']

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    # print(graphJSON)

    return render_template("results.html", ids=ids, graphJSON=graphJSON)
