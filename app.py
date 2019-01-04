from flask import Flask, request, render_template
from flask_assistant import Assistant, ask, tell
from steem import Steem
from steem.converter import Converter
from steem.blog import Blog 
from steem.account import Account
from steem.amount import Amount
from steemconnect.client import Client
from steemconnect.operations import Follow, Unfollow, Mute, ClaimRewardBalance, Comment, CommentOptions, Vote
import requests, json, os, random, string

St_username = "fancybrothers" 
Tag = ''
s = Steem()
c = Converter()
app = Flask(__name__)
assist = Assistant(app, route='/api', project_id=os.environ.get('project_id'))
app.config['INTEGRATIONS'] = ['ACTIONS_ON_GOOGLE'] # To enable Rich Messages
posts = s.get_discussions_by_trending({"limit":"8"}) # To cache the top 8 trending posts
sc = Client(client_id=os.environ.get('client_id'), client_secret=os.environ.get('client_secret'))

class Steemian:
    def __init__(self, St_username):
        self.username = St_username
        self.data = Account(self.username)
        self.reputation = str(self.data.rep)
        self.upvoteworth = self.calculate_voteworth()
        self.steempower = self.calculate_steempower(True)
        self.availablesp = self.calculate_steempower(False) # To get the amount of Steempower that can be delegated
        self.wallet = self.data.balances
        self.accountworth = self.calculate_accountworth()
        self.steemprice = self.cmc_price('1230') # To get the price of Steem form coinmarketcap
        self.sbdprice = self.cmc_price('1312')   # To get the price of Steem Dollars form coinmarketcap
        self.bloglink = 'https://steemit.com/@'+St_username # To get the price user's blog link
        self.rewards = [self.data["reward_steem_balance"],self.data["reward_sbd_balance"],self.data["reward_vesting_balance"]]
        if self.data["next_vesting_withdrawal"] != "1969-12-31T23:59:59": # Return True if the user is powering down
            self.powerdown = True
        else:
            self.powerdown = False


    def calculate_voteworth(self): # To calculate the vote worth
        reward_fund = s.get_reward_fund()
        sbd_median_price = s.get_current_median_history_price()	
        vests = Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares'])
        vestingShares = int(vests * 1e6)
        rshares = 0.02 * vestingShares
        estimated_upvote = rshares / float(reward_fund['recent_claims']) * Amount(reward_fund['reward_balance']).amount * Amount(sbd_median_price['base']).amount
        estimated_upvote = estimated_upvote * (float(self.data['voting_power'])/10000)
        return ('$'+str(round(estimated_upvote, 2)))
		
		
    def calculate_steempower(self,cd): # To calculate the steem power
	
        def vests2sp(v): # To convert vests into steem power
            sp = c.vests_to_sp(v)
            return str(round(sp, 1))
		
        total = float(Amount(self.data['vesting_shares'])+Amount(self.data['received_vesting_shares'])-Amount(self.data['delegated_vesting_shares']))
        owned = Amount(self.data['vesting_shares']).amount
        delegated = Amount(self.data['delegated_vesting_shares']).amount
        received = Amount(self.data['received_vesting_shares']).amount
        if cd: # A switch between availablesp and steempower 
            return('Your total Steem Power is %s ...  You own %s. You are delegating %s and you are receiving %s.'% (vests2sp(total),vests2sp(owned),vests2sp(delegated), vests2sp(received)))
        else:
            return(float(vests2sp(owned - delegated)))

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
     
def eligible_delegation(user,num): # To check if the delegation is possible
    user = Steemian(user)
    if user.powerdown:
        return ('You are powering down')
    elif user.availablesp < float(num):
        return ('Insufficient Available Steempower')
    else: # If the user isn't powering down and there's enough SP
        return ('eligible')

def resteem(username,author):
    if username == author:
        return ('A post by %s' % username)
    else:
        return ('Resteemed')

def randomperm(length):
   letter = string.ascii_lowercase
   return ''.join(random.choice(letter) for i in range(length))

   ##############################################################
   
 # Returns a welcome msg and refreshes the access token
@assist.action('Welcome')
def Welcome():
    sc.access_token = None
    return ask('Hello, Steem Voice is here! \nCan you provide me with a valid username?')
	
		
# Setting a new username and changing it
@assist.action('Change_username')
@assist.action('Welcome_username')
def r_Welcome(username):
    global St_username
    St_username = username
    sc.access_token = None
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
    resp.link_out('Open the post', postlink) # Is used to create a button that takes you to the post
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
    return resp

