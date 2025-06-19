# aurora/fetch.py

import requests
import datetime as dt
import pytz
from dateutil import parser

# NOAA endpoints
BASE              = "https://services.swpc.noaa.gov"
REALTIME_URL      = f"{BASE}/json/planetary_k_index_1m.json"
FORECAST_URL      = f"{BASE}/products/noaa-planetary-k-index-forecast.json"  # ← corrected
TZ                = pytz.timezone("America/Toronto")

def kp_now():
    """
    Fetch the latest *measured* planetary K-index.
    """
    resp = requests.get(REALTIME_URL, timeout=10)
    resp.raise_for_status()
    rec = resp.json()[-1]
    return (
        float(rec["kp_index"]),
        parser.isoparse(rec["time_tag"]).astimezone(TZ)
    )

def kp_forecast():
    """
    Fetch NOAA’s 3-day *predicted* K-index feed.
    Returns a list of (kp: float, time: datetime[TZ]) for predicted entries only.
    """
    resp = requests.get(FORECAST_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    out = []
    for rec in data:
        # rec is like ["2025-06-20 00:00:00", "3.67", "predicted", null]
        time_tag, kp_str, obs_flag = rec[0], rec[1], rec[2]
        if obs_flag != "observed":    # only take the forecasted points
            t  = parser.isoparse(time_tag + "Z").astimezone(TZ)
            kp = float(kp_str)
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
