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
    response = cur.fetchall()[0]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('games_list.html',
                                     games=df[df.Week == default_week],function="twenty_twenty", year=2020, week=week)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('games_list.html',
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week,function="twenty_twenty", year=2020, week=week)

# basic landing route
@app.route('/2019', methods=['GET', 'POST'])
def twenty_nineteen():

    # fetch data
    sql_string = 'select games from games_data where year = 2019'
    cur.execute(sql_string)
    response = cur.fetchall()[0]




    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('games_list.html',
                                     games=df[df.Week == default_week],function="twenty_nineteen",year=2019)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('games_list.html',function="twenty_nineteen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2019)

# basic landing route
@app.route('/2018', methods=['GET', 'POST'])
def twenty_eighteen():

    # fetch data
    sql_string = 'select games from games_data where year = 2018'
    cur.execute(sql_string)
    response = cur.fetchall()[0]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('games_list.html',function="twenty_eighteen",
                                     games=df[df.Week == default_week], year=2018)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('games_list.html',function="twenty_eighteen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2018)

# basic landing route
@app.route('/2017', methods=['GET', 'POST'])
def twenty_seventeen():

    # fetch 2020 data
    sql_string = 'select games from games_data where year = 2017'
    cur.execute(sql_string)
    response = cur.fetchall()[0]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('games_list.html',function="twenty_seventeen",
                                     games=df[df.Week == default_week+1], year=2017)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']

        return flask.render_template('games_list.html',function="twenty_seventeen",
                                     games=df[df.Week == int(selected_week)],
                                     selected_week=selected_week, year=2017)

@app.route('/matchups', methods=['GET', 'POST'])
def specific_matchups():
    # get a list of teams
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/Teams/2020?key=d8b5ea01537141eb9a320f95994b7109')
    # put in dataframe
    teams = pd.DataFrame.from_dict(response.json())
    teams= teams['Key'] # just get abbreviations

    # get the week 
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/CurrentWeek?key=d8b5ea01537141eb9a320f95994b7109')
    week = response.json()


    # load up the model
    with open('./models/nfl_predictor_rf.pkl', 'rb') as f:
        model = pickle.load(f)

    # fetch 2020 data
    sql_string = 'select stats from team_stats where year = 2020'
    cur.execute(sql_string)
    response = cur.fetchall()[0]

    df = pd.read_json(response[0]).T
    df = df.set_index('Team') # set index to be team to locate values

    predicted_winner = ""

    # load page
    if flask.request.method == 'GET':
        return flask.render_template('matchups.html', teams=teams, predicted_winner=predicted_winner)

    if flask.request.method == 'POST':
        # get inputs
        home_team = flask.request.form['team_user_selected_1']
        away_team = flask.request.form['team_user_selected_2']
        


        # create custom df
        custom_df = pd.DataFrame(index=[0], columns=['AwayAverage','AwayFirstDowns', 'AwayTime', 'AwayThirdDowns', 'HomeAverage','HomeFirstDowns', 'HomeTime', 'HomeThirdDowns'])
        
        # team 1 stats
        custom_df['HomeAverage'] = df.loc[home_team,'avg_up_to_week_{0}'.format(week)]
        custom_df['HomeFirstDowns'] = df.loc[home_team,'first_downs_up_to_week_{0}'.format(week)]
        custom_df['HomeTime'] = df.loc[home_team,'time_of_possession_up_to_week_{0}'.format(week)]
        custom_df['HomeThirdDowns'] = df.loc[home_team,'third_down_percentage_up_to_week_{0}'.format(week)]

        # team 2 stats
        custom_df['AwayAverage'] = df.loc[away_team,'avg_up_to_week_{0}'.format(week)]
        custom_df['AwayFirstDowns'] = df.loc[away_team,'first_downs_up_to_week_{0}'.format(week)]
        custom_df['AwayTime'] = df.loc[away_team,'time_of_possession_up_to_week_{0}'.format(week)]
        custom_df['AwayThirdDowns'] = df.loc[away_team,'third_down_percentage_up_to_week_{0}'.format(week)]


        # use model to predict
        selected_features = ['AwayAverage','AwayFirstDowns', 'AwayTime', 'AwayThirdDowns', 'HomeAverage','HomeFirstDowns', 'HomeTime', 'HomeThirdDowns']

        values = custom_df[selected_features].values

        predictions = model.predict(values) # make predictions

        if predictions[0] == 1:
            predicted_winner=home_team
        else:
            predicted_winner=away_team

        return flask.render_template('matchups.html', teams=teams, predicted_winner=predicted_winner, home_team=home_team, away_team=away_team)




if __name__ == '__main__':
    app.run(debug=True)
