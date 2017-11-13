from __future__ import print_function
from datetime import datetime
import tweepy
import requests
import os
import sys
import json
import re
import pendulum
import logging
import logging.handlers

SCRIPTPATH = os.path.dirname(os.path.abspath(__file__))

# convert timestamp to Pacific time
def local_time(record, datefmt=None):
    return datetime.fromtimestamp(record.created, pendulum.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %z')

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
formatter.formatTime = local_time
log_location = os.environ.get('TWITTERSPY_LOG_DIR') if os.environ.get('TWITTERSPY_LOG_DIR') else '/tmp/'
log_filename = log_location + '/twitterspy.log'
handler = logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight', backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)

# helper func that prints to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class Twitterspy:
    def __init__(self):
        self.do_auth()

    def do_auth(self):
        self.auth = tweepy.OAuthHandler(os.environ['TWITTER_OAUTH_TOKEN'], os.environ['TWITTER_OAUTH_SECRET'])

        try:
            with open(SCRIPTPATH + '/twitterspy.auth', 'r') as f:
                auth_cache = json.load(f)
        except IOError:
            auth_cache = self.create_auth_session()

        self.auth.set_access_token(auth_cache['key'], auth_cache['secret'])
        self.api = tweepy.API(self.auth)

    def create_auth_session(self):
        try:
            redirect_url = self.auth.get_authorization_url()
        except tweepy.TweepError:
            eprint("Error! Failed to get request token.")

        print("Open this URL in a web browser: {}".format(redirect_url))
        verifier = input("Enter verification code here: ")

        try:
            self.auth.get_access_token(verifier)
        except tweepy.TweepError:
            eprint("Error! Failed to get access token.")

        auth_cache = { "key": self.auth.access_token, "secret": self.auth.access_token_secret }
        with open(SCRIPTPATH + '/twitterspy.auth', 'w') as f:
            json.dump(auth_cache, f)
        return auth_cache


class spyStreamListener(tweepy.StreamListener):

    def set_keywords(self, keywords):
        self.keywords = keywords

    def set_target_accounts(self, accounts):
        self.target_accounts = accounts

    def on_status(self, status):
        if status.author.id_str in self.target_accounts:
            logger.info("@{}: {}".format(status.author.screen_name, status.text))
            reply_id = getattr(status, "in_reply_to_status_id_str", None)
            if reply_id is None:
                self.check_for_keywords(status)
            else:
                logger.info("    in reply to {}... skipping".format(status.in_reply_to_status_id_str))

    def on_error(self, status_code):
        if status_code == 420:
            return False

    def check_for_keywords(self, status):
        logger.info("    checking for keywords...")
        text = status.text
        for keyword in self.keywords:
            if re.search(keyword, text, re.IGNORECASE):
                self.send_notification("@{}: {}".format(status.author.screen_name, text), "flight deal for {}".format(keyword), "http://twitter.com/statuses/{}".format(status.id_str))
                return

    def send_notification(self, msg, title, url=""):
        logger.info("    sending notification: {} {} {}".format(msg, title, url))
        r = requests.post('https://api.pushover.net/1/messages.json', data = {
            'token': os.environ['PUSHOVER_APP_KEY'],
            'user': os.environ['PUSHOVER_USER_KEY'],
            'message': msg,
            'title': title,
            'url': url,
            'device': os.environ['PUSHOVER_DEVICE']
        })
        logger.info("    POST result: {}".format(r.status_code))


if __name__ == '__main__':
    ts = Twitterspy()
    mySpyListener = spyStreamListener()

    # get user ids from screen names
    logger.info("Following [{}]...".format(os.environ['TWITTERSPY_FOLLOW']))
    target_accounts = []
    for account in os.environ['TWITTERSPY_FOLLOW'].split(","):
        u = ts.api.get_user(account)
        target_accounts.append(u.id_str)
    mySpyListener.set_target_accounts(target_accounts)

    mySpyListener.set_keywords(os.environ['TWITTERSPY_KEYWORDS'].split(","))
    logger.info("Listening for tweets containing [{}]...".format(os.environ['TWITTERSPY_KEYWORDS']))

    # start filtering tweets via listener
    spy = tweepy.Stream(auth = ts.api.auth, listener=mySpyListener)
    spy.filter(follow=target_accounts)