@assist.action('userpostsrep') 
@assist.action('r_openfeed')
@assist.action('trendingresp') # To show a card of the post chosen
def r_trendingresp(OPTION):
    global posts, Option
    Option = int(OPTION) # This is the key of the chosen post
    postlink = 'https://steemit.com/@'+posts[Option]['author']+'/'+posts[Option]['permlink']
    resp = ask('Click the button below to open the post')
    date,time = posts[Option]['created'].split('T') 
    resp.card(title=posts[Option]['title'],
              text=('A post by %s created on %s at %s' % (posts[Option]['author'],date,time)),
              img_url=getpostimg(Option),
              link=postlink,
              link_title='Open The post'		  
              )

    return resp.suggest('Upvote the post', 'Write a comment')

@assist.action('openblog') # Retruns a button to the user's blog
def r_openblog():
    user = Steemian(St_username)	  
    return ask('Click the button below to open your blog').link_out('Open Blog',user.bloglink)

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

# Allows the user to connect their account using Steemconnect

@assist.action('login') 
def r_login():
    login_url = sc.get_login_url( 
        str(os.environ.get('server')) + "/login",  # This is the callback URL
        "login,custom_json,comment,vote", # The scopes needed (login allows us to verify the user'steem identity while custom_json allows us to Follow, unfollow and mute)
    )
    resp = ask("Please use the button below to login with SteemConnect")
    resp.link_out('Click Here', login_url) # To return the button that takes the user to the login page
    return resp

# To check if the user successfully connected his account

@assist.action('check')	
def r_check():
    if sc.access_token == None: # No access token
        return ask('Error, Please try to connect your account')
    else:
        return ask('Hello %s ! You can now use commands such as follow, unfollow, mute ...' % sc.me()["name"]) 

@assist.action('follow')	
def r_follow(inst,username):
    try:
        if inst == 'follow': # To follow a certain user
            follow = Follow(sc.me()["name"], username)
            sc.broadcast([follow.to_operation_structure()])
            return ask('Done, you are now following %s' % username)
        elif inst == 'unfollow': # To unfollow a certain user
            unfollow = Unfollow(sc.me()["name"], username)
            sc.broadcast([unfollow.to_operation_structure()])
            return ask('Done, you are no longer following %s' % username)
        elif inst == 'mute': # To mute a certain user
            ignore = Mute(sc.me()["name"], username)
            sc.broadcast([ignore.to_operation_structure()])
            return ask('Done, %s is now muted' % username)
        else:
            return ask('Error, Please try again!')
    except ValueError:
        return ask('Please connect your account before using this command')

# To check if you are following a user

@assist.action('followingcheck')
def r_followingcheck(username):
    count = s.get_follow_count(St_username)['following_count'] # To get the total number of following
    thousands = int(count/1000)
    other = count%1000
    lastuser = 0
    flist = []
    for i in range(thousands):  # s.get_following has a limit of 1000 so I have to break the total followers into groups of 1000
        flist.extend(s.get_following(St_username,lastuser,'blog',1000))
        lastuser = flist[-1]['following']
    flist.extend(s.get_following(St_username,lastuser,'blog',other))
    cond = False # Not following
    for i in range(count):
        if flist[i]['following'] == username.strip(): # To remove the extra space
            cond = True # Following

    if cond:
        return ask('You are following %s' % username)
    else:
        return ask('You are not following %s' % username)

# To check if a user is following you

@assist.action('followcheck')
def r_followcheck(username):
    count = s.get_follow_count(St_username)['follower_count']  # To get the total number of followers
    thousands = int(count/1000)
    other = count%1000
    lastuser = 0
    flist = []
    for i in range(thousands):  
        flist.extend(s.get_followers(St_username,lastuser,'blog',1000))
        lastuser = flist[-1]['follower']
    flist.extend(s.get_followers(St_username,lastuser,'blog',other))
    cond = False
    for i in range(count):
        if flist[i]['follower'] == username.strip():
            cond = True

    if cond:
        return ask('%s is following you' % username)
    else:
        return ask('%s is not following you' % username)

# Used to delegate SP

@assist.action('delegation')
def r_delegation(number,username):
    check = eligible_delegation(St_username,number)
    if check == 'eligible':
        resp = ask('You can use the link below to delegate using Steemconnect')
        link = ("https://steemconnect.com/sign/delegate-vesting-shares?delegator="+St_username+"&delegatee="+username+"&vesting_shares="+str(number)+"%20SP")
        resp.link_out('Click here', link)
        return resp
    else:
        return ask("Error: "+check) # To show the type of error
        
# To Claim all rewards

@assist.action('claim')
def r_claim():
    try:
        user = Steemian(sc.me()["name"])
        claim_reward_balance = ClaimRewardBalance('account', user.rewards[0], user.rewards[1], user.rewards[2])
        sc.broadcast([claim_reward_balance.to_operation_structure()])
        return ask('You have sucessfully claimed %s, %s and %s' % (user.rewards[0],user.rewards[1],user.rewards[2]))
    except: # If the user didn't connect his account
        return ask('Please connect your account before using this command')

