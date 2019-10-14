"""
Fetch cards from Cagematch and extract the wrestlers who were on that show
"""
from dataclasses import dataclass

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from url_loading import simple_get
import yaml
from enum import IntEnum
import sqlite3
from datetime import date
import argparse
import re
import cProfile


TYPE_FIELD = 'id'
ID_FIELD = 'nr'


class ContentType(IntEnum):
    WRESTLER = 2
    PROMOTION = 8
    TAG_TEAM = 28
    STABLE = 29

    
class ShowType(IntEnum):
    NORMAL = 0
    PARTIAL = 1
    PARTIAL_EXCLUDED = 2


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
    is_partial: ShowType = ShowType.NORMAL


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
            "is_partial" INTEGER,
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
    c.execute('''INSERT OR IGNORE INTO shows(show_id, name, arena, show_date, promotion, url, is_partial)
                 VALUES(?,?,?,?,?,?,?)''',
              (show.show_id, show.show_name, show.arena, show.date, show.promotion.id, show.url, show.is_partial))
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
    result = False
    divs = bs_html.find("div", {"class": "Matches"})
    for div in divs:
        result = div.find("div", {"class": "MatchResults"})
        if not_one_off(worker_name, result.text.strip()):
            result = True
    return result


def filter_excluded(workers, exclude, bs_html):
    """
    Exclude wrestlers who only appear in matches that have been marked for exclusion from the parsed
    list of workers.
    :param workers: the list of worker objects parsed from the All Workers section
    :param exclude: the indexes of matches to exclude
    :param bs_html: the HTML as passed through BeautifulSoup
    :return: the workers list with wrestlers only in excluded matches removed
    """
    exclude_matches = []
    include_matches = []
    divs = bs_html.find("div", {"class": "Matches"})
    i = 1
    for div in divs:
        result = div.find("div", {"class": "MatchResults"})
        if i in exclude:
            exclude_matches.append(result)
        else:
            include_matches.append(result)
        i = i + 1

    if args.verbose:
        print("Excluding matches: {0}, Including matches: {1}".format(exclude_matches, include_matches))

    newlist = []
    for worker in workers:
        if isinstance(worker.id, int):
            found_exclude = False
            for result in exclude_matches:
                for profile_link in result.find_all('a'):
                    if profile_link is not None:
                        worker_id, worker_name = extract_worker_id_name(profile_link)
                        if worker_id == worker.id:
                            found_exclude = True
            if found_exclude:
                found_include = False
                for result in include_matches:
                    for profile_link in result.find_all('a'):
                        if profile_link is not None:
                            worker_id, worker_name = extract_worker_id_name(profile_link)
                            if worker_id == worker.id:
                                found_include = True
            if found_exclude and not found_include:
                if args.verbose:
                    print("Excluding wrestler {0}".format(worker))
            else:
                newlist.append(worker)
        elif any(worker.name in s for s in exclude_matches) and not any(worker.name in s for s in include_matches):
            if args.verbose:
                print("Excluding wrestler {0}".format(worker))
        else:
            newlist.append(worker)
        
    return newlist


