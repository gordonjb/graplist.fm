"""
Fetch cards from Cagematch and extract the wrestlers who were on that show
"""
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from url_loading import simple_get
import yaml
from enum import Enum
import sqlite3
from datetime import date


class ContentType(Enum):
    WRESTLER = 2
    PROMOTION = 8


def create_tables():
    c.execute('''
        CREATE TABLE "promotions" (
            "promotion_id" INT PRIMARY KEY,
            "name" VARCHAR);
              ''')
    c.execute('''
        CREATE TABLE "shows" (
            "show_id" INT PRIMARY KEY,
            "name" VARCHAR,
            "arena" VARCHAR,
            "show_date" DATE,
            "promotion" INT,
            "url" VARCHAR,
            FOREIGN KEY ("promotion") REFERENCES
                "promotions" ("promotion_id"));
              ''')
    c.execute('''
        CREATE TABLE "workers" (
            "worker_id" VARCHAR PRIMARY KEY,
            "name" VARCHAR);
              ''')
    c.execute('''
        CREATE TABLE "appearances" (
            "worker_id" VARCHAR,
            "show_id" INT,
            FOREIGN KEY ("worker_id") REFERENCES "workers" ("worker_id"),
            FOREIGN KEY ("show_id") REFERENCES "shows" ("show_id"));
              ''')
    conn.commit()


def add_promotion(promotion_id, promotion_text):
    """
    Inserts the specified promotion into the promotion table.
    """
    c.execute('''INSERT OR IGNORE INTO promotions(promotion_id, name)
                 VALUES(?,?)''', (promotion_id, promotion_text))
    conn.commit()


def add_show(show_id, show_name, arena, date, promotion_id, url):
    """
    Inserts the specified show into the shows table.
    """
    c.execute('''INSERT OR IGNORE INTO shows(show_id, name, arena, show_date, promotion, url)
                 VALUES(?,?,?,?,?,?)''',
              (show_id, show_name, arena, date, promotion_id, url))
    conn.commit()


def add_worker(worker_id, worker_name):
    """
    Inserts the specified worker into the workers table.
    """
    c.execute('''INSERT OR IGNORE INTO workers(worker_id, name)
                 VALUES(?,?)''', (worker_id, worker_name))
    conn.commit()


def add_appearance(worker_id, show_id):
    """
    Inserts the specified worker and show pair into the appearances table.
    """
    c.execute('''INSERT INTO appearances(worker_id, show_id)
                 VALUES(?,?)''', (worker_id, show_id))
    conn.commit()


def parse_results(url):
    """
    Tries to extract wrestler info by parsing the MatchResults div for linked
    profiles.

    Abandoned, FOR NOW
    """
    raw_html = simple_get(url)
    if raw_html is not None:
        html = BeautifulSoup(raw_html, 'html.parser')
        divs = html.find("div", {"class": "Matches"})
        print(divs.prettify())
        for div in divs:
            result = div.find("div", {"class": "MatchResults"})
            for worker in result.find_all('a'):
                bits = urlparse(worker.attrs['href'])
                parsedBits = parse_qs(bits.query)
                linkType = int(parsedBits.get('id')[0])
                if ContentType(linkType) is ContentType.WRESTLER:
                    workerId = int(parsedBits.get('nr')[0])
                    print("#" + str(workerId) + ", " + worker.text)
            print("--------------------")


def parse_workers(url):
    """
    Tries to extract wrestler info by parsing the 'Comments Font9' div
    (All Workers).
    The content is split on commas, and then the ID is fetched from each item
    if present.
    """
    raw_html = simple_get(url)
    if raw_html is not None:
        html = BeautifulSoup(raw_html, 'html.parser')
        showTable = html.find("div", {"class": "InformationBoxTable"})
        keys = [span.get_text() for span in showTable.find_all("div", {"class": "InformationBoxTitle"})]
        values = [span.contents[0] for span in showTable.find_all("div", {"class": "InformationBoxContents"})]
        dictionary = dict(zip(keys, values))

        bits = urlparse(url)
        parsed_bits = parse_qs(bits.query)
        show_id = parsed_bits.get('nr')[0]
        arena = dictionary["Arena:"].get_text()
        date_str = dictionary["Date:"].get_text()
        dd, mm, yy = date_str.split(".")
        date_obj = date(int(yy), int(mm), int(dd))
        show_name = dictionary["Name of the event:"]
        promotion = dictionary["Promotion:"]
        if promotion is not None:
            bits = urlparse(promotion.attrs['href'])
            parsed_bits = parse_qs(bits.query)
            link_type = int(parsed_bits.get('id')[0])
            if ContentType(link_type) is ContentType.PROMOTION:
                promotion_id = int(parsed_bits.get('nr')[0])
                add_promotion(promotion_id, promotion.text)
        else:
            print("#" + str(-1) + ", " + promotion)

        add_show(show_id, show_name, arena, date_obj, promotion_id, url)

        all_workers = html.find("div", {"class": "Comments Font9"})
        worker_list = (u''.join(str(item) for item in all_workers)).split(",")
        for worker in worker_list:
            print("\'" + worker + "\'")
            worker_id = None
            worker_name = None
            worker_soup = BeautifulSoup(worker, 'html.parser')
            profile_link = worker_soup.find('a')
            if profile_link is not None:
                bits = urlparse(profile_link.attrs['href'])
                parsed_bits = parse_qs(bits.query)
                link_type = int(parsed_bits.get('id')[0])
                if link_type == 2:
                    worker_id = int(parsed_bits.get('nr')[0])
                    worker_name = profile_link.text
            else:
                worker_id = worker.strip()
                worker_name = worker.strip()

            if worker_id is not None:
                add_worker(worker_id, worker_name)
                add_appearance(worker_id, show_id)


def main():
    with open("shows.yaml", 'r') as yamlfile:
        shows = yaml.safe_load(yamlfile)

    for show in shows:
        parse_workers(show)


conn = sqlite3.connect('thedatabase.sqlite3', check_same_thread=False)
c = conn.cursor()
create_tables()
main()
