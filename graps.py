"""
Fetch cards from Cagematch and extract the wrestlers who were on that show
"""
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from url_loading import simple_get
import yaml
from enum import Enum


class ContentType(Enum):
    WRESTLER = 2
    PROMOTION = 8

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
        print(showTable.prettify())
        keys = [span.get_text() for span in showTable.find_all("div", {"class": "InformationBoxTitle"})]
        values = [span.contents[0] for span in showTable.find_all("div", {"class": "InformationBoxContents"})]
        dictionary = dict(zip(keys, values))

        bits = urlparse(url)
        parsedBits = parse_qs(bits.query)
        showId = parsedBits.get('nr')[0]
        arena = dictionary["Arena:"].get_text()
        date = dictionary["Date:"].get_text()
        showName = dictionary["Name of the event:"]
        promotion = dictionary["Promotion:"]
        if promotion is not None:
            bits = urlparse(promotion.attrs['href'])
            parsedBits = parse_qs(bits.query)
            linkType = int(parsedBits.get('id')[0])
            if ContentType(linkType) is ContentType.PROMOTION:
                promotionId = int(parsedBits.get('nr')[0])
                print("#" + str(promotionId) + ", " + promotion.text)
        else:
            print("#" + str(-1) + ", " + promotion)

        all_workers = html.find("div", {"class": "Comments Font9"})
        # print(u''.join(str(item) for item in all_workers))
        # worker_list = ("".join(all_workers.contents)).split(",")
        worker_list = (u''.join(str(item) for item in all_workers)).split(",")
        for worker in worker_list:
            worker_soup = BeautifulSoup(worker, 'html.parser')
            profile_link = worker_soup.find('a')
            if profile_link is not None:
                bits = urlparse(profile_link.attrs['href'])
                parsedBits = parse_qs(bits.query)
                linkType = int(parsedBits.get('id')[0])
                if linkType == 2:
                    workerId = int(parsedBits.get('nr')[0])
                    print("#" + str(workerId) + ", " + profile_link.text)
            else:
                print("#" + str(-1) + ", " + worker)
            print("--------------------")


def main():
    with open("shows.yaml", 'r') as yamlfile:
        shows = yaml.safe_load(yamlfile)

    for show in shows:
        parse_workers(show)


main()
