"""
Written by Alexander Valarus
Adapted by Michael Hopwood
Fall 2021
"""

import requests
import re
import random
from bs4 import BeautifulSoup
from node import Node
from tqdm import tqdm
import pandas as pd

WIKI = "https://en.wikipedia.org"
nodes = {}
node_pages = []


def get_soup(page):
    url = WIKI + page
    try:
        page = requests.get(url)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')
    except:
        #print("Page cannot be accessed.")
        soup = None
    return soup


def clean_tag(tag):
    """
    Removes unwanted elements from a tag.
    :param tag: a bs4.element.Tag object containg an infobox that should be clean
    :return: cleaned_tag: a bs4.element.Tag object that has had nuisance elements removed
    """
    cleaned_tag = tag
    for sup in cleaned_tag('sup'):
        sup.decompose()

    return cleaned_tag


def find_bio_table(soup):
    bio_table = soup.find('table', {'class': 'infobox vcard'})

    # The bio table's name may differ slightly by page, so try again if it fetches None at first.
    if bio_table is None:
        bio_table = soup.find('table', {'class': 'infobox biography vcard'})

    return bio_table


def find_influence(bio):
    # Find info boxes that are contained in collapsible menus
    raw_influences = None
    raw_influenced = None

    info_boxes = bio.find_all('div',
                              {'class': "mw-collapsible mw-collapsed",
                               # 'style': "text-align: center; font-size: 95%;"
                               }
                              )
    if len(info_boxes) == 0:
        info_boxes = bio.find_all('div',
                                  {'class': "mw-collapsible mw-made-collapsed mw-collapsed",
                                   # 'style': "text-align: center; font-size: 95%;"
                                   }
                                  )

    if len(info_boxes) == 0:
        info_boxes = bio.find_all('div',
                                  {'class': "mw-collapsible mw-made-collapsed mw-collapsed",
                                   # 'style': "text-align: center; font-size: 95%;"
                                   }
                                  )

    if len(info_boxes) == 0:
        info_boxes = bio.find_all('tr')

    for box in info_boxes:
        info_box_text = box.get_text().lower()
        if 'influences' in re.findall(r'%s\w*'% 'influences', info_box_text):
            raw_influences = box
        elif re.compile('influenced.+by').findall(info_box_text):
            raw_influences = box
        elif 'influenced' in re.findall(r'%s\w*'% 'influenced', info_box_text):
            raw_influenced = box
        else:
            continue
    return raw_influences, raw_influenced


def scrape_list():
    """
    Establishes a connection with wikipedia's pages listing philosophers
    then scrapes every url of every catalogued philosopher. Note that
    all of these links are the canonical urls, so no check is needed.
    """
    list_of_philosophers = []
    wiki_philosopher_lists = ['/wiki/List_of_philosophers_(A???C)',
                              '/wiki/List_of_philosophers_(D???H)',
                              '/wiki/List_of_philosophers_(I???Q)',
                              '/wiki/List_of_philosophers_(R???Z)']

    for group in wiki_philosopher_lists:
        # Connect to wikipedia and get the html of the page
        url = WIKI + group
        page = requests.get(url)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')

        # Use bs4 to scrape some philosophers
        div = soup.find('div', {'class': 'mw-parser-output'})

        # Destroy useless tags
        for trash in div('table'):
            trash.decompose()
        for trash in div('sup'):
            trash.decompose()
        for trash in div('ol'):
            trash.decompose()
        for trash in div('h2'):
            trash.decompose()
        for trash in div('dl'):
            trash.decompose()
        for trash in div('p'):
            trash.decompose()

        philosophers = div.find_all('li')

        # Finally, put all of the urls (and birth eras) in a list
        philosopher_pages = [(i.contents[0].get('title'), i.contents[0].get('href'), i.contents[-1]) for i in philosophers]
        list_of_philosophers += philosopher_pages

    return list_of_philosophers


def set_pages(page_list):
    node_pages = [wiki_page for _, wiki_page in page_list]


def scrape_philosopher(name, page, birthyear='unknown'):
    """
    Establishes a connection with a philosopher's wikipedia page and scrapes all influences/influenced
    :param name:
    :param page:
    :param birthyear: a string that gives approximate life era
    :return: None
    """

    #print(f"\n\nResearching {name}...", end='')
    # Connect to wikipedia and get the html of the page
    soup = get_soup(page)
    if soup is None:
        #print(f" {name} has no Wiki page.")
        new_philosopher = Node(name, page, birthyear)
        return new_philosopher

    # Initialize blank variables for influences/influenced tags
    raw_influences = None
    raw_influenced = None
    influences = []
    influenced = []

    # Extract the biography card from the individual's page
    bio_table = find_bio_table(soup)

    if bio_table is None:
        #print(f" {name} has no bio section.", end='')
        new_philosopher = Node(name, page, birthyear)
        return new_philosopher
    #else:
        #print(f" bio found...", end='')

    # Next, find all influences/influenced by checking several different types of info boxes.
    raw_influences, raw_influenced = find_influence(bio_table)

    # Strip away everything except the wanted data
    if raw_influences:
        raw_influences = clean_tag(raw_influences)
        raw_influences = raw_influences.find_all('a')
    #else:
        #print(f" {name} has no influences data.", end='')
    if raw_influenced:
        raw_influenced = clean_tag(raw_influenced)
        raw_influenced = raw_influenced.find_all('a')
    #else:
        #print(f" {name} has no influenced data.", end='')

    # Store the philosopher names and page extensions in a list of tuples
    if raw_influences:
        influences = [(i.get_text(), i.get('href')) for i in raw_influences]
    if raw_influenced:
        influenced = [(i.get_text(), i.get('href')) for i in raw_influenced]

    # Construct a Node for this philosopher as add influence/influenced links
    new_philosopher = Node(name, page, birthyear)
    for i in influences:
        new_philosopher.add_influence(*i)
    for i in influenced:
        new_philosopher.add_influenced(*i)

    return new_philosopher


