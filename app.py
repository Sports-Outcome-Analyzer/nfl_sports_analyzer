import flask
import os



app = flask.Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def main():
    # load initial page
    if flask.request.method == 'GET':
        return(flask.render_template('main_page.html'))
