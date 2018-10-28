from flask import Flask, render_template
from flask_assistant import Assistant, ask, tell
from steem import Steem
from rep_calculator import rep_cal # To calculate reputation from raw steemd rep

s = Steem()
app = Flask(__name__)
assist = Assistant(app, route='/api')

# Is used to calculate the reputation of a given user
@assist.action('reputation')
def rep():
    ask4_u = "What's your username?"
    return ask(ask4_u)
	
@assist.action('repusername')
def return_rep(repusername):
    try:
        user = s.get_accounts([repusername])
        final = str(rep_cal(user[0]['reputation']))
        return ask(final)
    except IndexError or ValueError:
	    return ask('Error, try again')
#------------------------------------------------------------

# run Flask app
if __name__ == '__main__':
    app.run(debug=True)