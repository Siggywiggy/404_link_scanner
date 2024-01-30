#! python3
# a program to check if all the links on a website are functional
# checking all the links on the same website regardless of depth
# external links are checked by depth of 1

import re
import bs4
import requests
import logging
import pprint
from helper_functions import tuple_checker as t_check
import time

logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s -  %(levelname) s -  %(message)s"
)

# comment out next line to enable logging

logging.disable(logging.CRITICAL)

logging.debug("Start of program...")

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
}

starting_url = "https://www.kliimaseade.ee"

# regex to capture all wbsite urls not preceded by "@"
url_regex = re.compile(r"(?<![@])(.*kliimaseade.ee).*")
# regex to capture all shortened links that dont match first group but match second group
url_regex_shortened = re.compile(f"^(?!.*\\b(?:.com|.ee|.eu|.org|mailto)\\b)(.*/.*/.*)")


def link_crawler(url):
    links_list = list()
    # tuples of parent/child url links to keep track of also parent link
    links_list.append((url, url))
    external_links = list()
    visited_links = list()
    broken_links = list()

    while links_list:
        logging.debug(f"lenght of list is {len(links_list)}")
        for link in links_list:
            # tuple unpack working link and its parent link from tuple
            parent_link, working_link = link
            # remove the current link from the list of links
            links_list = [value for value in links_list if value[1] != link[1]]
            # keeping track of visited links
            visited_links.append(working_link)
            # logging.debug(f"visited links are {visited_links}")
            # check if the download went OK
            try:
                request_object = requests.get(working_link, headers)
                request_object.raise_for_status()
            except (
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema,
            ) as schemaerr:
                print(f"Something went wrong with the url schema: {schemaerr}")
                #broken_links.append((parent_link, working_link))
                print(parent_link, working_link)
            except requests.exceptions.HTTPError as err:
                print(f"Something went wrong with downloading a page: {err}")
                print(err.response.status_code)
                print(parent_link, working_link)
                broken_links.append((parent_link, working_link))
                continue
            except requests.exceptions.ConnectionError as conn_err:
                print(f"something went wrong with connecting: {conn_err}")
                print(parent_link, working_link)
                broken_links.append((parent_link, working_link))
                continue

            # create soup object and parse it with 'lxml'
            soup_object = bs4.BeautifulSoup(request_object.content, "lxml")
            # getting all "a href" links
            all_href_links = soup_object.find_all("a", href=True)

            for i in all_href_links:  # loop over all freshly found links
                new_link = i["href"]
                if new_link in visited_links:  # if already visited, continue loop
                    logging.debug(f"{new_link} already visited, skipping")
                    continue

                match_object_long = url_regex.search(
                    new_link
                )  # search for full link regex match
                match_object_shortened = url_regex_shortened.search(
                    new_link
                )  # match partial link regex match

                if match_object_long:
                    # if long link regex results in match object
                    logging.debug(
                        f"regex match found! {match_object_long.group(1)} {new_link}"
                    )
                    # check if link is in either visited_links or links list
                    if new_link in visited_links:
                        continue
                    elif t_check(links_list, new_link):
                        logging.debug(f"{new_link} is in links_list, skipping")
                        continue
                    else:
                        links_list.append((working_link, new_link))

                # check if the link matches short link regex
                elif match_object_shortened:
                    logging.debug(
                        f"shortened url regex match found! {match_object_shortened.group()}"
                    )

                    # turn in to functional url
                    elongated_url = url + str(match_object_shortened.group())
                    # check if link is in either visited_links or links_list
                    logging.debug(f"elongated url is {elongated_url}")
                    # print(elongated_url)
                    # time.sleep(5)
                    if elongated_url in visited_links:
                        continue
                    elif t_check(links_list, new_link):
                        logging.debug(f"{elongated_url} is in links_list, skipping")
                        continue
                    else:
                        links_list.append((working_link, elongated_url))
                # if no regex match found
                elif (match_object_long is None) and (match_object_shortened is None):
                    logging.debug(f"external link found! {new_link}")
                    logging.debug(f"checking if {new_link} in visited_links:")
                    logging.debug(f"visited links are {visited_links}")
                    if new_link in visited_links:
                        continue
                    elif t_check(links_list, new_link):
                        logging.debug(f"{new_link} is in visited_links or links_list")
                        continue
                    else:
                        logging.debug(f"adding {new_link} to {external_links}")
                        external_links.append((working_link, new_link))

    for external_link in external_links:
        # check if the link has already been listed in broken links or visited links:
        logging.debug(f"external link is {str(list(external_link))}")

        if external_link[1] in visited_links:
            continue

        try:
            request_object = requests.get(external_link[1], headers)
            request_object.raise_for_status()
        except (
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
        ) as schemaerr:
            print(f"Something went wrong with downloading: {schemaerr}")
            visited_links.append(external_link)

        except requests.exceptions.HTTPError as err:
            print(f"Something went wrong with downloading: {err}")
            broken_links.append(external_link)
        except requests.exceptions.ConnectionError as urlerr:
            print(f"something went wrong with downloading: {urlerr}")
            visited_links.append(external_link)

    return broken_links


website_broken_links = link_crawler(starting_url)
pprint.pprint(website_broken_links)