from flask import Flask

from flask import render_template
from flask import request

import json
import pandas as pd
import pandasql as ps
import plotly
from pprint import pprint
import psycopg2
from six.moves import configparser
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists
from sqlalchemy_utils import create_database

# from flaskexample import app

from src.uscis_proc_times.cosmos_ops import CosmosOps


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
