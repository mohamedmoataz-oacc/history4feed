## Basics of RSS

RSS stands for Really Simple Syndication. Simply put, RSS is a standardized format using a computer (and human) readable format that shows what has changed for a website, and is especially used by blogs, podcasts, news sites, etc, for this reason.

Here is a sample of an RSS feed from The Record by the Recorded Future team; `https://therecord.media/feed/`.

Note, in many cases a blog will clearly show their RSS (or ATOM) feed URL, but not all. Whilst not all blogs have RSS feeds, if you open up a browser, navigate to the blog, and click view page source, you can usually find the feed address under the `link rel="alternate" type="application/rss+xml"` or `application/atom+xml` HTML tag.

The Recorded Future RSS feed shows all articles from the blog. The Record also allow you to subscribe to RSS feeds by category. For example, to the Cyber Crime category;

```shell
https://therecord.media/news/cybercrime/feed/
```

Generally an RSS feed has an XML structure containing at least the following items;

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">

<channel>
  <title>W3Schools Home Page</title>
  <link>https://www.w3schools.com</link>
  <description>Free web building tutorials</description>
  <item>
    <title>RSS Tutorial</title>
    <link>https://www.w3schools.com/xml/xml_rss.asp</link>
    <description>New RSS tutorial on W3Schools</description>
    <pubDate>Tue, 03 Jun 2003 09:39:21 GMT</pubDate>
  </item>
  <item>
    <title>XML Tutorial</title>
    <link>https://www.w3schools.com/xml</link>
    <description>New XML tutorial on W3Schools</description>
    <pubDate>Tue, 10 Jun 2003 11:34:12 GMT</pubDate>
  </item>
</channel>

</rss>
``` 

The `<channel>` tags capture the entire feed including metadata about the feed (`title`, `link`, and `description` in this case). There are many other optional elements that can be included in the `<channel>` tags, [as defined here](https://www.rssboard.org/rss-specification).

Each article in the feed is defined inside each `<item>` tag with sub-elements, generally the most important being:

* `title`: The title of the post / article
* `link`: The URL of the post / article
* `description`: The article content
* `pubDate`: The date the article was published

There are many other optional elements that can be included in the `<item>` tags, [as defined here](https://www.rssboard.org/rss-specification).

## Basics of ATOM

Atom is a similar format to RSS and used for the same reasons. It is a slightly newer format than XML (although almost 20 years old) and designed to cover some of the shortcomings of RSS.

[Here is a sample of an RSS feed from the 0patch blog](https://blog.0patch.com/feeds/posts/default).

An ATOM feed has a similar XML structure to RSS, however, you will notice some of the element names are different.

```xml
  <?xml version="1.0" encoding="utf-8"?>
   <feed xmlns="http://www.w3.org/2005/Atom">

     <title>Example Feed</title>
     <link href="http://example.org/"/>
     <updated>2003-12-13T18:30:02Z</updated>
     <author>
       <name>John Doe</name>
     </author>
     <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>

     <entry>
       <title>Atom-Powered Robots Run Amok</title>
       <link href="http://example.org/2003/12/13/atom03"/>
       <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
       <published>2003-12-13T18:30:02Z</published>
       <updated>2003-12-13T18:30:02Z</updated>
       <title>Something</title>
       <content>Some text.</content>
     </entry>
   </feed>
```

The blog information is captured at the top of the document.

Each article in the feed is defined inside each `<entry>` tag with sub-elements, generally the most important being:

* `title`: The title of the post / article
* `id`: The UUID of the post
* `link`: The URL of the post / article
* `published`: The date the article was published
* `content`: The article content

There are many other optional elements that can be included in the `<item>` tags, [as defined here](https://validator.w3.org/feed/docs/atom.html).

## The solution

There are two ways I came up with to get historic posts from a blog;

1. Scrape the blog for historic posts. This is the most accurate way to do it, though given the different structure of blogs and websites, this can become complex, requiring a fair bit of manual scraping logic to be written for each blog you want to follow
2. [Inspired by this Reddit thread](https://www.reddit.com/r/webscraping/comments/zxduid/python_library_to_scrape_rssfeeds_from/), use the Wayback Machine's archive. Often the Wayback Machine will have captured snapshots of a feed (though not always). For example, `https://therecord.media/feed/` has been captured [187 times between November 1, 2020 and August 12, 2022](https://web.archive.org/web/20220000000000*/https://therecord.media/feed/).

