from flask import Flask
from flask_assistant import Assistant, ask, tell
from steem import Steem
from steem.converter import Converter
from steem.blog import Blog
from steem.account import Account
from steem.amount import Amount
import requests

St_username = ""
s = Steem()
c = Converter()
app = Flask(__name__)
assist = Assistant(app, route='/api')

class Steemian:
    def __init__(self, St_username):
        self.username = St_username
        self.data = Account(self.username)
        self.reputation = str(self.data.rep)
        self.upvoteworth = self.calculate_voteworth()
        self.steempower = self.calculate_steempower()
        self.wallet = self.data.balances
        self.accountworth = self.calculate_accountworth()
        self.steemprice = self.cmc_price('1230')
        self.sbdprice = self.cmc_price('1312')
		
    def calculate_voteworth(self):
        reward_fund = s.get_reward_fund()
        sbd_median_price = s.get_current_median_history_price()	
        vests = Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares'])
        vestingShares = int(vests * 1e6);
        rshares = 0.02 * vestingShares
        estimated_upvote = rshares / float(reward_fund['recent_claims']) * Amount(reward_fund['reward_balance']).amount * Amount(sbd_median_price['base']).amount
        estimated_upvote = estimated_upvote * (float(self.data['voting_power'])/10000)
        return ('$'+str(round(estimated_upvote, 2)))
		
		
    def calculate_steempower(self):
	
        def vests2sp(v):
            sp = c.vests_to_sp(v)
            return str(round(sp, 1))
		
        total = float(Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares']))
        owned = Amount(self.data['vesting_shares']).amount
        delegated = Amount(self.data['delegated_vesting_shares']).amount
        received = Amount(self.data['received_vesting_shares']).amount
        return('Your total Steem Power is %s ...  You own %s. You are delegating %s and you are receiving %s.'% (vests2sp(total),vests2sp(owned),vests2sp(delegated), vests2sp(received)))
	
    def cmc_price(self,id):
        r = requests.get("https://api.coinmarketcap.com/v2/ticker/"+id)
        data = r.json()
        return data['data']['quotes']['USD']['price']
		
    def calculate_accountworth(self):
        SBD_price = self.cmc_price('1312')
        STEEM_price = self.cmc_price('1230')
        accountworth = (self.wallet['total']['STEEM'] + self.data.sp)*STEEM_price + self.wallet['total']['SBD']*SBD_price
        return round(accountworth,0)
        
		
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

# Is used to get the available steem of a given user

@assist.action('steem')
def r_steem():	
    user = Steemian(St_username)
    return ask('%s STEEM' % user.wallet['available']['STEEM'])
	
# Is used to get the available sbd of a given user

@assist.action('sbd')
def r_sbd():	
    user = Steemian(St_username)
    return ask('%s Steem Dollars' % user.wallet['available']['SBD'])
	
# Is used to get the savings of a given user

@assist.action('savings')
def r_savings():	
    user = Steemian(St_username)
    return ask('You have %s Steem Dollars and %s STEEM in your savings' % (user.wallet['savings']['SBD'],user.wallet['savings']['STEEM']))

# Is used to calculate the account worth

@assist.action('accountworth')
def r_accountworth():	
    user = Steemian(St_username)
    return ask('Your account is worth approximately $%i according to coinmarketcap\'s latest prices.' % user.accountworth)
	
# Is used to get the price of SBD

@assist.action('sbdprice')
def r_sbdprice():	
    user = Steemian(St_username)
    return ask('Steem Dollars is now worth $'+str(round(user.sbdprice,2))+' according to coinmarketcap.')
	
# Is used to get the price of STEEM

@assist.action('steemprice')
def r_steemprice():	
    user = Steemian(St_username)
    return ask('Steem is now worth $'+str(round(user.steemprice,2))+' according to coinmarketcap.')
						
# run Flask app
if __name__ == '__main__':
    app.run(debug=True)