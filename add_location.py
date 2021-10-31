import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import traceback

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

def convert(tude):
    """Convert lat/long strings of form:
    Example: 
       N 52° 13' 47''
       E 21° 0' 42''
       convert() =>
       52.22972222222222 21.011666666666667
    """
    multipler = 1 if tude[0] in ['N', 'E'] else -1
    print("MULTIPLIER", multipler, tude)
    info = re.split('[°\'"]', tude[1:])
    deg, minutes, seconds = float(info[0]), float(info[1]), float(info[2])
    return (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * multipler

def extract_numeric(s):
    splits = re.split(' ', s)
    lat_mult = 1 if splits[0][-1] in ['N', 'E'] else -1
    lat = float(re.split('°', splits[0])[0]) * lat_mult
    lon_mult = 1 if splits[1][-1] in ['N', 'E'] else -1
    lon = float(re.split('°', splits[1])[0]) * lon_mult
    try:
        return lat, lon
    except:
        print(s)
        print(splits)
        print(lat, lon)
        print(re.split('°', splits[0])[0])
        print(re.split('°', splits[1])[0])
        return float(lat), float(lon)

#data = pd.read_csv('data//alexander.csv')
#data = pd.read_csv('data//randyll.csv')
data = pd.read_csv('data//michael.csv')

successes = 0
accurate = 0
manually_filled = 0
lats, lons = [], []
for ind,row in data.iterrows():
    print(row['page'])
    try:
        latlong = get_wiki_location(row['page'])
        lat,lon = extract_numeric(latlong)
        successes += 1

        print("extracted: ", lat, lon)

        # compare to manually annotated
        if row['latitude'] != 'FILL':
            manually_filled += 1

            manual_lat, manual_lon = convert(row['latitude']), convert(row['longitude'])
            print("annotated: ", row['latitude'], row['longitude'])
            print("annot conv:", manual_lat, manual_lon) 

            pct_diff_lat = (lat - manual_lat) / (lat + manual_lat)/2
            pct_diff_lon = (lon - manual_lon) / (lon + manual_lon)/2
            print(pct_diff_lat, pct_diff_lon)
            if (pct_diff_lon < 1) & (pct_diff_lat < 1):
                accurate += 1
            
        lats.append(lat)
        lons.append(lon)

    except Exception as e:
        print(e)
        traceback.print_exc()
        lats.append('FILL')
        lons.append('FILL')
    print()

print(f"{successes} successes out of {len(data)}")
print(f"Accurate: {accurate} out of {manually_filled} manually filled.")

data['latitude'] = lats
data['longitude'] = lons

data.to_csv('data//michael_algoaddition.csv')
