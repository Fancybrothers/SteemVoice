from flask import Flask
from flask_assistant import Assistant, ask, tell
from steem import Steem
from steem.converter import Converter
from steem.blog import Blog 
from steem.account import Account
from steem.amount import Amount
import requests, json

St_username = ""
Tag = ''
s = Steem()
c = Converter()
app = Flask(__name__)
app.config['ASSIST_ACTIONS_ON_GOOGLE'] = True # To enable Rich Messages
assist = Assistant(app, route='/api')
posts = s.get_discussions_by_trending({"limit":"8"}) # To cache the top 8 trending posts


class Steemian:
    def __init__(self, St_username):
        self.username = St_username
        self.data = Account(self.username)
        self.reputation = str(self.data.rep)
        self.upvoteworth = self.calculate_voteworth()
        self.steempower = self.calculate_steempower()
        self.wallet = self.data.balances
        self.accountworth = self.calculate_accountworth()
        self.steemprice = self.cmc_price('1230') # To get the price of Steem form coinmarketcap
        self.sbdprice = self.cmc_price('1312')   # To get the price of Steem Dollars form coinmarketcap
        self.bloglink = 'https://steemit.com/@'+St_username # To get the price user's blog link
		
    def calculate_voteworth(self): # To calculate the vote worth
        reward_fund = s.get_reward_fund()
        sbd_median_price = s.get_current_median_history_price()	
        vests = Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares'])
        vestingShares = int(vests * 1e6);
        rshares = 0.02 * vestingShares
        estimated_upvote = rshares / float(reward_fund['recent_claims']) * Amount(reward_fund['reward_balance']).amount * Amount(sbd_median_price['base']).amount
        estimated_upvote = estimated_upvote * (float(self.data['voting_power'])/10000)
        return ('$'+str(round(estimated_upvote, 2)))
		
		
    def calculate_steempower(self): # To calculate the steem power
	
        def vests2sp(v): # To convert vests into steem power
            sp = c.vests_to_sp(v)
            return str(round(sp, 1))
		
        total = float(Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares']))
        owned = Amount(self.data['vesting_shares']).amount
        delegated = Amount(self.data['delegated_vesting_shares']).amount
        received = Amount(self.data['received_vesting_shares']).amount
        return('Your total Steem Power is %s ...  You own %s. You are delegating %s and you are receiving %s.'% (vests2sp(total),vests2sp(owned),vests2sp(delegated), vests2sp(received)))
	
    def cmc_price(self,id): # To get the price of a given currency
        r = requests.get("https://api.coinmarketcap.com/v2/ticker/"+id)
        data = r.json()
        return data['data']['quotes']['USD']['price']
		
    def calculate_accountworth(self): # To calculate the account worth
        SBD_price = self.cmc_price('1312')
        STEEM_price = self.cmc_price('1230')
        accountworth = (self.wallet['total']['STEEM'] + self.data.sp)*STEEM_price + self.wallet['total']['SBD']*SBD_price
        return round(accountworth,0)
   ######################## Functions ######################################
   
def getpostimg(i): # To get a post's thumbnail
    global posts
    metadata = posts[i]['json_metadata']
    imagedata = json.loads(metadata)
    try : # To test if the post is a dtube video
        imglink = 'https://snap1.d.tube/ipfs/'+imagedata['video']['info']['snaphash'] # To get the video's thumbnail form d.tube
        return(imglink)
    except KeyError: # If it's a regular post
        try:
            return imagedata['image'][0]
        except: # If no image is available 
            return 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/No_image_available_600_x_450.svg/320px-No_image_available_600_x_450.svg.png' # a "no image available" picture from wikimedia
     
 
   ##############################################################
		
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
		

# Is used to get a user's latest post

@assist.action('last_post')
def r_last_post():	
    b = Blog(St_username)
    user = Steemian(St_username)
    post = b.take(1)
    resp = ask('Your latest post is: \n'+ post[0]['title'])
    postlink = user.bloglink+'/'+post[0]['permlink']
    resp.link_out('The post', postlink) # Is used to create a button that takes you to the post
    return resp
	
@assist.action('wallet')
def r_desire(desire):
    user = Steemian(St_username)
    if desire == 'steem': # Is used to get the available steem of a given user
	    return ask('%s STEEM' % user.wallet['available']['STEEM'])
    elif desire == 'sbd': # Is used to get the available sbd of a given user
	    return ask('%s Steem Dollars' % user.wallet['available']['SBD'])
    elif desire == 'savings': # Is used to get the savings of a given user
	    return ask('You have %s Steem Dollars and %s STEEM in your savings' % (user.wallet['savings']['SBD'],user.wallet['savings']['STEEM']))
    elif desire == 'accountworth': # Is used to calculate the account worth
	    return ask('Your account is worth approximately $%i according to coinmarketcap\'s latest prices.' % user.accountworth)
    elif desire == 'steempower': # Is used to calculate the steem power of a given user
	    return ask(user.steempower)
    else:
	    return ask('Error! Please try again')

@assist.action('price')
def r_price(currency):
    user = Steemian(St_username)
    if currency == 'steem': # Is used to get the price of STEEM
	    return ask('Steem is now worth $'+str(round(user.steemprice,2))+' according to coinmarketcap.')
    elif currency == 'sbd': # Is used to get the price of SBD
	    return ask('Steem Dollars is now worth $'+str(round(user.sbdprice,2))+' according to coinmarketcap.')	
    else:
	    return ask('Error! Please try again')
		
@assist.action('trending') # Is used to display the top 8 trending posts (a certain tag can be specified)
def r_trendingposts(CTG,Tag):
    global posts
    if (Tag != '')or (CTG != 'trending'): # If a certain tag is specified or another category -posts- will be reloaded into the top 8 trending posts of that tag
        posts = eval('s.get_discussions_by_'+CTG)({"tag":Tag,"limit":"8"})
    if Tag == '':
        Tag = 'all tags' # To keep a proper resp statment even when no tag is specified 
    if CTG == 'created':
        resp = ask(('Here are the newest posts in %s') % (Tag)).build_carousel()
    else:
        resp = ask(('Here are the top %s posts in %s') % (CTG,Tag)).build_carousel()  # To make a new carousel
    for i in range(8): # Add each post to the carousel
        try:
            resp.add_item(posts[i]['title'],
                          key=(str(i)), # This key will be used if the user chooses a certain post
                          img_url=getpostimg(i)
                          )				
        except IndexError: # If the available posts are less than 8 (mostly promoted ones)
            break	
    print(resp)			
    return resp

@assist.action('r_openfeed')
@assist.action('trendingresp') # To show a card of the post chosen
def r_trendingresp(OPTION):
    global posts
    OPTION = int(OPTION) # This is the key of the chosen post
    postlink = 'https://steemit.com/@'+posts[OPTION]['author']+'/'+posts[OPTION]['permlink']
    resp = ask('Click the button below to open the post')
    date,time = posts[OPTION]['created'].split('T') 
    resp.card(title=posts[OPTION]['title'],
              text=('A post by %s created on %s at %s' % (posts[OPTION]['author'],date,time)),
              img_url=getpostimg(OPTION),
              img_alt='test', # This field is required
              link=postlink,
              linkTitle='Open The post'		  
              )

    return resp

@assist.action('openblog') # Retruns a button to the user's blog
def r_trendingposts():
    user = Steemian(St_username)	  
    return ask('Click the button below to open your blog').link_out('Blog',user.bloglink)

@assist.action('openfeed') # Retruns a list of posts from the user's list
def r_feed():
    global posts
    posts = s.get_discussions_by_feed({"tag":St_username,"limit":"10"})	
    resp = ask('Here are the latest posts from your feed').build_carousel()
    for i in range(10):
         try:
            resp.add_item(posts[i]['title'],
                          key=(str(i)), # This key will be used if the user chooses a certain post
                          img_url=getpostimg(i)
                          )				
         except IndexError: # If the available posts are less than 8
            break	
    return resp	
	
# run Flask app
if __name__ == '__main__':
    app.run(debug=True)