@assist.action('openreplies') # Open a link to replies
def r_openreplies():
    user = Steemian(St_username)	  
    return ask('Click the button below to open your replies').link_out('Open Replies',(user.bloglink+'/recent-replies'))


@assist.action('opencomments') # Open a link to comments
def r_opencomments():
    user = Steemian(St_username)	  
    return ask('Click the button below to open your comments').link_out('Open Comments',(user.bloglink+'/comments'))

@assist.action('delegations') # To show the list of delegations
def r_delegations():
    delegations = s.get_vesting_delegations(St_username, '', 100)
    if len(delegations) == 0:
	    return ask('No active delegations')
    else:
        resp = ask('Choose one:').build_carousel()
        for i in range(len(delegations)):
            resp.add_item(delegations[i]['delegatee'],
                          key=(str(i)), # This key will be used if the user chooses a certain post
                          description= str(round(c.vests_to_sp(Amount(delegations[i]['vesting_shares']).amount)))+" SP", # To convert vests to SP
                          img_url='https://steemitimages.com/u/'+delegations[i]['delegatee']+'/avatar'  # To get the avatar image of the delegatee
                          )	
            
        return resp

@assist.action('cdelegations') # To cancel a delegation
def r_cdelegations(OPTION):
    OPTION = int(OPTION)
    delegations = s.get_vesting_delegations(St_username, '', 100)
    resp = ask('Click the button below to cancel the delegation')
    resp.card(title=delegations[OPTION]['delegatee'],
              text=str(round(c.vests_to_sp(Amount(delegations[OPTION]['vesting_shares']).amount)))+" SP",
              img_url='https://steemitimages.com/u/'+delegations[OPTION]['delegatee']+'/avatar',
              link=("https://steemconnect.com/sign/delegate-vesting-shares?delegator="+St_username+"&delegatee="+delegations[OPTION]['delegatee']+"&vesting_shares=0%20SP"),
              link_title='Cancel Delegation'		  
              )
    return resp


# Transfer Steem or SBD

@assist.action('transfer')
def r_transfer(number,currency,username):
    url = sc.hot_sign(
        "transfer",
        {
            "to": username,
            "amount": number+' '+currency.upper(),
      },
    )  
    return ask('Click the button below to continue with your transfer:').link_out('Click here',url)

# Return a user's 8 latest posts
@assist.action('userposts')
def r_userposts(username):
    global posts
    discussion_query = {
        "tag": username.replace(' ', ''),
        "limit": 8,
    }
    posts = s.get_discussions_by_blog(discussion_query)	
    resp = ask('There you go:').build_carousel()
    for i in range(len(posts)):
        resp.add_item(posts[i]['title'],
                        key=(str(i)),
                        description=resteem(username,posts[i]['author']), 
                        img_url=getpostimg(i)  # To get the avatar image of the delegatee
                        )	
    return resp

# To save the comment in a variable called comment and ask the user for confirmation
@assist.action('commentconfirmation')
def r_comment(any):
    global comment
    comment = any
    return ask('Would you like to confirm this comment: %s' % comment).suggest('Yes','No')

# If the user confirms the comment, the app will broadcast the comment  

@assist.action('broadcastcomment')
def r_broadcastcomment(yon):
    try:
        global comment,posts,Option
        if yon == 'Yes':
            finalcomment = Comment(
            sc.me()["name"], #author
            randomperm(10), #permlink
            comment, #body
            parent_author=posts[Option]['author'],
            parent_permlink=posts[Option]['permlink'],
            )

            sc.broadcast([finalcomment.to_operation_structure()])
            return ask('broadcasting %s to %s' % (comment,posts[Option]['title']))
        else:   
            return ask('Canceling comment')
    except: # If the user didn't connect his account
        return ask('Please connect your account before using this command')

# To save the upvote percentage in a variable called percent and ask the user for confirmation

@assist.action('upvoteconfirmation')
def r_upvote(number):
    if (int(number)<=100) and (0<=int(number)): 
        global percent
        percent = number
        return ask('Would you like to confirm this upvote: %s percent' % percent).suggest('Yes','No')
    else:
        return ask('Please make sure to enter a valid percent')


# If the user confirms the upvote, the app will broadcast the upvote  

@assist.action('broadcastupvote')
def r_broadcastupvote(yon):
    try:
        global percent, posts, Option
        vote = Vote(sc.me()['name'], posts[Option]["author"], posts[Option]["permlink"], int(percent))
        sc.broadcast([vote.to_operation_structure()])
        return ask('broadcasting upvote to %s' % posts[Option]['title'])
    except: # If the user didn't connect his account
        return ask('Please connect your account before using this command')

# Allows setting the access token and Shows the page when user successfully authorizes the app

@app.route('/login')
def loginpage():
    sc.access_token = request.args.get("access_token")
    return render_template('success.html', variable = sc.me()["name"])
	 
	
# run Flask app
if __name__ == '__main__':
    app.run(debug=True) 