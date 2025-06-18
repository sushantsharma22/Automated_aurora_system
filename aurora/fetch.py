import requests, datetime as dt, pytz
BASE   = "https://services.swpc.noaa.gov"
TZ     = pytz.timezone("America/Toronto")

def kp_now():
    url = f"{BASE}/json/planetary_k_index_1m.json"
    data = requests.get(url, timeout=10).json()[-1]
    return float(data["kp_index"]), dt.datetime.fromisoformat(data["time_tag"]).astimezone(TZ)

def cloud_pct(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lon}&current=cloud_cover")
    return requests.get(url, timeout=10).json()["current"]["cloud_cover"]

def sun_times(lat, lon, date):
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date}&formatted=0"
    j = requests.get(url, timeout=10).json()["results"]
    return (dt.datetime.fromisoformat(j["sunrise"]).astimezone(TZ),
            dt.datetime.fromisoformat(j["sunset"]).astimezone(TZ))

def moon_illumination(date):
    url = f"https://api.farmsense.net/v1/moonphases/?d={date.strftime('%s')}"
    return float(requests.get(url, timeout=10).json()[0]["Illumination"])
