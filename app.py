from flask import Flask
from flask_assistant import Assistant, ask, tell
from steem import Steem
from steem.converter import Converter
from steem.blog import Blog
from rep_calculator import rep_cal # To calculate reputation from raw steemd rep
from cleaner import clean
import math

s = Steem()
c = Converter()
app = Flask(__name__)
assist = Assistant(app, route='/api')

# Is used to calculate the reputation of a given user
@assist.action('reputation')
def rep():
    ask4_u = "What's your username?"
    return ask(ask4_u)
	
@assist.action('rep_username')
def r_rep(username):
    user = s.get_accounts([username])
    final = str(rep_cal(user[0]['reputation']))
    return ask(final)

#------------------------------------------------------------

# Is used to calculate the upvote worth of a given user

@assist.action('vote_worth')
def voteworth():
     ask4_u = "What's your username?"
     return ask(ask4_u)

	
@assist.action('vw_username')
def r_voteworth(username):
    user = s.get_accounts([username])
    reward_fund = s.get_reward_fund()
    sbd_median_price = s.get_current_median_history_price()
    vests = float(clean(user[0]['vesting_shares']))+float(clean(user[0]['received_vesting_shares']))-float(clean(user[0]['delegated_vesting_shares']))
    vestingShares = int(vests * 1e6);
    rshares = 0.02 * vestingShares
    estimated_upvote = rshares / float(reward_fund['recent_claims']) * float(clean(reward_fund['reward_balance'])) * float(clean(sbd_median_price['base']))	
    estimated_upvote = estimated_upvote * (float(user[0]['voting_power'])/10000)
    return ask('$'+str(round(estimated_upvote, 2)))
		
#------------------------------------------------------------

# Is used to calculate the steem power of a given user
@assist.action('steempower')
def steempower():
     ask4_u = "What's your username?"
     return ask(ask4_u)

	
@assist.action('sp_username')
def r_steempower(username):	

    def vests2sp(v):
        sp = c.vests_to_sp(v)
        return str(round(sp, 1))
		
    user = s.get_accounts([username])
    total = float(clean(user[0]['vesting_shares']))+float(clean(user[0]['received_vesting_shares']))-float(clean(user[0]['delegated_vesting_shares']))
    owned = float(clean(user[0]['vesting_shares']))
    delegated = float(clean(user[0]['delegated_vesting_shares']))
    received = float(clean(user[0]['received_vesting_shares']))
    return ask(   'Your total Steem Power is '  +  vests2sp(total)+  '...'  +  ' You own '  +  vests2sp(owned)  +  '. You are delegateing '  +  vests2sp(delegated)  +  ' and you are receiving '  +  vests2sp(received)  )
	
#------------------------------------------------------------

# Is used to get a user's latest post

@assist.action('last_post')
def steempower():
     ask4_u = "What's your username?"
     return ask(ask4_u)
	 
@assist.action('r_last_post')
def r_post(username):	
    b = Blog(username)
    post = b.take(1)
    return ask('The latest post from @' + username + ' is: \n'+ post[0]['title'])

# run Flask app
if __name__ == '__main__':
    app.run(debug=True)