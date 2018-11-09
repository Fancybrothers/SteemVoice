from flask import Flask
from flask_assistant import Assistant, ask, tell
from steem import Steem
from steem.converter import Converter
from steem.blog import Blog
from steem.account import Account
from rep_calculator import rep_cal # To calculate reputation from raw steemd rep
from cleaner import clean
import math

St_username = ""
s = Steem()
c = Converter()
app = Flask(__name__)
assist = Assistant(app, route='/api')

class Steemian:
    def __init__(self, St_username):
        self.username = St_username
        self.data = Account(self.username)
        self.reputation = str(rep_cal(self.data['reputation']))
        self.upvoteworth = self.calculate_voteworth()
        self.steempower = self.calculate_steempower()
		
		
    def calculate_voteworth(self):
        reward_fund = s.get_reward_fund()
        sbd_median_price = s.get_current_median_history_price()
        vests = float(clean(self.data['vesting_shares']))+float(clean(self.data['received_vesting_shares']))-float(clean(self.data['delegated_vesting_shares']))
        vestingShares = int(vests * 1e6);
        rshares = 0.02 * vestingShares
        estimated_upvote = rshares / float(reward_fund['recent_claims']) * float(clean(reward_fund['reward_balance'])) * float(clean(sbd_median_price['base']))	
        estimated_upvote = estimated_upvote * (float(self.data['voting_power'])/10000)
        return ('$'+str(round(estimated_upvote, 2)))
		
		
    def calculate_steempower(self):
	
        def vests2sp(v):
            sp = c.vests_to_sp(v)
            return str(round(sp, 1))
		
        total = float(clean(self.data['vesting_shares']))+float(clean(self.data['received_vesting_shares']))-float(clean(self.data['delegated_vesting_shares']))
        owned = float(clean(self.data['vesting_shares']))
        delegated = float(clean(self.data['delegated_vesting_shares']))
        received = float(clean(self.data['received_vesting_shares']))
        return(   'Your total Steem Power is '  +  vests2sp(total)+  '...'  +  ' You own '  +  vests2sp(owned)  +  '. You are delegating '  +  vests2sp(delegated)  +  ' and you are receiving '  +  vests2sp(received)  )

# Setting a new username and changing it
@assist.action('Change_username')
@assist.action('Welcome_username')
def Welcome(username):
    global St_username
    St_username = username
    return ask('Got it. How can I assist?')

	
# Is used to calculate the reputation of a given user

@assist.action('reputation')
def r_rep():
    user = Steemian(St_username)
    return ask(user.reputation)

# Is used to calculate the upvote worth of a given user

@assist.action('vote_worth')
def r_voteworth():
    user = Steemian(St_username)
    return ask(user.upvoteworth)
		
# Is used to calculate the steem power of a given user

@assist.action('steempower')
def r_steempower():	
    user = Steemian(St_username)
    return ask(user.steempower)

# Is used to get a user's latest post

@assist.action('last_post')
def r_last_post():	
    b = Blog(St_username)
    post = b.take(1)
    return ask('Your latest post is: \n'+ post[0]['title'])

# run Flask app
if __name__ == '__main__':
    app.run(debug=True)