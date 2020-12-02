import flask
import os
import pickle
import requests
import psycopg2
import pandas as pd
from pandas import json_normalize


# load in env variables
db_host = os.environ['HEROKU_DB_HOST']
db_name = os.environ['HEROKU_DB']
db_user = os.environ['HEROKU_DB_USER']
db_password = os.environ['HEROKU_DB_PASSWORD']
api_key = os.environ['SPORTS_DATA_IO_API']

# set default week
default_week = 1

# connect to postgres database
conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
cur = conn.cursor()




# define flask app
app = flask.Flask(__name__, template_folder='templates')


# basic landing route
@app.route('/2020', methods=['GET', 'POST'])
def twenty_twenty():

    # get the week 
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/CurrentWeek?key=d8b5ea01537141eb9a320f95994b7109')
    week = response.json()

    # fetch data
    sql_string = 'select games from games_data where year = 2020'
    cur.execute(sql_string)
    response = cur.fetchall()[1]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('main_page.html',
                                     games=df[df.Week == default_week],function="twenty_twenty", year=2020, week=week)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('main_page.html',
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week,function="twenty_twenty", year=2020, week=week)

# basic landing route
@app.route('/2019', methods=['GET', 'POST'])
def twenty_nineteen():

    # fetch data
    sql_string = 'select games from games_data where year = 2019'
    cur.execute(sql_string)
    response = cur.fetchall()[1]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('main_page.html',
                                     games=df[df.Week == default_week],function="twenty_nineteen",year=2019)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('main_page.html',function="twenty_nineteen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2019)

# basic landing route
@app.route('/2018', methods=['GET', 'POST'])
def twenty_eighteen():

    # fetch data
    sql_string = 'select games from games_data where year = 2018'
    cur.execute(sql_string)
    response = cur.fetchall()[1]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('main_page.html',function="twenty_eighteen",
                                     games=df[df.Week == default_week], year=2018, week=week)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('main_page.html',function="twenty_eighteen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2018, week=week)

# basic landing route
@app.route('/2017', methods=['GET', 'POST'])
def twenty_seventeen():

    # fetch 2020 data
    sql_string = 'select games from games_data where year = 2017'
    cur.execute(sql_string)
    response = cur.fetchall()[1]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('main_page.html',function="twenty_seventeen",
                                     games=df[df.Week == default_week+1], year=2017)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('main_page.html',function="twenty_seventeen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2017)
if __name__ == '__main__':
    app.run(debug=True)
