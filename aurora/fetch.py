# aurora/fetch.py

import requests
import urllib3
import datetime as dt
import pytz
from dateutil import parser
import math


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
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
        # Farmsense returns Illumination as a percentage-like number
        return float(data[0]["Illumination"])
    except (requests.exceptions.SSLError, requests.exceptions.RequestException, KeyError, IndexError):
        # If the external API fails (SSL handshake, network, or unexpected JSON),
        # compute an approximate illumination fraction locally so the workflow
        # can continue without external dependency.
        # Algorithm: use simple synodic-month age -> illumination formula.
        def _julian_date(dt_obj: dt.datetime) -> float:
            y = dt_obj.year
            m = dt_obj.month
            # include fractional day
            day = dt_obj.day + (dt_obj.hour + dt_obj.minute / 60.0 + dt_obj.second / 3600.0) / 24.0
            if m <= 2:
                y -= 1
                m += 12
            A = math.floor(y / 100)
            B = 2 - A + math.floor(A / 4)
            jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + B - 1524.5
            return jd

        jd = _julian_date(date)
        # days since known new moon epoch (J2000-ish)
        days_since_epoch = jd - 2451550.1
        synodic_month = 29.53058867
        # age into current lunar cycle
        age = days_since_epoch % synodic_month
        # illuminated fraction (0..1)
        frac = (1 - math.cos(2 * math.pi * age / synodic_month)) / 2
        return float(frac * 100.0)
