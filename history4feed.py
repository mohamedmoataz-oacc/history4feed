import argparse
import sys
import time
from datetime import datetime, date, time as dt_time, timezone
from io import BytesIO, StringIO
from xml.dom.minidom import Document, Element, parse

from pathlib import Path
import sqlite3, os, uuid
import waybackpack, requests
from dateutil.parser import parse as parse_date
from readability import Document as ReadabilityDocument
from tqdm.auto import tqdm
import itertools, json, hashlib
import brotli
import logging
from types import SimpleNamespace
from typing import Any
from dotenv import load_dotenv


LINK_TO_SELF = "https://github.com/signalscorps/history4feed"
LOG_PRINT = 105
DEFAULT_USER_AGENT = "History4Feed"

class Session(object):
    def __init__(
        self,
        follow_redirects=False,
        user_agent=DEFAULT_USER_AGENT,
        max_retries=3,
        sleep_seconds=1
    ):
        self.follow_redirects = follow_redirects
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.sleep_seconds = sleep_seconds

    def get(self, url, **kwargs):
        headers = {
            "User-Agent": self.user_agent,
        }
        response_is_final = False
        retries = 0
        while not response_is_final:
            res = requests.get(
                url,
                allow_redirects=self.follow_redirects,
                headers=headers,
                stream=True,
                **kwargs
            )

            if res.status_code != 200:
                logger.info("HTTP status code: {0}".format(res.status_code))

            if int(res.status_code / 100) in [4, 5]:  # 4XX and 5XX codes
                logger.info("Waiting 1 second before retrying.")
                retries += 1
                if retries <= self.max_retries:
                    logger.info("Waiting 1 second before retrying.")
                    time.sleep(self.sleep_seconds)
                    continue
                else:
                    logger.print(f"Maximum retries reached for `{url}`, skipping.")
                    return res
            else:
                response_is_final = True
        return res



def newLogger(name: str) -> logging.Logger:
    # Configure logging
    logging.addLevelName(LOG_PRINT, "LOG")
    stream_handler = logging.StreamHandler()  # Log to stdout and stderr
    stream_handler.setLevel(LOG_PRINT)
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [%(levelname)s] %(message)s",
        handlers=[stream_handler],
        datefmt='%d-%b-%y %H:%M:%S'
    )
    logger = logging.getLogger("History4Feed")
    logger.print = lambda msg: logger.log(LOG_PRINT, msg)
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(logs_dir/datetime.now().strftime('log_%Y_%m_%d-%H_%M.log'), "w")
    handler.formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    handler.setLevel(logging.NOTSET)
    logger.addHandler(handler)
    logger.print("=====================History4Feed======================")

    return logger

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

logger = newLogger(__name__)

class NoneDict(dict):
    def __getitem__(self, __key: Any) -> Any:
        try:
            return super().__getitem__(__key)
        except:
            return None

class FeedEntry(dict):
    element: Element = None
    author = ''
    type = 'rss'
    _id = None
    link = title = description = None

    def __init__(self, elem, link, blog_id=None):
        if not elem:
            return
        if isinstance(elem, str):
            elem = parse(StringIO(elem)).firstChild
        self.element = elem
        self.link = link
        self.title = getText(getFirstElementByTag(elem, "title"))
        self.created = get_publish_date(elem)
        self.added = datetime.now(timezone.utc)
        self.author = get_author(elem)
        self.categories = json.dumps(get_categories(elem))
        self.blog_id = blog_id

    def build_entry_element(self):
        d = Document()
        element = d.createElement('item')
        element.appendChild(createTextElement(d, "title", self.title))
        link = createTextElement(d, "link", self.link)
        link.setAttribute("href", self.link)
        element.appendChild(link)
        element.appendChild(createTextElement(d, "pubDate", self.created.isoformat()))
        element.appendChild(createTextElement(d, "description", self.description))


        for category in json.loads(self.categories):
            element.appendChild(createTextElement(d, "category", category))

        if self.author:
            author = d.createElement('author')
            author.appendChild(createTextElement(d, "name", self.author))
            element.appendChild(author)
        return element
        
    @property
    def id(self):
        if not self._id:
            # self._id = hashlib.sha512((self.link+str(self.blog_id)).encode()).hexdigest()
            self._id = str(uuid.uuid4())
        return self._id

    @property
    def description_decoded(self):
        return self.description
    @description_decoded.setter
    def description_decoded(self, value):
        self.description = value

    @property
    def raw_xml(self):
        return self.element.toxml()

    @property
    def description_encoded(self):
        return self.description

    def items(self):
        return self.__dict__

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except BaseException as e:
            raise KeyError(key) from e

    def set_from_dict(self, dct: dict):
        for k, v in dct.items():
            setattr(self, k, v)

