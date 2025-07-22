# aurora/fetch.py

import requests
import urllib3
import datetime as dt
import pytz
from dateutil import parser


# suppress the InsecureRequestWarning when we disable SSL verify
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# NOAA endpoints
BASE         = "https://services.swpc.noaa.gov"
REALTIME_URL = f"{BASE}/json/planetary_k_index_1m.json"
FORECAST_URL = f"{BASE}/products/noaa-planetary-k-index-forecast.json"
TZ           = pytz.timezone("America/Toronto")


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
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()["current"]["cloud_cover"]


def sun_times(lat, lon, date):
    """
    Sunrise/sunset from sunrise-sunset.org.
    Returns (sunrise: datetime[TZ], sunset: datetime[TZ]).
    """
    url = (
        f"https://api.sunrise-sunset.org/json"
        f"?lat={lat}&lng={lon}&date={date}&formatted=0"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    j  = resp.json()["results"]
    sr = dt.datetime.fromisoformat(j["sunrise"]).astimezone(TZ)
    ss = dt.datetime.fromisoformat(j["sunset"]).astimezone(TZ)
    return sr, ss


def moon_illumination(date):
    """
    Moon illumination % from FarmSense.
    """
    # ensure we have a datetime, not just a date
    if isinstance(date, dt.date) and not isinstance(date, dt.datetime):
        date = dt.datetime(date.year, date.month, date.day)

    ts  = int(date.timestamp())
    url = f"https://api.farmsense.net/v1/moonphases/?d={ts}"

    # disable cert verification to avoid the expired-certificate error
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()

    data = resp.json()
    return float(data[0]["Illumination"])
