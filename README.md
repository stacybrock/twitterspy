# twitterspy

Watch twitter accounts for keywords to trigger pushover notifications

## Requirements

Python 3.6+

Package requirements are defined in `requirements.txt`

## Configuration

Configuration is via environment variables.

* `TWITTER_OAUTH_SECRET` = Twitter application consumer secret (https://apps.twitter.com/app/new)
* `TWITTER_OAUTH_TOKEN` = Twitter application consumer key
* `TWITTERSPY_FOLLOW` = comma-separated list of twitter handles to follow (no `@` required)
* `TWITTERSPY_KEYWORDS` = comma-separated list of keywords to search for
* `TWITTERSPY_LOG_DIR` = directory to log to
* `TWITTERSPY_PID` = path to pid file
* `PUSHOVER_APP_KEY` = Pushover application key (https://pushover.net/apps/build)
* `PUSHOVER_DEVICE` = Pushover device name
* `PUSHOVER_USER_KEY` = Pushover user key
