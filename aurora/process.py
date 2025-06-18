import datetime as dt, pytz
from .config import CLOUD_MAX

def evaluate(city, data):
    kp, kp_time  = data["kp"]
    cloud        = data["cloud"]
    sunrise, sunset = data["sun"]
    moon_pct     = data["moon"]

    # dark if before sunrise or after sunset
    now  = kp_time
    dark = now < sunrise or now > sunset

    send = kp >= city["kp_min"] and cloud <= CLOUD_MAX and dark
    score = max(0, min(100,
        50 + (kp - city["kp_min"]) * 10 + (30 - cloud) * 0.5 - moon_pct * 0.1))

    return dict(send=send, score=round(score),
                details=dict(kp=kp, cloud=cloud, moon_pct=moon_pct,
                             time=kp_time.isoformat()))
