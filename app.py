import flask
import os
import pickle
import requests
import psycopg2
import json
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler


# load in env variables
db_host = os.environ['HEROKU_DB_HOST']
db_name = os.environ['HEROKU_DB']
db_user = os.environ['HEROKU_DB_USER']
db_password = os.environ['HEROKU_DB_PASSWORD']
api_key = os.environ['SPORTS_DATA_IO_API']
api_key_2 = os.environ['SPORTS_DATA_IO_API_2']

# import model
with open('./models/nfl_predictor_rf.pkl', 'rb') as f:
    model = pickle.load(f)


# connect to postgres database
conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port="5432")
cur = conn.cursor()




# define flask app
app = flask.Flask(__name__, template_folder='templates')


# define database update
def update_database():
    # get both dataframes we need from api
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/CurrentWeek?key={0}'.format(api_key_2))
    week = response.json()

    # season stats per team
    response = requests.get('https://api.sportsdata.io/api/nfl/odds/json/ScoresByWeek/2020REG/{0}?key={1}'.format(week, api_key))
    current_games = pd.DataFrame.from_dict(response.json())



    # season stats per team
    response = requests.get('https://api.sportsdata.io/api/nfl/odds/json/TeamSeasonStats/2020REG?key={0}'.format(api_key))
    team_stats_2020 = pd.DataFrame.from_dict(response.json())

    # bring in the database dataframes
    # create the SQL string for games data 
    sql_string = 'SELECT games from games_data where year = 2020'
    cur.execute(sql_string)
    db_games_data = cur.fetchone()[0]
    db_games_data = pd.read_json(db_games_data).T


    # create the SQL string for team stats data 
    sql_string = 'SELECT stats from team_stats where year = 2020'
    cur.execute(sql_string)
    db_team_stats = cur.fetchone()[0]
    db_team_stats = pd.read_json(db_team_stats).T

    # update year team stats
    for index, row in team_stats_2020.iterrows():
        db_team_stats.at[index, 'avg_up_to_week_{0}'.format(week)] = row.Score / row.Games
        db_team_stats.at[index, 'first_downs_up_to_week_{0}'.format(week)] = row.FirstDowns / row.Games
        db_team_stats.at[index, 'third_down_percentage_up_to_week_{0}'.format(week)] = row.ThirdDownPercentage
        
        # convert string time of possession to float
        top = row.TimeOfPossession.split(':')
        top = float('{0}.{1}'.format(top[0],top[1]))
        db_team_stats.at[index, 'time_of_possession_up_to_week_{0}'.format(week)] = top
        
        
        
    # update database for team stats
    data = db_team_stats.to_json(orient="index")
    sql_string = 'UPDATE team_stats SET stats = %s WHERE year = 2020'
    cur.execute(sql_string, (json.dumps(data),))
    conn.commit()

    # update this weeks games with stats
    current_games = current_games[['Week', 'AwayTeam', 'HomeTeam', 'AwayScore', 'HomeScore']]

    db_team_stats = db_team_stats.set_index('Team')

    for index, row in current_games.iterrows():
        current_games.at[index,'HomeAverage'] = db_team_stats.loc[row.HomeTeam,'avg_up_to_week_{0}'.format(week)]
        current_games.at[index,'HomeFirstDowns'] = db_team_stats.loc[row.HomeTeam,'first_downs_up_to_week_{0}'.format(week)]
        current_games.at[index,'HomeTime'] = db_team_stats.loc[row.HomeTeam,'time_of_possession_up_to_week_{0}'.format(week)]
        current_games.at[index,'HomeThirdDowns'] = db_team_stats.loc[row.HomeTeam,'third_down_percentage_up_to_week_{0}'.format(week)]

        # team 2 stats
        current_games.at[index,'AwayAverage'] = db_team_stats.loc[row.AwayTeam,'avg_up_to_week_{0}'.format(week)]
        current_games.at[index,'AwayFirstDowns'] = db_team_stats.loc[row.AwayTeam,'first_downs_up_to_week_{0}'.format(week)]
        current_games.at[index,'AwayTime'] = db_team_stats.loc[row.AwayTeam,'time_of_possession_up_to_week_{0}'.format(week)]
        current_games.at[index,'AwayThirdDowns'] = db_team_stats.loc[row.AwayTeam,'third_down_percentage_up_to_week_{0}'.format(week)]

    # let model make predictions on this weeks games
    selected_features = ['AwayAverage','AwayFirstDowns', 'AwayTime', 'AwayThirdDowns', 'HomeAverage','HomeFirstDowns', 'HomeTime', 'HomeThirdDowns']
    # get values we want
    values = current_games[selected_features].values

    # make predictions
    predictions = model.predict(values)

    for index, row in current_games.iterrows():
        current_games.at[index, 'PredictHomeTeamWin'] = predictions[index]
        
    # fill scores as games arent played yet
    current_games = current_games.fillna(-1)
        
    # append to all games
    db_games_data = db_games_data.append(current_games, ignore_index=True)

    db_games_data.to_csv('./custom_games_by_season/2020_data.csv', header=True,  encoding='utf-8', index=False) 


    # update database for season games
    data = db_games_data.to_json(orient="index")
    sql_string = 'UPDATE games_data SET games = %s WHERE year = 2020'
    cur.execute(sql_string, (json.dumps(data),))
    conn.commit()

    print('update successful')

