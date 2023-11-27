#### Short backfill (RSS)

```shell
python3 history4feed.py \
    --url https://krebsonsecurity.com/feed/ \
    --sleep_seconds 3 \
    --earliest_entry 2023-10-01
```

#### Sleep for 5 seconds and increase retries for a large backfill (RSS)

```shell
python3 history4feed.py \
    --url https://therecord.media/feed/ \
    --sleep_seconds 5 \
    --number_of_retries 5 \
    --earliest_entry 2020-01-01
```

#### Set latest entry (so that no updates happen) (RSS)

```shell
python3 history4feed.py \
    --url https://www.schneier.com/blog/atom.xml \
    --earliest_entry 2023-01-01 \
    --latest_entry 2023-03-01
```

#### Show live feed entries in the response (RSS)

```shell
python3 history4feed.py \
    --url https://grahamcluley.com/feed/ \
    --earliest_entry 2023-07-01
```

Delete it

```shell
python3 history4feed.py \
    --url https://grahamcluley.com/feed/ \
    --delete
```

Now compare when no live feed entries shown in the response

```shell
python3 history4feed.py \
    --url https://grahamcluley.com/feed/ \
    --earliest_entry 2023-07-01 \
    --ignore_live_feed_entries
```

### Test blog update with no date (RSS)

```shell
python3 history4feed.py \
    --url https://throw-away-98765.blogspot.com/feeds/posts/default/ \
    --earliest_entry 2023-07-01
```

Note, this is a blog I own. I add a post an then run an update to see if new post ingested;

```shell
python3 history4feed.py
```

#### Dealing with an RSS feed with some styling (feedblitz)

```shell
python3 history4feed.py \
    --url https://feeds.fortinet.com/fortinet/blog/threat-research\&x=1 \
    --sleep_seconds 5 \
    --earliest_entry 2023-08-01 
```


Get a larger time period in the feed, starting from May 2023, but add 5 second delay between each request to prevent rate limiting on server;

```shell
python3 history4feed.py \
    --url https://therecord.media/feed/ \
    --earliest_entry 2023-05-01 \
    --pretty_print \
    --sleep_seconds 5
```

This time, only consider post between January 2023 and March 2023;

```shell
python3 history4feed.py \
    --url https://therecord.media/feed/ \
    --earliest_entry 2023-01-01 \
    --latest_entry 2023-03-31 \
    --pretty_print \
    --sleep_seconds 5
```

Now try with an ATOM feed from 2023-07-01 using `https://www.schneier.com/feed/atom/` blog;

```shell
python3 history4feed.py \
    --url https://www.schneier.com/feed/atom/ \
    --earliest_entry 2022-01-01 \
    --latest_entry 2022-03-01
```

Ignore any entries in the live feed;

```shell
python3 history4feed.py \
    --url https://www.schneier.com/feed/atom/ \
    --earliest_entry 2023-07-01 \
    --ignore_live_feed_entries
```

And include current entries;

```shell
python3 history4feed.py \
    --url https://www.schneier.com/feed/atom/ \
    --earliest_entry 2023-07-01
```

## RSS Time range

```shell
python3 history4feed.py \
    --url https://www.hackerone.com/blog.rss \
    --earliest_entry 2023-01-01 \
    --latest_entry 2023-01-05
```

## RSS Time range

```shell
python3 history4feed.py \
    --url https://arstechnica.com/tag/security/feed/ \
    --earliest_entry 2023-01-01
```

## Feedburner (ATOM)

```shell
python3 history4feed.py \
    --url https://feeds.feedburner.com/govtech/blogs/lohrmann_on_infrastructure \
    --earliest_entry 2023-06-01
```