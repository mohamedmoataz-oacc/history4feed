# history4feed

## Overview

It is common for feeds (RSS or XML) to only include a limited number of posts. I generally see the latest 3 - 5 posts of a blog in a feed. For blogs that have been operating for years, this means potentially thousands of posts are missed.

There is no way to page through historic articles using an RSS or ATOM feed (they were not designed for this), which means the first poll of the feed will only contain the limited number of articles in the feed. This limit is defined by the blog owner.

history4feed can be used to create a complete history for a blog, and keep that history updated, exposing the posts in a database and a single RSS feed.

history4feed;

1. takes an RSS / ATOM feed URL
2. downloads a Wayback Machine archive for the feed
3. identified all unique blog posts in the historic feeds downloaded
4. downloads a HTML version of the article content on each page
5. stores each post in a SQLlite database
6. can be re-run at anytime to download any new posts on the blog into the database

## Install

```shell
# clone the latest code
git clone https://github.com/signalscorps/history4feed
# create a venv
cd history4feed
python3 -m venv history4feed-venv
source history4feed-venv/bin/activate
# install requirements
pip3 install -r requirements.txt
```

If you want to use the ScrapFly proxy service you need to add your API to an `.env` file.

```shell
cp .env.sample .env
```

## Usage

You can see some examples we use for testing to help you get started in `design/mvp/test.md`.

Threat intelligence related blogs can be found here: https://github.com/signalscorps/awesome-threat-intel-blogs

### Feed list

Running the script with the `list` flag will show all existing feeds and the data held by each

```shell
python3 history4feed.py --list
```

Will return a response in the following format;

```txt
feed_id,feed_type,feed_url,feed_last_run,feed_earliest_entry,feed_latest_entry
```
 
### Feed Updates

Running the script without any flags, e.g.

```shell
python3 history4feed.py
```

Will check all feeds in the database for new posts.

### Add a New Feed

The following flags/arguments can be used to add a new feed;

* `--url` (required): the URL of the RSS or ATOM feed, e.g. `https://therecord.media/news/cybercrime/feed/`. Note this will be validated to ensure the feed is in the correct format.
    * note, this must be unique. If you want to change the settings of an existing feed URL you must first delete it and then re-ingest its data.
    * note, some URLs with special characters need to be escaped before passing to the CLI, e.g. `https://feeds.fortinet.com/fortinet/blog/threat-research&x=1` -> `https://feeds.fortinet.com/fortinet/blog/threat-research\&x=1` (note the `\` escape character before the `&`)
* `--earliest_entry` (optional): earliest record you want to scrape. Must be in the past.
    * default is `2020-01-01`
    * format: `YYYY-MM-DD`
* `--latest_entry` (optional): The latest record you want to scrape. Must be in the past.
    * note: if latest_entry, updates will not apply to this blog as it will only ever show data up until the date entered.
    * default is script run time
    * format: `YYYY-MM-DD`
* `--sleep_seconds` (optional): This is useful when a large amount of posts are returned. This sets the time between each request to get the full text of the article to reduce servers blocking robotic requests.
    * default is `2`
    * format: whole number (seconds)
* `--number_of_retries` (optional): This is useful when a large amount of posts are returned. This sets the number of retries when a non-200 response is returned.
    * default is `3`
    * format: whole number (count)
* `--ignore_live_feed_entries` (optional): If passed, will ignore any entries in the live feed URL entered.
    * default if not passed is false (`0`)
* `--pretty_print` (optional): By default, history4feed will minify the content stored. If passed, XML output is pretty printed in the DB. Note, if the feed is already pretty printed, this setting will try an re-prettify (possibly leading to a worse outcome). If the feed is already in a pretty printed format, the output will be pretty and this setting is not recommended.
    * default if not passed is false (`0`)

Note, when a new feed is added all data will be added to the database for that feed. However, no other feeds in the database will be checked for updates. You need to run the script without any flags to do this.

### Deleting a feed

* `--url` (required): the URL of the RSS or ATOM feed you want to delete. Must match the `feed.url` in the database exactly
* `--delete`: if passed will delete the feed url entered and any feed entries associate with it from the database.

## Useful supporting tools

* [Donate to the Wayback Machine]](https://archive.org/donate)

## Support

[Minimal support provided via Slack in the #support-oss channel](https://join.slack.com/t/signalscorps-public/shared_invite/zt-1exnc12ww-9RKR6aMgO57GmHcl156DAA).

## License

[Apache 2.0](/LICENSE).