def not_one_off(worker_name, search):
    """
    Checks whether the name does not match the one off pattern: i.e. is not followed by a bracketed name
    :param worker_name: the plain text name under test
    :param search: the match result to match against
    :return: True if the regex matches, in other words does not match the one off pattern
    """
    return bool(re.search(worker_name + "(( \\(([c\\)]|[w\\/]))|( [^(])|$|\\))", search))


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
        url, is_partial = check_is_partial(url)
        if is_partial:
            exclude = url['exclude']
            exclude_from_count = url.get('exclude_from_count') or False
            if exclude_from_count:
                show_type = ShowType.PARTIAL_EXCLUDED
            else:
                show_type = ShowType.PARTIAL
            url = url['url']
        else:
            show_type = ShowType.NORMAL
        raw_html = simple_get(url)
        if raw_html is not None:
            html = BeautifulSoup(raw_html, 'html.parser')

            show = parse_show_info(html, url, show_type)
            shows.append(show)
            if args.verbose:
                print("Parsed show info {0}".format(show))

            workers = parse_worker_list(html)
            if show_type > 0:
                workers = filter_excluded(workers, exclude, html)
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
    Check if the URL is a dict. If so, and the dict is named one of 'merge', 'taping' or 'squash', return
    an array of the sub-items. If not, return an array containing just the input url.
    :param url: A URL str or a dict of URLs
    :return: a list of urls
    """
    urls = [url]
    if isinstance(url, dict):
        if any([i in url for i in ['merge', 'taping', 'squash']]):
            urls = url.get('merge') or url.get('taping') or url.get('squash')
    return urls


def check_is_partial(url):
    """
    Check if the URL is a dict. If so, and the dict is named 'partial', return the sub-items, and True to indicate
    this. If not, return the input url and False.
    :param url: A URL str or a dict of URLs
    :return: the dict structure for a partial show entry, or the url, and True or False respectively
    """
    if isinstance(url, dict):
        if any([i in url for i in ['partial']]):
            partial_dict = url.get('partial')
            return partial_dict, True
    else:
        return url, False


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
            worker_id, worker_name = extract_worker_id_name(profile_link)
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


def extract_worker_id_name(profile_link):
    """
    From a discovered 'a' tag, check type field to verify ContentType.WRESTLER, then extract ID and Name
    :param profile_link: a discovered BeautifulSoup 'a' tag
    :return: int worker ID and text name (worker_id, worker_name)
    """
    worker_id = None
    worker_name = None
    query_parts = parse_qs(urlparse(profile_link.attrs['href']).query)
    link_type = int(query_parts.get(TYPE_FIELD)[0])
    if link_type == ContentType.WRESTLER:
        worker_id = int(query_parts.get(ID_FIELD)[0])
        worker_name = profile_link.text
    return worker_id, worker_name


def parse_show_info(html, url, show_type):
    """
    From the souped HTML, create a dictionary for the show info table, and extract the relevant portions.
    :param html: the HTML as passed through BeautifulSoup
    :param url: the show URL
    :param show_type: whether the show is a partial show
    :return: a Show object
    """
    dictionary = get_show_information_dictionary(html)
    query_parts = parse_qs(urlparse(url).query)
    show_id = query_parts.get(ID_FIELD)[0]
    arena = dictionary["Arena:"].get_text()
    date_str = dictionary["Date:"].get_text()
    dd, mm, yy = date_str.split(".")
    date_obj = date(int(yy), int(mm), int(dd))
    show_name = apply_translations(dictionary["Name of the event:"], args.dntranslate)
    promotion_str = dictionary["Promotion:"]
    promotion = parse_promotion_info(promotion_str)
    return Show(show_id, arena, date_obj, show_name, promotion, url, show_type)


def apply_translations(show_name, dntranslate=False):
    """
    Apply the following translations to strings:
      - 'Tag {x}' to 'Day {x}'
    :param show_name: the input string to translate
    :param dntranslate: whether translation should be skipped (retrieve from args)
    :return: the translated string
    """
    if dntranslate:
        return show_name
    else:
        return re.sub(r"(Tag)( [0-9]+)", r"Day\2", show_name)


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
        if link_type == ContentType.PROMOTION:
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
    parser.add_argument("-t", "--no-translations", dest="dntranslate",
                        help="don't perform translations, e.g Tag -> Day in show names",
                        action="store_true")
    parser.add_argument("-p", "--profile", dest="profiler",
                        help="run profiling",
                        action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
    c = conn.cursor()
    if args.profiler:
        pr = cProfile.Profile()
        pr.enable()
    create_tables()
    main()
    if args.profiler:
        pr.disable()
        pr.print_stats()
