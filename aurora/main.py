from aurora import fetch, process, notify, config
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, datetime as dt, json

FORCE_SEND = True  # Always send for testing

def load_recipients(city_name):
    creds_dict = json.loads(os.environ["GOOGLE_SHEETS_CREDS"])
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(os.environ["GOOGLE_SHEET_ID"]).worksheet("Recipients")
    rows = sheet.get_all_records()
    return [r for r in rows if r["city"].lower() == city_name.lower()]

def run():
    today = dt.date.today()
    for city in config.CITIES:
        print(f"\n🔍 Evaluating: {city['name']}")
        data = dict(
            kp=fetch.kp_now(),
            cloud=fetch.cloud_pct(city["lat"], city["lon"]),
            sun=fetch.sun_times(city["lat"], city["lon"], today),
            moon=fetch.moon_illumination(today),
        )
        ev = process.evaluate(city, data)
        d = ev["details"]

        print(f"📊 Kp: {d['kp']} | Clouds: {d['cloud']}% | Moon: {d['moon_pct']}%")
        print(f"🕒 Time: {d['time']} | Score: {ev['score']} | Send: {ev['send']}")

        if ev["send"] or FORCE_SEND:
            recips = load_recipients(city["name"])
            if recips:
                print(f"📨 Sending to: {[r['email'] for r in recips]}")
                notify.send_email(recips, city, ev)
            else:
                print("⚠️ No recipients found for this city.")
        else:
            print("🚫 Conditions not met; skipping send.")

if __name__ == "__main__":
    run()
