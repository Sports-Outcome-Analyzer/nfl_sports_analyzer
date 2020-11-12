import flask
import os
import requests
import pandas as pd
from pandas import json_normalize 

# get our api key
apiKey = os.environ['sportsAPI']

# define flask app
app = flask.Flask(__name__, template_folder='templates')

# basic landing route
@app.route('/', methods=['GET', 'POST'])
def main():
    # make call for list of games
    response = requests.get('https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/2020REG/10?key={0}'.format(apiKey))


    df = pd.DataFrame.from_dict(response.json())     # turn into dataframe
    df = df[['AwayTeam','HomeTeam']] # transform into only team names


    # load page
    if flask.request.method == 'GET':
        return(flask.render_template('main_page.html', games=df))

if __name__ == '__main__':
    app.run()