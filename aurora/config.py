from datetime import timedelta
import os
from dotenv import load_dotenv
import pytz

TZ = pytz.timezone("America/Toronto")

load_dotenv()  # Load .env values into os.environ

CITIES = [
    dict(
        name="Windsor",
        lat=42.3149,
        lon=-83.0364,
        kp_min=6,
    ),
]

# global thresholds
CLOUD_MAX = 50  # %
CHECK_INTERVAL = timedelta(minutes=15)

# optional admin email (if you want to use it later)
ADMIN_EMAIL = os.getenv("MAIL_FROM", "auroraalertss@gmail.com")

