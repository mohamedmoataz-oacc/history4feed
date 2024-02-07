# history4feed

## Overview

It is common for feeds (RSS or XML) to only include a limited number of posts. I generally see the latest 3 - 5 posts of a blog in a feed. For blogs that have been operating for years, this means potentially thousands of posts are missed.

There is no way to page through historic articles using an RSS or ATOM feed (they were not designed for this), which means the first poll of the feed will only contain the limited number of articles in the feed. This limit is defined by the blog owner.

history4feed can be used to create a complete history for a blog and output it as an RSS feed.

history4feed;

1. takes an RSS / ATOM feed URL
2. downloads a Wayback Machine archive for the feed
3. identified all unique blog posts in the historic feeds downloaded
4. downloads a HTML version of the article content on each page
5. creates a single RSS (`.xml`) file from all the articles downloadede

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

### Proxy settings

history4feed is configured to work with the ScrapFly proxy service.
If you want to use the ScrapFly proxy service you need to add your API to an `.env` file.

```shell
cp .env.sample .env
```

## Usage

You can see some examples we use for testing to help you get started in `design/mvp/test.md`.

Threat intelligence related blogs can be found here: https://github.com/signalscorps/awesome-threat-intel-blogs

```shell
python3 history4feed.py \
    --url URL \
    --earliest_entry DATE \
    --latest_entry DATE \
    --sleep_seconds SECS \
    --number_of_retries RETRIES \
    --ignore_live_feed_entries BOOLEAN \
    --decode_output BOOLEAN \
    --pretty_print BOOLEAN \
    --output_file FILE_NAME
```

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
* `--decoded_output` (optional): history4feed can print the post content in the description as either HTML encoded or decoded. Encoded is the default if not set for security, but decoded content (raw HTML) can also be printed if desired.
    * default if not passed is false (`0`)
* `--pretty_print` (optional): By default, history4feed will minify the content stored into a flat file (single line XML). If changing this to true (`1`), the minified file will be converted to pretty print.
    * default if not passed is false (`0`)
* `--output_file` (optional): By default history will print a file with name `<URL>-<EARLIEST_TIME_IN_FEED><LATEST_TIME_IN_FEED>.xml` in the `output/` directory. You can change the filename by passing it using this field. DO NOT pass the `.xml` extension in the value. e.g. use `my_file` NOT `my_file.xml`

## Useful supporting tools

* [Donate to the Wayback Machine](https://archive.org/donate)

## Support

[Minimal support provided via Slack in the #support-oss channel](https://join.slack.com/t/signalscorps-public/shared_invite/zt-1exnc12ww-9RKR6aMgO57GmHcl156DAA).

## License

[Apache 2.0](/LICENSE).