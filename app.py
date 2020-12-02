import flask
import os
import pickle
import requests
import pandas as pd
from pandas import json_normalize

# get our api key
# apiKey = os.environ['sportAPI']
apiKey = 'd8b5ea01537141eb9a320f95994b7109'
default_week = 1
# define flask app
app = flask.Flask(__name__, template_folder='templates')


# basic landing route
@app.route('/', methods=['GET', 'POST'])
def main():
    # make call for list of games
    response = requests.get(
        'https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/2020REG/{0}?key=d8b5ea01537141eb9a320f95994b7109'.format(
            default_week))

    df = pd.DataFrame.from_dict(response.json())  # turn into dataframe
    # df = df[['AwayTeam','HomeTeam']] # transform into only team names

    # load page
    if flask.request.method == 'GET':
        return flask.render_template('main_page.html',
                                     games=df)

    if flask.request.method == 'POST':
        selected_week = flask.request.form['week_user_selected']
        selected_year = flask.request.form['year_user_selected2']
        year_api_dict = {'2017': 'a',
                         '2018': 'b',
                         '2019': 'c',
                         '2020': 'https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/2020REG/{0}?key=d8b5ea01537141eb9a320f95994b7109'}
        api_call = year_api_dict[selected_year]

        response = requests.get(
            api_call.format(
                selected_week))
        df = pd.DataFrame.from_dict(response.json())
        return flask.render_template('main_page.html',
                                     games=df,
                                     selected_week=selected_week,
                                     selected_year=selected_year)


if __name__ == '__main__':
    app.run(debug=True)