def get_canonical_url(page):
    """
    This function goes to a wikipedia page and returns the page's canonical url.
    The reason that this is important is that multiple urls may link to the same page, but
    there is always only one canonical url for that page. When adding a node from a crawled link,
    checking the page's canonical url guarantees that we are not adding duplicates.
    Example: wiki/Husserl (non-canonical) links to wiki/Edmund_Husserl (canonical). If we don't
    check the canonical name, this would result in him incorrectly having two different nodes.
    :param page:
    :return: canonical_url
    """
    soup = get_soup(page)
    if soup is None:
        return None
    canonical_url = soup.find('link', {'rel': 'canonical'})
    canonical_url = canonical_url.get('href').split('org')[1]
    return canonical_url


def validate_links(key):
    """
    This function checks every link in one node and ensures the link is recognized by the paired node.
    :param key:
    :return: None
    """
    initial_node = nodes[key]
    initial_name = initial_node.get_name()
    initial_page = initial_node.get_page()
    node_incoming_links = initial_node.get_incoming()
    node_outgoing_links = initial_node.get_outgoing()
    keys = list(nodes.keys())

    for incoming_name, incoming_page in node_incoming_links:
        canonical_url = get_canonical_url(incoming_page)
        if canonical_url not in node_pages and canonical_url is not None:
            nodes[incoming_name] = Node(incoming_name, canonical_url)
            node_pages.append(canonical_url)
            target = nodes[incoming_name]
            target_outgoing = target.get_outgoing()
            if initial_name not in (n for (n, _) in target_outgoing):
                target.add_influenced(initial_name, initial_page)

    for outgoing_name, outgoing_page in node_outgoing_links:
        canonical_url = get_canonical_url(outgoing_page)
        if canonical_url not in node_pages:
            nodes[outgoing_name] = Node(outgoing_name, canonical_url)
            node_pages.append(canonical_url)
            target = nodes[outgoing_name]
            target_incoming = target.get_incoming()
            if initial_name not in (n for (n, _) in target_incoming):
                target.add_influence(initial_name, initial_page)


def validate_node(key):
    # TODO: Double check to make sure this is working as expected
    if not nodes[key].outgoing_links and not nodes[key].incoming_links:
        del nodes[key]
    else:
        nodes[key].deduplicate_links()


def export_data():

    names, births, incoming_links, outgoing_links, pages = [], [], [], [], []
    for k, node in nodes.items():
        name, birth, i_links, o_links = node.fetch_data()
        names.append(name)
        births.append(birth)
        incoming_links.append(i_links)
        outgoing_links.append(o_links)
        pages.append(node.page)

    data = pd.DataFrame()
    data['name'] = names
    data['birth'] = births
    data['incoming_links'] = incoming_links
    data['outgoing_links'] = outgoing_links
    data['page'] = pages
    data.to_csv('philosopher_data.csv', encoding='UTF-8')

def main():
    global nodes
    global node_pages
    print("Discovering Philosophy Network...\n")

    # Scrape the list of wiki pages first
    philosopher_list = scrape_list()
    node_pages = [wiki_page for _, wiki_page, _ in philosopher_list]

    # Create a dictionary of nodes using the scrap philosopher function
    # The key to each node is the person's name
    print("Scraping philosophers...")
    for philosopher in tqdm(philosopher_list):
        nodes[philosopher[0]] = scrape_philosopher(*philosopher)

    # Check to see how many nodes there are in the initial list
    keys = list(nodes.keys())
    print(f"\nThere are {len(keys)} recorded nodes before link validation.")

    # Validate every link and every node
    print("Validating links...")
    for key in tqdm(keys):
        validate_links(key)
    print("Validating nodes...")
    keys = list(nodes.keys())
    print(f"\nThere are {len(keys)} recorded nodes before node validation.")
    for key in tqdm(keys):
        validate_node(key)

    keys = list(nodes.keys())
    print(f"There are {len(keys)} final recorded nodes after all validation.")
    for key in list(nodes.keys()):
        nodes[key].brief_summary()
        print(f"{nodes[key].name}: {nodes[key].page}.")
    export_data()


if __name__ == "__main__":
    main()
