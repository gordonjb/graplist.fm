"""
Fetch cards from Cagematch and extract the wrestlers who were on that show
"""
from dataclasses import dataclass

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from url_loading import simple_get
import yaml
from enum import Enum
import sqlite3
from datetime import date
import argparse
import re

TYPE_FIELD = 'id'
ID_FIELD = 'nr'


class ContentType(Enum):
    WRESTLER = 2
    PROMOTION = 8
    TAG_TEAM = 28
    STABLE = 29


@dataclass
class Promotion:
    id: int
    name: str


@dataclass
class Show:
    show_id: str
    arena: str
    date: date
    show_name: str
    promotion: Promotion
    url: str


@dataclass
class Worker:
    id: str
    name: str


def create_tables():
    c.execute('''
        CREATE TABLE "promotions" (
            "promotion_id" INTEGER PRIMARY KEY,
            "name" TEXT);
              ''')
    c.execute('''
        CREATE TABLE "shows" (
            "show_id" TEXT PRIMARY KEY,
            "name" TEXT,
            "arena" TEXT,
            "show_date" TEXT,
            "promotion" INTEGER,
            "url" TEXT,
            FOREIGN KEY ("promotion") REFERENCES
                "promotions" ("promotion_id"));
              ''')
    c.execute('''
        CREATE TABLE "workers" (
            "worker_id" TEXT PRIMARY KEY,
            "name" TEXT);
              ''')
    c.execute('''
        CREATE TABLE "appearances" (
            "worker_id" TEXT,
            "show_id" TEXT,
            FOREIGN KEY ("worker_id") REFERENCES "workers" ("worker_id"),
            FOREIGN KEY ("show_id") REFERENCES "shows" ("show_id"),
            UNIQUE("worker_id", "show_id"));
              ''')
    conn.commit()


def add_promotion(promotion):
    """
    Inserts the specified promotion into the promotion table.
    """
    c.execute('''INSERT OR IGNORE INTO promotions(promotion_id, name)
                 VALUES(?,?)''', (promotion.id, promotion.name))
    conn.commit()


def add_show(show):
    """
    Inserts the specified show into the shows table.
    """
    c.execute('''INSERT OR IGNORE INTO shows(show_id, name, arena, show_date, promotion, url)
                 VALUES(?,?,?,?,?,?)''',
              (show.show_id, show.show_name, show.arena, show.date, show.promotion.id, show.url))
    conn.commit()


def add_worker(worker):
    """
    Inserts the specified worker into the workers table.
    """
    c.execute('''INSERT OR IGNORE INTO workers(worker_id, name)
                 VALUES(?,?)''', (worker.id, worker.name))
    conn.commit()


def add_appearance(worker, show):
    """
    Inserts the specified worker and show pair into the appearances table.
    """
    c.execute('''INSERT OR IGNORE INTO appearances(worker_id, show_id)
                 VALUES(?,?)''', (worker.id, show.show_id))
    conn.commit()


def validate_worker(worker_name, bs_html):
    """
    Perform checks against a plain text worker name by iterating over the MatchResults and performing tests on each
    result entry.
    :param worker_name: the plain text name under test
    :param bs_html: the HTML as passed through BeautifulSoup
    :return: True if the worker is valid, False if it should be rejected
    """
    divs = bs_html.find("div", {"class": "Matches"})
    for div in divs:
        result = div.find("div", {"class": "MatchResults"})
        if not_one_off(worker_name, result.text.strip()):
            return True

    return False


def not_one_off(worker_name, search):
    """
    Checks whether the name does not match the one off pattern: i.e. is not followed by a bracketed name
    :param worker_name: the plain text name under test
    :param search: the match result to match against
    :return: True if the regex matches, in other words does not match the one off pattern
    """
    return bool(re.search(worker_name + "(( \\(([c\\)]|[w\\/]))|( [^(])|$)", search))


def parse_workers(url):
    """
    From a URL, fetches the page, and passes it through BeautifulSoup. Then parses the show info, promotion info, and
    worker info from the page.
    All these are added to the database
    :param url: the show URL or dictionary
    """
    urls = get_urls(url)

    shows = []
    all_workers = []
    for url in urls:
        raw_html = simple_get(url)
        if raw_html is not None:
            html = BeautifulSoup(raw_html, 'html.parser')

            show = parse_show_info(html, url)
            shows.append(show)
            if args.verbose:
                print("Parsed show info {0}".format(show))

            workers = parse_worker_list(html)
            all_workers.extend(workers)

    if len(shows) > 1:
        if args.verbose:
            print("Merging {0} shows".format(len(shows)))
        show_names = []
        show_ids = []
        show_urls = []
        for show in shows:
            show_names.append(show.show_name)
            show_ids.append(show.show_id)
            show_urls.append(show.url)
        name = '/'.join(show_names) + " Taping"
        ids = "m" + ','.join(show_ids)
        url_cs = ','.join(show_urls)
        the_show = Show(ids, shows[0].arena, shows[0].date, name, shows[0].promotion, url_cs)
    else:
        the_show = shows[0]

    add_promotion(the_show.promotion)
    add_show(the_show)
    for worker in all_workers:
        add_worker(worker)
        add_appearance(worker, the_show)


