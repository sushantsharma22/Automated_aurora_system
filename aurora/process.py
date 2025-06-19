# aurora/process.py

import datetime as dt
from .config import CLOUD_MAX

def evaluate_now(city, data):
    """
    Real-time alert: send only if
      1) measured Kp ≥ kp_min
      2) cloud_pct ≤ CLOUD_MAX
      3) it’s dark (before sunrise OR after sunset)

    Returns dict(send: bool, score: int, details: dict).
    """
    kp, kp_time      = data["kp"]
    cloud_pct        = data["cloud"]
    sunrise, sunset  = data["sun"]
    moon_pct         = data["moon"]

    # 1) thresholds
    kp_ok    = kp >= city["kp_min"]
    cloud_ok = cloud_pct <= CLOUD_MAX
    dark_ok  = (kp_time < sunrise) or (kp_time > sunset)

    send = kp_ok and cloud_ok and dark_ok

    # 2) visibility score (0–100) for your email body
    raw_score = (
        50
        + (kp - city["kp_min"]) * 10
        + (30 - cloud_pct) * 0.5
        - moon_pct * 0.1
    )
    score = max(0, min(100, raw_score))

    details = {
        "kp":        kp,
        "time":      kp_time.isoformat(),
        "cloud_pct": cloud_pct,
        "sunrise":   sunrise.isoformat(),
        "sunset":    sunset.isoformat(),
        "moon_pct":  moon_pct,
    }

    return {"send": send, "score": round(score), "details": details}


def evaluate_forecast(city, forecast):
    """
    Advance-warning: find the *earliest* forecasted time where
    kp ≥ city['kp_min'], then compute a notify timestamp at 10 AM.

    Returns (send: bool, details: dict):
      details = {
        kp: float,
        event_time: iso8601 str,
        notify_time: iso8601 str,
        kp_min: int
      }
    """
    kp_min = city["kp_min"]
    # earliest crossing
    event = next(((kp, t) for kp, t in forecast if kp >= kp_min), None)
    if event is None:
        return False, {}

    kp_val, event_time = event

    # decide which day to notify at 10 AM
    if event_time.hour >= 10:
        notify_date = event_time.date()
    else:
        notify_date = event_time.date() - dt.timedelta(days=1)

    # 10:00 local on that date
    notify_time = dt.datetime.combine(
        notify_date,
        dt.time(hour=10, minute=0),
        tzinfo=event_time.tzinfo
    )

    details = {
        "kp":           kp_val,
        "event_time":   event_time.isoformat(),
        "notify_time":  notify_time.isoformat(),
        "kp_min":       kp_min,
    }
    return True, details
