# twitterspy

Watch twitter accounts for keywords to trigger pushover notifications

## Requirements

* Python 3.8+

pip packages:
* daemonize
* tweepy
* pendulum

Package requirements are defined in `requirements.txt`

## Configuration

Configuration is via environment variables.

* `TWITTER_CONSUMER_SECRET` = Twitter application consumer secret (https://apps.twitter.com/app/new)
* `TWITTER_CONSUMER_KEY` = Twitter application consumer key
* `TWITTER_ACCESS_TOKEN` = Twitter Dev Portal → App → Keys & Tokens → Authentication Tokens → Access Token
* `TWITTER_ACCESS_SECRET` = Twitter Dev Portal → App → Keys & Tokens → Authentication Tokens → Access Token Secret
* `TWITTERSPY_FOLLOW` = comma-separated list of twitter handles to follow (no `@` required)
* `TWITTERSPY_KEYWORDS` = comma-separated list of keywords to search for
* `TWITTERSPY_LOG_DIR` = directory to log to
* `TWITTERSPY_PID` = path to pid file
* `PUSHOVER_APP_KEY` = Pushover application key (https://pushover.net/apps/build)
* `PUSHOVER_DEVICE` = Pushover device name
* `PUSHOVER_USER_KEY` = Pushover user key