Whilst the Wayback Machine will completely miss some blog archives, a particular problem for smaller sites that are less likely to be regularly indexed by the WBM), and potentially miss certain feed items where the RSS feed updates faster the WBM re-indexes the site, I chose this approach as it is currently the most scalable way I could come up with to backfill history (and most of the requirements for my use-cases were from high profile sites with a fairly small publish rate).

[Waybackpack](https://github.com/jsvine/waybackpack) is a command-line tool that lets you download the entire Wayback Machine archive for a given URL for this purpose.

Here is an example of how to use it with The Record Feed;

```shell
python3 -m venv tutorial_env
source tutorial_env/bin/activate
pip3 install waybackpack
waybackpack https://therecord.media/feed/ -d ~/Downloads/therecord_media_feed --from-date 2015 --uniques-only  
```

In the above command I am requesting all unique feed pages downloaded by the Wayback Machine (`--uniques-only `) from 2015 (`--from-date 2015`) from the feed URL (`https://therecord.media/feed/`)

Which produces about 100 unique `index.html` files (where `index.html` is the actual RSS feed). They are nested in folders named with the index datetime (time captured by WBM) in the format `YYYYMMDDHHMMSS` like so;

```

~/Downloads/therecord_media_feed
├── 20220808162900
│   └── therecord.media
│       └── feed
│           └── index.html
├── 20220805213430
│   └── therecord.media
│       └── feed
│           └── index.html
...
└── 20201101220102
    └── therecord.media
        └── feed
            └── index.html
```

It is important to point out unique entries just mean the `index.html` files have at least one difference. That is to say, much of the file can actually be the same (and include the same articles). Also whilst saved as .html documents, the content is actually pure .xml.

Take `20220808162900 > therecord.media > index.html` and `20220805213430 > therecord.media > index.html`

Both of these files contain the same item;

```xml
<item>
    <title>Twitter confirms January breach, urges pseudonymous accounts to not add email or phone number</title>
    <link>https://therecord.media/twitter-confirms-january-breach-urges-pseudonymous-accounts-to-not-add-email-or-phone-number/</link>
```

history4feed looks at all unique `<link>` elements in the downloaded `index.html` files to find the unique `<items>`s.

Note, this blog is in RSS format. 

Here's another example, this time using an ATOM feed as an example;

```shell
waybackpack https://www.schneier.com/feed/atom/ -d ~/Downloads/schneier_feed --from-date 2015 --uniques-only  
```

Looking at a snippet from one of the `index.html` files;

```xml
    <entry>
        <author>
            <name>Bruce Schneier</name>
        </author>
        <title type="html"><![CDATA[Friday Squid Blogging: Vegan Chili Squid]]></title>
        <link rel="alternate" type="text/html" href="https://www.schneier.com/blog/archives/2021/01/friday-squid-blogging-vegan-chili-squid.html" />
        <id>https://www.schneier.com/?p=60711</id>
        <updated>2021-01-04T16:50:54Z</updated>
        <published>2021-01-22T22:19:15Z</published>
```

Here, history4feed looks at the `<link href` value to find the unique entries between each `index.html`.

## Dealing with partial content in feeds

The `description` field (in RSS feeds) and `content` field (in ATOM feeds) can contain the entirety of the raw article, including the html formatting. You can see this in The Record's RSS feed. Sometime the HTML content is decoded or encoded.

However, some blogs choose to use snippets in their RSS feed content. For example, choosing only to include the first paragraph - requiring a subscriber to read the full content outside of their feed aggregator.

I wanted to include a full-text feed in the historical output created by history4feed.

To do this, once a historical feed is created, the feed is passed to the [readability-lxml library](https://pypi.org/project/readability-lxml/).

history4feed takes all the source URLs (either `<link>` property value in the `<entry>` or `<item>` tags) for the articles in the feeds and passes them to readability-lxml.

The result is then reprinted in the `description` or `content` field depending on feed type, overwriting the potentially partial content that it originally contained.

Note, history4feed cannot detect if a feed is full or partial so will always request the full content for all items via readability-lxml, regardless of whether the feed content is partial or full.

## Dealing with encoding in post content

Content in feed `description` or `content` (that is, the actual post) is typically printed in one of two ways, either;

* encoded html ASCII: this is a safe way to handle HTML inside the RSS/ATOM XML data. All HTML symbols are encoded, e.g. `<` is printed as `&lt;`, so as to not escape the XML tags
* decoded html: this can be thought of as raw HTML. That is, it contains all HTML tags unmodified. This is useful to have, but can cause issues inside XML. Decoded HTML is printed inside `CDATA` tags so that it does not escape XML.

history4feed can handle all above scenarios.

Depending on the input, history4feed converts the encoding of the input to create another versions of the post in the output;

* `posts.description_encoded`: ASCII encoded version of post content
* `posts.description_decoded`: html decoded version of the post content (with CDATA tags)

## Live feed data (data not from wayback machine)

In addition to the historical feed information pulled by the Wayback Machine, history4feed also includes the latest posts in the live feed URL.

Live feed data always takes precedence. history4feed will remove duplicate entries found in the Wayback Machine response, and will instead use the live feed version by default.

## Rebuilding the feed (for `blog.full_rss`) in API download links

history4feed converts all feeds and their content into a single RSS formatted XML file, stored in the `blog.full_rss` database field.

The RSS files for each feed contain a simplified header;

```xml
<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">

        <channel>

            <title>BLOG.TITLE</title>
            <description>BLOG.DESCRIPTION</description>
            <link>BLOG.URL</link>
            <lastBuildDate>BLOG.MODIFIED</lastBuildDate>
            <generator>https://www.github.com/history4feed</generator>
            
            <ITEMS></ITEMS>

        </channel>

    </rss>
```

Each item is rebuilt as follows;

```xml
            <item>
                <title>POST.TITLE</title>
                <description>POST.DESCRIPTION_DECODED</description>
                <link>POST.LINK</link>
                <pubDate>POST.CREATED</pubDate>
                <author>POST.AUTHOR</author>
                <category>POST.CATEGORY</category>
            </item>
```

The order of the RSS feed is in descending time order, that is, it starts with the latest entry first.

## Dealing with feed validation on input

ATOM feeds are XML documents. ATOM feeds can be validated by checking for the header tags where `<feed` tag contains the text `atom` somewhere inside it, e.g. https://www.schneier.com/feed/atom/

RSS feeds are very similar to ATOM in many ways. RSS feeds can be validated as they contain an `<rss>` tag in the header of the document. e.g. https://www.hackread.com/feed/

Feeds are validated to ensure they contain this data before any processing is carries out.

For example, https://github.com/signalscorps/history4feed/ is not an RSS or ATOM feed, so would return an error.

This is used to populated the `feed.type` value in the database.

## Dealing with IP throttling during full text requests

Many sites will stop robotic request to their content. As the full text function of history4feed relies on accessing each blog post individually this can result in potentially thousands of requests to the Wayback Machine and which have a high risk of being blocked.

history4feed has two potential workarounds to solve this problem;

### 1. Use a proxy

history4feed supports the use of [ScrapFly](https://scrapfly.io/).

This is a paid service ([with a free tier](https://scrapfly.io/pricing)). In my own research, its the best proxy for web scraping.

You will need to register for an account and grab your API key.

Note, due to many site blocking access to Russian IPs, the request includes the following proxy locations only;

```shell
country=us,ca,mx,gb,fr,de,au,at,be,hr,cz,dk,ee,fi,ie,se,es,pt,nl
```

### 2. Use inbuilt app settings

It's best to request only what you need, and also slow down the rate at which the content is requested (so the request look more like a human).

history4feed supports the following options;

* sleep times: sets the time between each request to get the full post text
* time range: an earliest and latest post time can be set, reducing the number of items returned in a single script run. Similarly, you can reduce the content by ignoring entries in the live feed.
* retries: by default, when in full text mode history4feed will retry the page a certain number of times in case of error. If it still fails after retries count reached, the script will fail. You can change the retries as you require.

## A note on error handling

Due to the way old feeds are pulled from WBM, it is likely some will now be deleted (404s). Similarly, the site might reject requests (403's -- see proxy use as a solution to this).

history4feed will soft handle these errors and log the failure, including the HTTP status code and the paticular URL that failed. You can view the logs for each run in the `logs/` directory.

This means that if it's required you can go back and get this post manually. However, one limitation of soft error handling is you won't be able to do this using the same history4feed install though.

## Storage in the database

history4feed uses a lightweight sqllite database to store input and output to power the API responses.

The database has a structure like so;

* feed (determined by each feed URL) -- contains the history4feed settings entered
* blog (determined by each feed URL) -- contains the blog information
    * post (each post belonging to feed) -- includes all post data for the blog

Because their are differences in feed content fields, they are normalised in the database. The databases tables have the following fields;

### Feeds table

This holds all metadata about feeds entered by a user when configuring it;

* `feed.id`: uuidv4 internal id assigned by history4feed on user entry
* `feed.type`: autodetected, either RSS or ATOM based on feed content
* `feed.url`: url entered by user 
* `feed.created`: datetime user created the feed
* `feed.last_run`: date of last run for data. Will update with every run (if latest_entry not set)
* `feed.retries`: retry value entered by user (or the default value)
* `feed.sleep_seconds`: sleep time entered by user (or the default value)
* `feed.earliest_entry`: date of earliest feed entered by user (blank if not value entered)
* `feed.latest_entry`: date of latest feed entered by user (blank if not value entered)
* `feed.ignore_live_feed_entries`: boolean, if `ignore_live_feed_entries` was set to true
* `feed.pretty`: boolean, if `full_text_pretty` was set to true

### Blog table

This is the information about the blog that published the post. Some of the information here is used in the final RSS output for the header information;

* `blog.id`: uuidv4 internal id assigned by history4feed
* `blog.feed_id`: uuidv4 internal id assigned by history4feed (links entry to feed table)
* `blog.title`: title of the blog, taken from the ATOM/RSS feed of the blog
* `blog.description`: description of the blog, taken from the ATOM/RSS feed of the blog
* `blog.url`: URL of the blog, taken from the ATOM/RSS feed of the blog (not the user input)
* `blog.latest_post`: autogenerated datetime of latest (newest) post in feed
* `blog.earliest_post`: autogenerated datetime of earliest (oldest) post in feed
* `blog.full_rss`: an RSS payload containing all posts created for that feed

### Posts table

* `post.id`: uuidv4 internal id assigned by history4feed
* `post.blog_id`: uuidv4 internal id assigned by history4feed (links entry to blog table)
* `posts.title`: title of post (in feed)
* `post.link`: link of post (in feed)
* `post.created`: created time of post (in feed)
* `post.author`: post author (in feed)
* `post.[categories]`: categories of post (in feed)
* `posts.description_encoded`: ASCII encoded version of post content
* `posts.description_decoded`: html decoded version of the post content

## Checking for feed updates

history4feed will check for updates to existing feeds URLs in the database each time the script is executed without any flags.

On updates, history4feed will check for posts not already indexed (it will search for posts with a date greater than `blog.latest_post`)

The same precedent applies as for the first run; if an item has been ingested already using the live feed, it will not be replaced by the Wayback Machine version.

## Cyber-security focused RSS/ATOM feeds

Signals Corps build threat intelligence software.

Check out our Awesome Threat Intel Feeds repository for a list of RSS and ATOM feeds we follow that publish threat intelligence related content:

https://github.com/signalscorps/awesome-threat-intel-rss