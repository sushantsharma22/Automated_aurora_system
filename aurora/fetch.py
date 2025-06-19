# aurora/fetch.py

import requests
import datetime as dt
import pytz
from dateutil import parser

# NOAA endpoints
BASE         = "https://services.swpc.noaa.gov"
REALTIME_URL = f"{BASE}/json/planetary_k_index_1m.json"
FORECAST_URL = f"{BASE}/json/3-day-forecast.json"

# Local timezone
TZ = pytz.timezone("America/Toronto")

def kp_now():
    """
    Latest *measured* planetary K-index.
    Returns (kp_index: float, time: datetime[TZ]).
    """
    resp = requests.get(REALTIME_URL, timeout=10)
    resp.raise_for_status()
    rec = resp.json()[-1]
    t = parser.isoparse(rec["time_tag"]).astimezone(TZ)
    return float(rec["kp_index"]), t

def kp_forecast():
    """
    NOAA 3-day *predicted* K-index in 3-h steps.
    Returns List[(kp: float, time: datetime[TZ])].
    """
    resp = requests.get(FORECAST_URL, timeout=10)
    resp.raise_for_status()
    out = []
    for rec in resp.json():
        t  = parser.isoparse(rec["time_tag"]).astimezone(TZ)
        kp = float(rec["kp_index"])
        out.append((kp, t))
    return out

def cloud_pct(lat, lon):
    """
    Current cloud cover % from Open-Meteo.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=cloud_cover"
    )
    return requests.get(url, timeout=10).json()["current"]["cloud_cover"]

def sun_times(lat, lon, date):
    """
    Sunrise/sunset from sunrise-sunset.org.
    Returns (sunrise: datetime[TZ], sunset: datetime[TZ]).
    """
    url = (
        f"https://api.sunrise-sunset.org/json"
        f"?lat={lat}&lng={lon}&date={date}&formatted=0"
    )
    j = requests.get(url, timeout=10).json()["results"]
    sr = dt.datetime.fromisoformat(j["sunrise"]).astimezone(TZ)
    ss = dt.datetime.fromisoformat(j["sunset"]).astimezone(TZ)
    return sr, ss

def moon_illumination(date):
    """
    Moon illumination % from FarmSense.
    """
    ts = int(date.strftime("%s"))
    url = f"https://api.farmsense.net/v1/moonphases/?d={ts}"
    return float(requests.get(url, timeout=10).json()[0]["Illumination"])