def get_urls(url):
    """
    Check if the URL is a dict. If so, return an array of the sub-items. If not, return an array containing just the
    input url.
    :param url: A URL str or a dict of URLs
    :return: a list of urls
    """
    urls = []
    if isinstance(url, dict):
        if any([i in url for i in ['merge', 'taping', 'squash']]):
            urls = url.get('merge') or url.get('taping') or url.get('squash')
    else:
        urls = [url]
    return urls


def parse_worker_list(html):
    """
    Tries to extract wrestler info by parsing the 'Comments Font9' div
    (All Workers).
    The content is split on commas, and then the ID is fetched from each item
    if present.
    :param html: the HTML as passed through BeautifulSoup
    """
    all_workers = html.find("div", {"class": "Comments Font9"})
    worker_list = (u''.join(str(item) for item in all_workers)).split(",")
    ret = []
    for worker in worker_list:
        if args.verbose:
            print("Scraped worker being parsed: \'" + worker + "\'")
        worker_id = None
        worker_name = None
        worker_soup = BeautifulSoup(worker, 'html.parser')
        profile_link = worker_soup.find('a')
        if profile_link is not None:
            query_parts = parse_qs(urlparse(profile_link.attrs['href']).query)
            link_type = int(query_parts.get(TYPE_FIELD)[0])
            if ContentType(link_type) is ContentType.WRESTLER:
                worker_id = int(query_parts.get(ID_FIELD)[0])
                worker_name = profile_link.text
        else:
            plain_text_name = worker.strip()
            if validate_worker(plain_text_name, html):
                worker_id = plain_text_name
                worker_name = plain_text_name

        if worker_id is not None:
            if args.verbose:
                print("Successfully parsed, {0}/{1}".format(worker_id, worker_name))
            ret.append(Worker(worker_id, worker_name))

    return ret


def parse_show_info(html, url):
    """
    From the souped HTML, create a dictionary for the show info table, and extract the relevant portions.
    :param html: the HTML as passed through BeautifulSoup
    :param url: the show URL
    :return: a Show object
    """
    dictionary = get_show_information_dictionary(html)
    query_parts = parse_qs(urlparse(url).query)
    show_id = query_parts.get(ID_FIELD)[0]
    arena = dictionary["Arena:"].get_text()
    date_str = dictionary["Date:"].get_text()
    dd, mm, yy = date_str.split(".")
    date_obj = date(int(yy), int(mm), int(dd))
    show_name = dictionary["Name of the event:"]
    promotion_str = dictionary["Promotion:"]
    promotion = parse_promotion_info(promotion_str)
    return Show(show_id, arena, date_obj, show_name, promotion, url)


def parse_promotion_info(promotion_str):
    """
    From the contents of the 'Promotion' infobox, check for a link. If a link exists, and the content type in the URL
    indicates the link is to a Promotion page, parse the promotion information from the text.
    :param promotion_str: The contents of the 'Promotion: ' infobox.
    :return: a Promotion object
    """
    if promotion_str is not None:
        query_parts = parse_qs(urlparse(promotion_str.attrs['href']).query)
        link_type = int(query_parts.get(TYPE_FIELD)[0])
        if ContentType(link_type) is ContentType.PROMOTION:
            promotion_id = int(query_parts.get(ID_FIELD)[0])
            return Promotion(promotion_id, promotion_str.text)
    else:
        print("No promotion found, input was {0}".format(promotion_str))
        return Promotion(-1, "")


def get_show_information_dictionary(html):
    """
    Find the information box from the show page. Essentially treat it as a table:
        find every InformationBoxTitle div, and use the text as a key.
        find every InformationBoxContents div, and use the content as a value.

    :param html: the show page html, as parsed through Beautiful Soup
    :return: dictionary of the show information box
    """
    show_table = html.find("div", {"class": "InformationBoxTable"})
    keys = [span.get_text() for span in show_table.find_all("div", {"class": "InformationBoxTitle"})]
    values = [span.contents[0] for span in show_table.find_all("div", {"class": "InformationBoxContents"})]
    dictionary = dict(zip(keys, values))
    return dictionary


def main():
    with open(args.filename, 'r') as yamlfile:
        shows = yaml.safe_load(yamlfile)

    for show in shows:
        parse_workers(show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape and parse a list of shows')
    parser.add_argument("-f", "--file", dest="filename",
                        help="file to be loaded", metavar="FILE",
                        default="shows.yaml")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="output more info about what's being parsed",
                        action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
    c = conn.cursor()
    create_tables()
    main()
