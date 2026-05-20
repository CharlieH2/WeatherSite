import requests
import csv
import os
from dotenv import load_dotenv

load_dotenv()

LOCATION_API_KEY = os.getenv('LOCATION_API_KEY')

query = "Stilton"

url = ('https://geokeo.com/geocode/v1/search.php?q=%s&api=%s' % (query, LOCATION_API_KEY))


resp = requests.get(url=url)
data = resp.json()
if 'status' in data:
    if data['status']=='ok':
        address=data['results'][0]['formatted_address']
        latitude=data['results'][0]['geometry']['location']['lat']
        longitude=data['results'][0]['geometry']['location']['lng']

        with open('location_data.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['address', 'latitude', 'longitude'])
            writer.writerow([address, latitude, longitude])


