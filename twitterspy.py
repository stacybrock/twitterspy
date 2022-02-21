from datetime import datetime
from daemonize import Daemonize
import argparse
import json
import logging
import logging.handlers
import os
import pendulum
import re
import requests
import sys
import tweepy

SCRIPTPATH = os.path.dirname(os.path.abspath(__file__))

# handle command line args
parser = argparse.ArgumentParser()
parser.add_argument("--nodaemon", help="run in foreground", action="store_true")
args = parser.parse_args()

# convert timestamp to Pacific time
def local_time(record, datefmt=None):
    return datetime.fromtimestamp(
        record.created,
        pendulum.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %z')

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
formatter.formatTime = local_time
log_location = os.environ.get('TWITTERSPY_LOG_DIR') if os.environ.get('TWITTERSPY_LOG_DIR') else '/tmp/'
log_filename = log_location + '/twitterspy.log'
handler = logging.handlers.TimedRotatingFileHandler(
    log_filename, when='midnight', backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)
keep_fds = [handler.stream.fileno()]

# helper func that prints to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class Twitterspy:
    def __init__(self):
        self.do_auth()

    def do_auth(self):
        auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'],
                                   os.environ['TWITTER_CONSUMER_SECRET'])
        auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'],
                              os.environ['TWITTER_ACCESS_SECRET'])
        self.api = tweepy.API(auth)


class spyStream(tweepy.Stream):

    def set_keywords(self, keywords):
        self.keywords = keywords

    def set_target_accounts(self, accounts):
        self.target_accounts = accounts

    def on_status(self, status):
        # check if the author of this tweet is an account we are targeting
        if status.author.id_str not in self.target_accounts:
            return

        logger.info(f"@{status.author.screen_name}: {status.text}")
        reply_id = getattr(status, 'in_reply_to_status_id_str', None)
        if reply_id is None:
            self.check_for_keywords(status)
        else:
            logger.info(f"    in reply to {status.in_reply_to_status_id_str}... skipping")

    def on_error(self, status_code):
        if status_code == 420:
            return False

    def check_for_keywords(self, status):
        logger.info('    checking for keywords...')
        text = status.text
        for keyword in self.keywords:
            if re.search(keyword, text, re.IGNORECASE):
                self.send_notification(
                    f"@{status.author.screen_name}: {text}",
                    f"twitter alert for {keyword}",
                    f"http://twitter.com/statuses/{status.id_str}")
                return

    def send_notification(self, msg, title, url=""):
        logger.info(f"    sending notification: {msg} {title} {url}")
        r = requests.post('https://api.pushover.net/1/messages.json', data = {
            'token': os.environ['PUSHOVER_APP_KEY'],
            'user': os.environ['PUSHOVER_USER_KEY'],
            'message': msg,
            'title': title,
            'url': url,
            'device': os.environ['PUSHOVER_DEVICE']
        })
        logger.info(f"    POST result: {r.status_code}")


def main():
    ts = Twitterspy()
    mySpyListener = spyStream(
        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
        access_token=os.environ['TWITTER_ACCESS_TOKEN'],
        access_token_secret=os.environ['TWITTER_ACCESS_SECRET'])

    # get user ids from screen names
    logger.info(f"Following [{os.environ['TWITTERSPY_FOLLOW']}]...")
    target_accounts = []
    for account in os.environ['TWITTERSPY_FOLLOW'].split(','):
        u = ts.api.get_user(screen_name=account)
        target_accounts.append(u.id_str)
    mySpyListener.set_target_accounts(target_accounts)

    mySpyListener.set_keywords(os.environ['TWITTERSPY_KEYWORDS'].split(','))
    logger.info(f"Listening for tweets containing [{os.environ['TWITTERSPY_KEYWORDS']}]...")

    # start filtering tweets via listener
    mySpyListener.filter(follow=target_accounts)


daemon = Daemonize(
    app='twitterspy', pid=os.environ['TWITTERSPY_PID'],
    action=main, keep_fds=keep_fds, foreground=args.nodaemon)
daemon.start()
