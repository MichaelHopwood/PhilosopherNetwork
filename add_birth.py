import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import traceback
import datefinder
import numpy as np
import copy
import datetime

# Example: http://www.geonames.org/search.html?q=paris+france&country=
base_url = "http://www.geonames.org/search.html?q="
appendage = "&country="

#location = 'paris+france'
location = 'babylon'


def find_date(string):
    orig_string = copy.copy(string)
    string = re.sub('c\.', '', string)
    string = re.sub('circa', '', string)

    num_AD = len(re.findall('AD', string))
    num_BC = len(re.findall('BC', string))

    string = re.sub('AD', '', string)
    string = re.sub('BC', '', string)

    string = re.sub('\s', '', string)

    birth_date = "FILL"
    if re.search(r"(\d+)–(\d+)", string):
        # Finds dates like "1844-1846"
        year_data = re.findall(r"(\d+)–(\d+)", string)
        y_data = year_data[0]
        birth_date = int(y_data[0])

    elif re.search(r"\d\d\d\d", string):
        # Finds dates like "born 1944"
        year_data = re.findall(r"\d\d\d\d", string)
        y_data = int(year_data[0])
        birth_date = y_data

    elif re.search(r"\d\d\d", string):
        # Finds dates like "born 194"
        year_data = re.findall(r"\d\d\d", string)
        y_data = int(year_data[0])
        birth_date = y_data

    elif re.search(r"\d+(th|rd|st)", string):
        # Get century
        year_data = re.findall(r"\d+", string)
        birth_date = int(year_data[0])*100 - 50

    if num_AD == 1 and num_BC == 1:
        # Person born in BC and died in AD
        birth_date *= -1
    elif num_BC > 0:
        # Person born and died in BC
        birth_date *= -1

    if birth_date == "FILL":
        print("No date found..")
        print(orig_string)
        print(string)

    return birth_date

def convert(tude):
    """Convert lat/long strings of form:
    Example: 
    N 52° 13' 47''
    E 21° 0' 42''
    convert() =>
    52.22972222222222 21.011666666666667
    """
    multipler = 1 if tude[0] in ['N', 'E'] else -1
    info = re.split('[°\'"]', tude[1:])
    deg, minutes, seconds = float(info[0]), float(info[1]), float(info[2])
    return (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * multipler


def extract(string):
    print("STRING", string)
    # Find structures like:   N 13° 38' 11''
    # \w\s\d+°\s\d+'\s\d+''
    try:
        attempt1 = re.findall("\w\s\d+°\s\d+'\s\d+''", string)
        if len(attempt1):
            return convert(attempt1[0])
    except:
        return 'FILL'

    # Find structures like:    Lat/Lng : 43.5675 / 4.1933'
    # Lat/Lng\s:\s\d*.\d*\d\s*/\s*\d*.\d*
    try:
        attempt2 = re.findall("Lat/Lng\s:\s-?\d*\.\d*\s*\/\s*-?\d*\.\d*", string)
        print(attempt2)
        if len(attempt2):
            a = re.findall("-?\d+\.\d*", attempt2[0])
            print(a)
            return a[0], a[1]
    except:
        return 'FILL', 'FILL'

def get_latlong_location(location):
    url = base_url + location + appendage
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')

    # Use bs4 to scrape some philosophers
    #div = soup.find_all('tr')#, {'class': 'geo'})
    #data = div[3].find_all('td')[-2:]

    data = soup.find_all(['tr', 'td'])

    # Attempt 1
    lat, long = 'FILL', 'FILL'
    for d in data:
        dproc = " ".join(d.text.split())
        if "Lat/Lng" in dproc:
            lat, long = extract(dproc)
            if lat != 'FILL' and long != 'FILL':
                break

    # Attempt 2

    if lat == 'FILL':
        lat = " ".join(data[0].text.split())
        lat = extract(lat)
    if long == 'FILL':
        long = " ".join(data[1].text.split())
        long = extract(long)
    return lat, long


def get_wiki_birth(philosopher_extension):
    wiki_url = "https://en.wikipedia.org"
    url = wiki_url + philosopher_extension
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')

    div = soup.find_all(['th','td'], {'class': ['infobox-label', 'infobox-data']})

    for i, d in enumerate(div):
        if 'born' in d.text.lower():               
            birth = "FILL"               
            lat = "FILL"
            long = "FILL"
            for data in div[i+1]:
                data = data.text
                # Check if date in snippet

                if birth == "FILL":
                    try:
                        birth = list(datefinder.find_dates(data))[0]
                    except Exception as e:
                        print('not work', e)
                        print(data)
                        try:
                            birth = find_date(data)
                        except Exception as e:
                            print("fail 2", e)
                            traceback.print_exc()

                if lat == "FILL" or long == "FILL":
                    lat, long = get_latlong_location(data)
    print("BIRTH:", birth)
    print("LOC:", lat, long)
    print()

    return birth, lat, long

#data = pd.read_csv('data//alexander.csv')
#data = pd.read_csv('data//randyll.csv')
data = pd.read_csv('data//michael.csv')

successes = 0
births = []
lats, longs = [], []
for ind,row in data.iterrows():

    birthdate, lat, long = "FILL", "FILL", "FILL"

    print(row['page'])
    try:
        birthdate, lat, long = get_wiki_birth(row['page'])
        successes += 1

    except Exception as e:
        print(e)
        traceback.print_exc()

    births.append(birthdate)
    lats.append(lat)
    longs.append(long)

    #break
    if birthdate == 'FILL' or lat == 'FILL' or long == 'FILL':
        break

print(f"{successes} successes out of {len(data)}")

data['births'] = births
data['latitude'] = lats
data['longitude'] = longs

data.to_csv('data//michael_algoaddition_adddate.csv')

