# load in env variables
import flask
import os
import pickle
import requests
import psycopg2
import pandas as pd
from pandas import json_normalize


db_host = os.environ['HEROKU_DB_HOST']
db_name = os.environ['HEROKU_DB']
db_user = os.environ['HEROKU_DB_USER']
db_password = os.environ['HEROKU_DB_PASSWORD']
api_key = os.environ['SPORTS_DATA_IO_API']
# apiKey = 'd8b5ea01537141eb9a320f95994b7109'


# connect to postgres database
conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
cur = conn.cursor()


# fetch 2020 data
sql_string = 'select games from games_data where year = 2020'
cur.execute(sql_string)
response = cur.fetchall()[1]

# load in data frame
df = pd.read_json(response[0])