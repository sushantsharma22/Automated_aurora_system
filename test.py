# test.py

import os
import json
import datetime as dt
from dotenv import load_dotenv
load_dotenv()

from aurora import fetch, process, notify, config
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Confirm paths
print("📂 Current directory:", os.getcwd())

TZ = config.TZ

def test_google_sheet():
    print("\n🔍 Testing Google Sheets access...")
    cred_path = os.path.abspath("google-creds.json")
    print("📄 Using absolute path:", cred_path)

    with open(cred_path, "r") as f:
        creds = json.load(f)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds, scope))
    sheet = client.open_by_key(os.environ["GOOGLE_SHEET_ID"]).worksheet("Recipients")
    rows = sheet.get_all_records()
    print(f"✅ Sheet loaded. {len(rows)} rows found.")
    return sheet, rows

def test_fetch_kp():
    print("\n🔍 Testing real-time Kp fetch...")
    kp, kp_time = fetch.kp_now()
    print(f"✅ Current Kp: {kp} at {kp_time}")

    print("\n🔍 Testing forecast Kp fetch...")
    forecast = fetch.kp_forecast()
    print(f"✅ Forecast contains {len(forecast)} entries.")
    return (kp, kp_time), forecast

def test_weather_data(city):
    print(f"\n🔍 Fetching weather/sun/moon data for {city['name']}...")
    cloud = fetch.cloud_pct(city["lat"], city["lon"])
    sunrise, sunset = fetch.sun_times(city["lat"], city["lon"], dt.date.today())
    moon = fetch.moon_illumination(dt.date.today())
    print(f"✅ Cloud: {cloud}%, Sunrise: {sunrise.time()}, Sunset: {sunset.time()}, Moon: {moon}%")
    return {
        "kp": (6.0, dt.datetime.now(TZ)),  # Force valid kp for test
        "cloud": cloud,
        "sun": (sunrise, sunset),
        "moon": moon,
    }

def test_evaluation(city, data, forecast):
    print("\n🧠 Running real-time evaluation...")
    now_result = process.evaluate_now(city, data)
    print(f"Send: {now_result['send']}, Score: {now_result['score']}")
    print("Details:", now_result["details"])

    print("\n🔮 Running forecast evaluation...")
    send, details = process.evaluate_forecast(city, forecast)
    print(f"Send: {send}, Details:", details)

def test_email_dry_run(city, recipients, now_result, forecast_details):
    print("\n📧 Dry-run: preparing email payloads (no send)...")
    try:
        notify.send_email(recipients, city, now_result)
        notify.send_forecast_email(recipients, city, forecast_details)
        print("✅ Email format OK.")
    except Exception as e:
        print("❌ Email formatting failed:", e)

def main():
    sheet, rows = test_google_sheet()
    (kp, kp_time), forecast = test_fetch_kp()

    city = config.CITIES[0]
    data = test_weather_data(city)
    test_evaluation(city, data, forecast)

    fake_recipient = [{"email": "test@example.com", "name": "Tester"}]
    now_result = process.evaluate_now(city, data)
    _, forecast_details = process.evaluate_forecast(city, forecast)
    if not forecast_details:
        forecast_details = {"kp": 7, "event_time": "N/A", "kp_min": city["kp_min"]}

    test_email_dry_run(city, fake_recipient, now_result, forecast_details)

if __name__ == "__main__":
    main()
