import requests
from bs4 import BeautifulSoup
import pandas as pd

# Example: http://www.geonames.org/search.html?q=paris+france&country=
base_url = "http://www.geonames.org/search.html?q="
appendage = "&country="

#location = 'paris+france'
location = 'babylon'

def get_latlong_location(location):
    url = base_url + location + appendage
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')

    # Use bs4 to scrape some philosophers
    div = soup.find_all('tr')#, {'class': 'geo'})
    data = div[3].find_all('td')[-2:]
    lat = " ".join(data[0].text.split())
    long = " ".join(data[1].text.split())
    print(location, ':', lat, long)

def get_wiki_location(philosopher_extension):
    wiki_url = "https://en.wikipedia.org"
    url = wiki_url + philosopher_extension
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')

    div = soup.find_all('div', {'class': 'birthplace'})
    div2 = div[0].find_all('a')
    extention = div2[0].get('href')
    location_url = wiki_url + extention

    page = requests.get(location_url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')
    div = soup.find_all('span', {'class': 'geo-dec'})

    latlong = div[0].text
    return latlong

data = pd.read_csv('michael.csv')
successes = 0
for ind,row in data.iterrows():
    print(row['page'])
    try:
        latlong = get_wiki_location(row['page'])
        print(latlong)
        successes += 1
    except:
        pass

print(f"{successes} successes out of {len(data)}")