def createTextElement(document: Document, tagName, text):
    el = document.createElement(tagName)
    txtNode = document.createTextNode(text or "")
    el.appendChild(txtNode)
    return el

def createRSSHeader(feed_data):
    d = Document()
    rss = d.createElement("rss")
    d.appendChild(rss)
    rss.setAttribute("version", "2.0")
    channel = d.createElement("channel")
    rss.appendChild(channel)
    channel.appendChild(createTextElement(d, "title", feed_data["title"]))
    channel.appendChild(createTextElement(d, "description", feed_data["description"]))
    channel.appendChild(createTextElement(d, "link", feed_data["url"]))
    channel.appendChild(createTextElement(d, "lastBuildDate", datetime.now(timezone.utc).isoformat()))
    channel.appendChild(createTextElement(d, "generator", LINK_TO_SELF))
    return d, channel

class DBHelper:
    DEFAULT_PATH = "history4feed.sqlite"
    def __init__(self, db_path: Path = None) -> None:
        if not db_path:
            db_path = self.DEFAULT_PATH
        self.db_path = db_path
        self.initialize_database()

    def initialize_database(self):
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create Feeds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Feed (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    url TEXT,
                    created TEXT,
                    last_run TEXT,
                    retries INTEGER,
                    sleep_seconds REAL,
                    earliest_entry TEXT,
                    latest_entry TEXT,
                    ignore_live_feed_entries BOOLEAN,
                    pretty BOOLEAN,
                    UNIQUE (id)
                )
            ''')

            # Create Blog table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Blog (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    url TEXT,
                    latest_post   TEXT,
                    earliest_post   TEXT,
                    full_rss TEXT,
                    FOREIGN KEY(id) REFERENCES Feed(id) ON DELETE CASCADE,
                    UNIQUE (id)
                )
            ''')

            # Create Posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Post (
                    id TEXT PRIMARY KEY,
                    blog_id TEXT,
                    title TEXT,
                    link TEXT,
                    author TEXT,
                    created TEXT,
                    added TEXT,
                    categories TEXT,
                    description TEXT,
                    raw_xml TEXT,
                    FOREIGN KEY(blog_id) REFERENCES Blog(id) ON DELETE CASCADE,
                    UNIQUE (id)
                )
            ''')

            conn.commit()
            conn.close()

    def add_blog(self, blog, feed_id):
        blog['id'] = blog['feed_id'] = feed_id
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        now = self.json_serialize(datetime.now(timezone.utc))
        cursor.execute(f'''
            INSERT OR REPLACE INTO Blog VALUES (:id, :title, :description, :url, :latest_post, :earliest_post, :full_rss);
        ''', NoneDict(blog))
        cursor.execute(f"""
            UPDATE Feed
                SET last_run = ?
                WHERE id = ?
        """, (datetime.now(timezone.utc), feed_id))
        conn.commit()
        conn.close()

    def delete_feed(self, feed_url):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        conn.executescript('PRAGMA foreign_keys = ON;') #needed for cascade to work

        cursor.execute("""
            DELETE FROM Feed
                WHERE url = ?
        """, (feed_url,))
        conn.commit()
        conn.close()

    def get_feed_by_url(self, url):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        feed_id = None
        cursor.execute("SELECT * from Feed where url = ?", (url,))
        cursor.row_factory = sqlite3.Row
        feed = cursor.fetchone()
        conn.commit()
        conn.close()
        return feed

    def add_feed(self, feed_settings, feed_type):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        now = self.json_serialize(datetime.now(timezone.utc))
        feed_settings['created']  = now
        feed_settings['last_run'] = now
        feed_settings['type']     = feed_type
        cursor.execute(f'''
            INSERT INTO Feed VALUES (:id, :type, :url, :created, :last_run, :retries, :sleep_seconds, :earliest_entry, :latest_entry, :ignore_live_feed_entries, :pretty);
        ''', NoneDict(feed_settings))
        conn.commit()
        conn.close()
        return feed_settings['id']

    def add_posts(self, posts: list[FeedEntry]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        feed_id = None
        now = self.json_serialize(datetime.now(timezone.utc))
        cursor.executemany(f'''
            INSERT OR REPLACE INTO Post VALUES (:id, :blog_id, :title, :link, :author, :created, :added, :categories, :description, :raw_xml);
        ''', posts)
        conn.commit()
        conn.close()

    def get_posts(self, blog_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        now = self.json_serialize(datetime.now(timezone.utc))
        cursor.execute(f'''
            SELECT * FROM Post WHERE blog_id = ?;
        ''', (blog_id,))
        cursor.row_factory = sqlite3.Row
        resp = cursor.fetchall()
        conn.commit()
        conn.close()
        return resp

    def get_feed_list(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(f'''
            SELECT 
                Feed.id AS feed_id,
                type AS feed_type,
                Feed.url AS feed_url,
                last_run,
                Blog.earliest_post AS earliest_post,
                Blog.latest_post AS latest_post,
                ignore_live_feed_entries,
                earliest_entry,
                latest_entry,
                full_rss
            FROM
                Feed
            INNER JOIN Blog ON Blog.id = Feed.id
            ;
        ''')
        resp = cursor.fetchall()
        conn.commit()
        conn.close()
        return resp

    def get_blog(self, blog_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # find out if feed already exists in database
        now = self.json_serialize(datetime.now(timezone.utc))
        cursor.execute(f'''
            SELECT latest_post, full_rss FROM Blog WHERE id = ?;
        ''', (blog_id,))
        resp = cursor.fetchone()
        if resp:
            d, full_rss = resp
            d = d and parse_date(d)
        conn.commit()
        conn.close()
        return d, full_rss

    @staticmethod
    def json_serialize(obj):
        if isinstance(obj, (datetime, date, dt_time)):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return str(obj)

class History4FeedException(Exception):
    pass
class UnknownFeedtypeException(History4FeedException):
    pass
class ParseArgumentException(History4FeedException):
    pass


def getText(nodelist: list[Element]):
    if not nodelist:
        return ''
    if not isinstance(nodelist, list):
        nodelist = nodelist.childNodes
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getFirstElementByTag(node, tag):
    if not node:
        return None
    elems = node.getElementsByTagName(tag)
    return (elems or None) and elems[0]

def getFirstChildByTag(node: Element, tag):
    child = None
    for c in node.childNodes:
        if c.nodeName == tag:
            child = c
            break
    return child

class FetchRedirect(History4FeedException):
    pass

def fetch_page(session, url) -> bytes:
    proxy_apikey = os.getenv("SCRAPFILE_APIKEY")
    
    if proxy_apikey:
        logger.info(f"Fetching `{url}` via scrapfile.io")
        resp = session.get("https://api.scrapfly.io/scrape", params=dict(key=proxy_apikey, url=url, country="us,ca,mx,gb,fr,de,au,at,be,hr,cz,dk,ee,fi,ie,se,es,pt,nl"))
        result = SimpleNamespace(**resp.json()['result'])
        if result.status_code > 399:
            raise History4FeedException(f"PROXY_GET Request failed for `{url}`, status: {result.status_code}, reason: {result.status}")
        elif result.status_code > 299:
            raise FetchRedirect(f"PROXY_GET for `{url}` redirected, status: {result.status_code}, reason: {result.status}")
        return result.content.encode()

    logger.info(f"Fetching `{url}`")
    resp  = session.get(url)
    if not resp.ok:
        raise History4FeedException(f"GET Request failed for `{url}`, status: {resp.status_code}, reason: {resp.reason}")

    # some times, wayback returns br encoding, try decompressing
    try:
        return brotli.decompress(resp.content)
    except:
        pass
    return resp.content

def get_publish_date(item):
    published = getFirstElementByTag(item, "published")
    if not published:
        published = getFirstElementByTag(item, "pubDate")
    return parse_date(getText(published))

def get_categories(entry: Element) -> list[str]:
    categories = []
    for category in entry.getElementsByTagName('category'):
        cat = category.getAttribute('term') or getText(category)
        if not cat:
            cat = category
        categories.append(cat)
    return categories

def get_author(item):
    author = getFirstElementByTag(item, "dc:creator")
    if not author:
        author = getFirstElementByTag(getFirstElementByTag(item, "author"), "name")
    return getText(author)

# Function to extract namespaces from a node
def get_namespaces(node):
    namespaces = {}
    for attr in (node.attributes or {}).values():
        if attr.name.startswith("xmlns:"):
            prefix = attr.name.split(":")[1]
            namespaces[prefix] = attr.value
    return namespaces

def get_entries(document: Document, feed_type: str, blog_id) -> dict[str, FeedEntry]:
    entries = {}
    if feed_type == "atom":
        for item in document.getElementsByTagName("entry"):
            link = getAtomLink(item, rel='alternate')

            entries[link] = FeedEntry(item, link, blog_id=blog_id)
    elif feed_type == "rss":
        channel = getFirstElementByTag(document, "channel")
        for item in channel.getElementsByTagName("item"):
            link = getText(getFirstElementByTag(item, "link")).strip()

            entries[link] = FeedEntry(item, link, blog_id=blog_id)
    return entries

def retrieve_feed(url, from_date, to_date, args=None, db: DBHelper=None, is_update=False):
    session = Session(
        user_agent="curl",
        follow_redirects=True,
        max_retries=3,
    )

    feed_type: str = None
    entries = {} #put items in dict using url as key to eliminate duplicates
    # do initial feed validation
    try:
        content = fetch_page(session, url)
        live_doc, feed_metadata, feed_type = parse_xml(content, url)
        namespaces = get_namespaces(live_doc.firstChild)
    except History4FeedException:
        raise

    feed_setting = {'id': str(uuid.uuid4()), 'url': url}
    if not is_update:
        feed_setting.update(args.__dict__)

    newlycreated = True
    if feed := db.get_feed_by_url(url):
        newlycreated = False
        feed_setting.update(feed)
    feed_id = feed_setting['id']
    
    
    new_posts = {}

    session.max_retries = int(feed_setting['retries'] or 0)
    db_doc = None
    if not newlycreated:
        if not is_update:
            raise History4FeedException(f"Conflicting entry for `{feed_setting['url']}`.")
        latest_entry, db_xml = db.get_blog(feed_id)
        if not latest_entry or not db_xml:
            latest_entry = parse_date(feed_setting["earliest_entry"])
        else:
            db_doc, _, _ = parse_xml(db_xml, f"db:blog_id={feed_id}")
            namespaces.update(get_namespaces(db_doc.firstChild))
        from_date = latest_entry.strftime('%Y%m%d')
        to_date   = datetime.now(timezone.utc).strftime('%Y%m%d')
        latest_post, earliest_post, full_rss = args.latest_post, args.earliest_post, args.full_rss

    results = waybackpack.search(url, from_date=from_date, to_date=to_date, uniques_only=True, session=session)
    timestamps = [
            entry['timestamp'] for entry in results 
                    # if int(entry['statuscode'])<300 #skip redirects
        ]
    document = None
    
    if timestamps:
        pack = waybackpack.Pack(url, timestamps, uniques_only=True, session=session)
        for i, asset in tqdm(enumerate(pack.assets), "Retrieving archived feeds", len(pack.assets), unit='feed', colour='green'):
            url = asset.get_archive_url("id_")
            try:
                content = fetch_page(session, url)
                document, _, feed_type = parse_xml(content, asset.timestamp)
                namespaces.update(get_namespaces(document.firstChild))
                entries.update(get_entries(document, feed_type, feed_id))
            except BaseException as e:
                logger.print(f"failed to retrieve archive from `{url}` into fulltext")
                logger.error("", exc_info=True)

    if args.ignore_live_feed_entries and not entries:
        raise Exception("No Wayback Machine archive exists for this blog. Please use live feed.")


    live_entries = get_entries(live_doc, feed_type, feed_id)
    filter_date1 = datetime.strptime(from_date, "%Y%m%d").date()
    filter_date2 = datetime.strptime(to_date, "%Y%m%d").date()
    # entries.update(live_entries)
    if feed_setting['ignore_live_feed_entries']:
        for link in live_entries.keys():
            entries.pop(link, None)
    else:
        entries.update(live_entries)
        document = live_doc
    db_entries ={}
    if db_doc: #add old entries after processing into full text to avoid reretrieving
        db_entries = get_entries(db_doc, "rss", feed_id)
        entries.update(db_entries)

    for k, v in entries.items():
        if db_entries.get(k) is None:
            new_posts[k] = v

    new_posts = filter_posts_by_dates(new_posts.values(), latest_entry=filter_date2, earliest_entry=filter_date1)

    if new_posts:
        process_into_full_text(session, new_posts, feed_type, feed_setting['sleep_seconds'])
        logger.print(f"Processed {len(new_posts)} posts into full text")


        filtered_entries = filter_posts_by_dates(entries.values(), latest_entry=filter_date2, earliest_entry=filter_date1)
        #generate feed        
        filtered_entries = sorted(filtered_entries, key=lambda x: x.created, reverse=True)
        earliest_post, latest_post = filtered_entries[-1].created, filtered_entries[0].created
        out, channel = createRSSHeader(feed_metadata)
        for feed_entry in filtered_entries:
            channel.appendChild(feed_entry.build_entry_element())

        if feed_setting['pretty']:
            full_rss = out.toprettyxml()
        else:
            full_rss = out.toxml()
    else:
        earliest_post, latest_post, full_rss = None, None, None
        logger.print(f"No new posts for `{url}`")

    feed_metadata.update(earliest_post=earliest_post, latest_post=latest_post, full_rss=full_rss)
    if newlycreated:
        feed_id = db.add_feed(feed_setting, feed_type.upper())
    db.add_blog(feed_metadata, feed_id)
    db.add_posts(new_posts)

def getAtomLink(node: Element, rel='self'):
    links = [child for child in node.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName in ['link', 'atom:link']]
    
    link = links[0]
    for l in links:
        if l.attributes['rel'].value == rel:
            link = l
            break
    return link.attributes['href'].value

def process_into_full_text(session, entries: dict[str, FeedEntry], feed_type: str, sleep_seconds: float) -> Document:
    is_atom = feed_type == "atom"
    d = Document()
    for i, entry in tqdm(enumerate(entries), "Processing into full text", len(entries), unit='entry', colour='green'):
        try:
            fulltext = get_full_text(session, entry.link)
            element: Element = entry.element
            textnode = d.createCDATASection(fulltext)

            if is_atom:
                content = getFirstElementByTag(element, "content")
            else:
                content = getFirstElementByTag(element, "description")
            content = content or SimpleNamespace(tagName="description")
            newcontent: Element = d.createElement(content.tagName)
            newcontent.appendChild(textnode)
            newcontent.setAttribute("type", "html")
            element.replaceChild(newcontent, content)
            entry.description_decoded = fulltext
            time.sleep(sleep_seconds)
        except BaseException as e:
            logger.print(f"failed to process `{entry.link}` into fulltext")
            logger.error("", exc_info=True)
    return entries

def parse_xml(data, timestamp) -> tuple[Document, str]:
    try:
        feed_type = None
        feed_data = {}
        if isinstance(data, str):
            document = parse(StringIO(data))
        else:
            document = parse(BytesIO(data))
        # check if it's atom or rss
        if rss := getFirstElementByTag(document, "rss"):
            channel = getFirstElementByTag(rss, "channel")
            feed_data['description'] = getText(getFirstElementByTag(channel, "description"))
            feed_data['title'] = getText(getFirstElementByTag(channel, "title"))
            feed_data['url'] = getText(getFirstElementByTag(channel, "link"))

            feed_type = "rss"
        elif feed := getFirstElementByTag(document, "feed"):
            feed_data['description'] = getText(getFirstElementByTag(feed, "description"))
            feed_data['title'] = getText(getFirstElementByTag(feed, "title"))
            feed_data['url'] = getAtomLink(feed)

            feed_type = "atom"
        else:
            raise UnknownFeedtypeException()
        return document, feed_data, feed_type
    except BaseException as e:
        raise UnknownFeedtypeException(f"Failed to parse feed from `{timestamp}`") from e

def get_full_text(session, link):
    try:
        page = fetch_page(session, link)
        doc  = ReadabilityDocument(page, url=link)
        return doc.summary()
    except BaseException as e:
        raise History4FeedException(f"Error processing fulltext: {e}") from e

def filter_posts_by_dates(entries: list[FeedEntry], earliest_entry=None, latest_entry=None) -> list[FeedEntry]:
    filtered_entries : list[FeedEntry] = []
    # filter entries by --latest_entry
    for feed_entry in entries:
        if (latest_entry and feed_entry.created.date() > latest_entry) or (earliest_entry and feed_entry.created.date() < earliest_entry):
            continue
        filtered_entries.append(feed_entry)
    return filtered_entries

def parse_date_arg(date: str, name="date") -> str:
    if not date:
        return None
    try:
        return datetime.fromisoformat(date).strftime('%Y%m%d')
    except:
        raise ParseArgumentException(f"Unable to parse {name}={date} as a date")

def update_all(db: DBHelper):
    feeds = db.get_feed_list()
    logger.print(f"Updating {len(feeds)} feeds")
    for i, feed in enumerate(feeds):
        args = SimpleNamespace(**feed)
        try:
            if args.latest_entry:
                logger.print(f"Skipping #{i+1} of {len(feeds)}")
                continue
            logger.print(f"Updating #{i+1} of {len(feeds)} feeds, url:{feed['feed_url']}")
            retrieve_feed(feed['feed_url'], "2000-01-01", "2000-01-01",  args=args, db=db, is_update=True)
        except BaseException as e:
            logger.print(f"Update blog failed for `{args.feed_url}`")
            logger.error("", exc_info=True)

def main(args):
    db = DBHelper()
    earliest_entry = parse_date_arg(args.earliest_entry, "--earliest_entry")
    latest_entry = parse_date_arg(args.latest_entry or datetime.now(timezone.utc).isoformat(), "--latest_entry")
    # print("args:", args)
    if args.list:
        feed_list = db.get_feed_list()
        if feed_list:
            print(",".join(tuple(feed_list[0].keys())[:6]))
        for feed in feed_list:
            print(",".join(map(str,tuple(feed)[:6])))
    elif args.url:
        if args.delete:
            db.delete_feed(args.url)
        else:
            document = retrieve_feed(args.url, earliest_entry, latest_entry,  args=args, db=db, is_update=False)
    else:
        update_all(db)
    

def parse_arguments():
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="history4feed.py - A script to fetch feed history.")
        
        # Define command-line arguments
        options1 = parser.add_mutually_exclusive_group(required=True)
        options1.add_argument("--url", help="(required): the URL of the RSS or ATOM feed, e.g. https://therecord.media/news/cybercrime/feed/. Note this will be validated to ensure the feed is in the correct format.")
        options1.add_argument("--list", action="store_true", help="show all existing feeds and the data held by each.")
        args, _ = parser.parse_known_args()


        options = parser.add_mutually_exclusive_group(required=bool(args.url))
        options.add_argument("--earliest_entry", help="(required): earliest record you want to scrap in format YYYY-MM-DD", default="2000-01-01")
        options.add_argument("--delete", action="store_true", help="if passed will delete the feed url entered and any feed entries associate with it from the database.")

        parser.add_argument("--full_text", "--full-text", action="store_true", help=" (optional): default is false. If passed, converts potentially partial feeds into full text feeds.")
        parser.add_argument("--pretty", action="store_true", help="(optional): default is false. If passed, XML output is pretty printed.")
        parser.add_argument("--retries", "--number_of_retries", default=3, help="(optional): default is 3. This is useful when --full_text is used for a large amount of posts are returned. This sets the number of retries when a non-200 response is returned.")
        parser.add_argument("--sleep_seconds", type=float, default=2, help="(optional): default is 0. This is useful when --full_text is used for a large amount of posts are returned. This sets the time between each request to get the full text of the article to reduce servers blocking robotic requests.")
        parser.add_argument("--latest_entry", help="(optional): Default is script run time. The latest record you want to scrap in format YYYY-MM-DD")
        parser.add_argument("--ignore_live_feed_entries", action="store_true", help="ignore any entries in the live feed URL entered")
        parser.add_argument("--full_text_decoded", action="store_true", help=" (optional): default is false. If passed, full text is wrapped in a CDATA section.")
        args = parser.parse_args()
    else:
        args = SimpleNamespace(earliest_entry="2000-01-01", latest_entry="2000-01-01", url=None, list=False)
    return args

if __name__ == "__main__":
    # Parse the command-line arguments
    args = parse_arguments()
    logger.info("arguments: %s"%str(args))
    try:
        load_dotenv(".env")
        main(args)
    except UnknownFeedtypeException as e:
        msg = "The URL entered does not resolve to a valid RSS or ATOM feed. Please enter a valid RSS or ATOM feed URL"
        logger.print(msg)
        logger.error("", exc_info=True)
        sys.exit(1)
    except Exception as e:
        # logger.error(e, exc_info=True)
        logger.print(f"Failed:\t{e}")
        logger.error("", exc_info=True)
        sys.exit(1)
