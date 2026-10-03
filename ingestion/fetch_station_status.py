from datetime import datetime, timezone

import requests

URL = "https://api.cyclocity.fr/contracts/dublin/gbfs/v2/station_status.json"

response = requests.get(URL, timeout=30)   # call the API; give up after 30 seconds
response.raise_for_status()                # stop with an error if the status isn't 200 OK
payload = response.json()                  # turn the JSON text into Python dicts and lists

stations = payload["data"]["stations"]
feed_time = datetime.fromtimestamp(payload["last_updated"], tz=timezone.utc)

print(f"Feed last updated (UTC): {feed_time}")
print(f"Stations in feed: {len(stations)}")
print(f"First station: {stations[0]}")