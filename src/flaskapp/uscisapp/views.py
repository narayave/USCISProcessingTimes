from flask import Flask

from flask import render_template
from flask import request

import json
import pandas as pd
from pprint import pprint

# import pandasql as ps
import plotly
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

print(app.url_map)


@app.route('/')
def index():

    query = f"""
        SELECT DISTINCT VALUE c.formKey
        FROM c
    """

    submission_forms = proc_times_cosmos_client.db_query_items(query)

    return render_template("input.html",
                           title='Home USCIS Tracker', dropdown_list=submission_forms)


@app.route('/homeresults')
def home_page_results():

    all_actor_roles = ["COP", "GOV", "JUD", "BUS", "CRM", "DEV", "EDU", "ENV",
                       "HLH", "LEG", "MED", "MNC"]

    loc = request.args.get('location').upper()
    checks = request.args.getlist('check_list[]')
    checks = [i.encode('utf-8') for i in checks]
    ticks = checks
    print loc
    print checks

    if len(checks) == 1:
        query = "SELECT * FROM central_results WHERE action_state='%s' \
                    and actor_type = '%s' and CAST(year AS INTEGER) >= 2010 \
                    ORDER BY month_year;" % (loc, checks[0])
    elif len(checks) > 1:
        query = "SELECT * FROM central_results WHERE action_state='%s' \
                    and actor_type IN %s and CAST(year as INTEGER) >= 2013 \
                    ORDER BY month_year;" % (loc, tuple(checks))
    elif checks == []:
        query = "SELECT * FROM central_results WHERE action_state='%s' \
                    and CAST(year as INTEGER) >= 2013 ORDER BY month_year \
                    DESC;" % (loc)

    print query

    query_results = pd.read_sql_query(query, con)
    print query_results

    results_dict = []
    overall_result = []
    for i in ticks:
        query = "SELECT year, month_year, actor_type, events_count, norm_scale \
                    FROM query_results WHERE actor_type ='"+i+"'"

        results_tmp = ps.sqldf(query, locals())
        print results_tmp

        event_counts = results_tmp['events_count'].values
        norms_scale = results_tmp['norm_scale'].values

        scores_avg = [(j / i)*100 for i, j in zip(event_counts, norms_scale)]
        print 'Scores_avg ' + str(scores_avg)

        years = map(int, list(results_tmp['month_year'].values))
        scores = map(float, scores_avg)

        # Add logic to check last 2 months
	if len(scores_avg) != 0 and len(scores_avg) > 2:
		last_month = scores[-2]
		this_month = scores[-1]
		verdict = 1 if this_month >= last_month else 0
		overall_result.append(
			dict(actor=results_tmp['actor_type'][0], verdict=verdict)
		)
		print last_month, this_month, verdict

        try:
            # for item in query
            results_dict.append(
                dict(x=years, y=scores, name=results_tmp['actor_type'][0],
                     type='line'))
        except Exception as e:
            print 'Error message - ' + str(e)
            continue

    pprint(results_dict)

    print ps.sqldf(query, locals())

    graphs = [
        dict(  # data,
            data=[item for item in results_dict],
            layout=dict(
                title='Result',
                xaxis=dict(title='Years', type='category'),
                yaxis=dict(title='Impact score (%)')
            )
        )
    ]

    # Add "ids" to each of the graphs to pass up to the client for templating
    ids = ['Results:']

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    print graphJSON

    return render_template("results.html", ids=ids, graphJSON=graphJSON,
                           overall=overall_result)

@app.route('/results')
def form_output():

    form_key = request.args.get('form_names')
    print(f'Selecting form - {form_key}')

    query = f"""
        SELECT c.run_date, c.formKey, CONCAT(c.categoryKey, ' - ', c.officeKey) AS catg_office_key, c.time_val, c.time_units
        FROM c
        WHERE c.formKey = {form_key}
        ORDER BY c.run_date, c.categoryKey, c.officeKey
    """

    form_results = proc_times_cosmos_client.db_query_items(query)
    pprint(form_results)

    form_pdf = pd.json_normalize(form_results)
    form_pdf.show()

    dates = map(int, list(form_pdf['run_date'].values))
    times = map(float, list(form_pdf['time_val'].values))

    results_dict = []
    try:
        # for item in query
        results_dict.append(
            dict(x=dates, y=times, name=form_pdf['catg_office_key'],
                 type='line'))
    except Exception as e:
        print('Error message - ' + str(e))

    pprint(results_dict)

    graphs = [
        dict(  # data,
            data=[item for item in results_dict],
            layout=dict(
                title='Result',
                xaxis=dict(title='Dates', type='category'),
                yaxis=dict(title='Times (in months)')
            )
        )
    ]

    # Add "ids" to each of the graphs to pass up to the client for templating
    ids = ['Results:']

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    print(graphJSON)

    return render_template("results.html", ids=ids, graphJSON=graphJSON)
