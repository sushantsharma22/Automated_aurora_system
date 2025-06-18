from aurora import fetch, process, notify, config
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, datetime as dt, json

def load_recipients(city_name):
    """Load recipients from Google Sheets matching city."""
    creds_dict = json.loads(os.environ["GOOGLE_SHEETS_CREDS"])
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(os.environ["GOOGLE_SHEET_ID"]).worksheet("Recipients")
    rows = sheet.get_all_records()
    recipients = []

    for idx, row in enumerate(rows):
        if row["city"].lower() == city_name.lower():
            row["_sheet_row"] = idx + 2  # account for 1-based sheet + header row
            recipients.append(row)

    return recipients, sheet

def should_notify(recipient, score, today):
    """Return True if user hasn't been notified today or score is high."""
    last = recipient.get("last_notified")
    if not last or last.strip() == "":
        return True
    if score >= 50:
        return True
    return last != str(today)

def update_last_notified(sheet, recipients, today):
    """Write today's date to last_notified column for notified users."""
    for r in recipients:
        row = r["_sheet_row"]
        sheet.update_cell(row, 4, str(today))  # col 4 = last_notified

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

        if ev["send"]:
            all_recipients, sheet = load_recipients(city["name"])
            recipients = [r for r in all_recipients if should_notify(r, ev["score"], today)]

            if recipients:
                print(f"📨 Sending to: {[r['email'] for r in recipients]}")
                notify.send_email(recipients, city, ev)
                update_last_notified(sheet, recipients, today)
            else:
                print("✅ Recipients already notified today or skipped.")
        else:
            print("🚫 Conditions not met; skipping send.")

if __name__ == "__main__":
    run()