# get rid of scheduler because apis suck
# scheduler = BackgroundScheduler()
# scheduler.add_job(update_database, 'cron', day_of_week = 'thu', hour='7',  minute='30')
# scheduler.start()


# defualt week 
default_week = 1

@app.route('/', methods=['GET'])
def landing_page():
    return flask.render_template('landing_page.html')


@app.route('/contact', methods=['GET'])
def contact_pages():
    return flask.render_template('contact.html')

# basic landing route
@app.route('/2020', methods=['GET', 'POST'])
def twenty_twenty():

    # get the week -- change this to get from database
    # response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/CurrentWeek?key=d8b5ea01537141eb9a320f95994b7109')
    # week = response.json()
    week = 14 # hardcode for now because i ran out of api
    # fetch data
    sql_string = 'select games from games_data where year = 2020'
    cur.execute(sql_string)
    response = cur.fetchall()[0]





    # load page
    if flask.request.method == 'GET':
        # load games
        df = pd.read_json(response[0]).T
        return flask.render_template('games_list.html',
                                     games=df[df.Week == week].reset_index(),function="twenty_twenty", year=2020, week=week)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']
        week = df[df.Week == int(selected_week)].reset_index()
        return flask.render_template('games_list.html',
                                     games=week,
                                     amount=len(week),
                                     week=selected_week,function="twenty_twenty", year=2020)

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
                                     games=df[df.Week == default_week].reset_index(),function="twenty_nineteen",year=2019, week=1)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']
        week = df[df.Week == int(selected_week)].reset_index()
        return flask.render_template('games_list.html',function="twenty_nineteen",
                                     games=week,
                                     amount=len(week),
                                     week=selected_week, year=2019)

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
                                     games=df[df.Week == default_week].reset_index(), year=2018, week=1)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']
        week = df[df.Week == int(selected_week)].reset_index()
        return flask.render_template('games_list.html',function="twenty_eighteen",
                                     games=week,
                                     amount=len(week),
                                     week=selected_week, year=2018)

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
                                     games=df[df.Week == default_week+1].reset_index(), year=2017, week=1)

    if flask.request.method == 'POST':

        df = pd.read_json(response[0]).T
        selected_week = flask.request.form['week_user_selected']
        week = df[df.Week == int(selected_week)].reset_index()
        return flask.render_template('games_list.html',function="twenty_seventeen",
                                     games=week,
                                     amount=len(week),
                                     week=selected_week, year=2017)

@app.route('/matchups', methods=['GET', 'POST'])
def specific_matchups():
    # get a list of teams
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/Teams/2020?key=152276092f6d485086221429787e75a8')
    # put in dataframe
    teams = pd.DataFrame.from_dict(response.json())
    teams= teams['Key'] # just get abbreviations

    # get the week 
    # response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/CurrentWeek?key=d8b5ea01537141eb9a320f95994b7109')
    week = 14


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
        return flask.render_template('matchups.html', teams=teams, predicted_winner=predicted_winner, error=False)

    if flask.request.method == 'POST':
        # get inputs
        home_team = flask.request.form['team_user_selected_1']
        away_team = flask.request.form['team_user_selected_2']
        
        if home_team == away_team:
            return flask.render_template('matchups.html', teams=teams, predicted_winner="no winner", home_team=home_team, away_team=away_team, error=True)



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

        return flask.render_template('matchups.html', teams=teams, predicted_winner=predicted_winner, home_team=home_team, away_team=away_team, error=False)




if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.run()
