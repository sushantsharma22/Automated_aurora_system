# aurora/main.py

import datetime as dt
import pytz
from aurora import fetch, process, notify, config
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json

# Local timezone
TZ = pytz.timezone("America/Toronto")


def load_recipients(city_name):
    """
    Load sheet rows for this city.
    """
    with open(os.environ["GOOGLE_SHEETS_CREDS_FILE"], "r") as f:
        creds = json.load(f)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds  = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(os.environ["GOOGLE_SHEET_ID"]) \
                   .worksheet("Recipients")
    rows = sheet.get_all_records()
    recs = []
    for idx, row in enumerate(rows):
        if row["city"].lower() == city_name.lower():
            row["_sheet_row"] = idx + 2
            recs.append(row)
    return recs, sheet


def should_notify_rt(rec, now_dt):
    """
    Real-time: only if never sent, or ≥4h since last_rt_notified.
    """
    last = rec.get("last_rt_notified", "").strip()
    if not last:
        return True
    last_dt = dt.datetime.fromisoformat(last)
    return (now_dt - last_dt) >= dt.timedelta(hours=4)


def should_notify_forecast(rec, today):
    """
    Forecast: only once per calendar day.
    """
    last = rec.get("last_notified", "").strip()
    return (not last) or (last != str(today))


def update_last_rt(sheet, recs, now_iso):
    for r in recs:
        sheet.update_cell(r["_sheet_row"], 5, now_iso)  # assumes col 5 is last_rt_notified


def update_last_notified(sheet, recs, today):
    for r in recs:
        sheet.update_cell(r["_sheet_row"], 4, str(today))  # col 4 is last_notified


def run():
    now_dt = dt.datetime.now(TZ)
    today  = now_dt.date()

    for city in config.CITIES:
        print(f"\n🔍 Evaluating {city['name']} at {now_dt.isoformat()}")

        # ─── Real-time ───────────────────────────────
        data_now = {
            "kp":    fetch.kp_now(),
            "cloud": fetch.cloud_pct(city["lat"], city["lon"]),
            "sun":   fetch.sun_times(city["lat"], city["lon"], today),
            "moon":  fetch.moon_illumination(today),
        }
        ev_now = process.evaluate_now(city, data_now)
        d_now  = ev_now["details"]

        print(f"▶ Real-time: kp={d_now['kp']}, cloud={d_now['cloud_pct']}%, "
              f"moon={d_now['moon_pct']}%, score={ev_now['score']}, send={ev_now['send']}")

        if ev_now["send"]:
            recs, sheet = load_recipients(city["name"])
            to_send = [r for r in recs if should_notify_rt(r, dt.datetime.fromisoformat(d_now["time"]))]
            if to_send:
                print(f"✉️ Sending real-time to {[r['email'] for r in to_send]}")
                notify.send_email(to_send, city, ev_now)
                update_last_rt(sheet, to_send, d_now["time"])
            else:
                print("✔️ Real-time: cooldown in effect, skipping.")

        # ─── Forecast ────────────────────────────────
        send_fc, details_fc = process.evaluate_forecast(city, fetch.kp_forecast())
        if send_fc:
            # only at the designated 10 AM hour
            nt = dt.datetime.fromisoformat(details_fc["notify_time"])
            if (now_dt.date() == nt.date() and now_dt.hour == nt.hour):
                recs_fc, sheet_fc = load_recipients(city["name"])
                to_send_fc = [r for r in recs_fc if should_notify_forecast(r, today)]
                if to_send_fc:
                    print(f"✉️ Sending forecast to {[r['email'] for r in to_send_fc]}")
                    notify.send_forecast_email(to_send_fc, city, details_fc)
                    update_last_notified(sheet_fc, to_send_fc, today)
                else:
                    print("✔️ Forecast: already sent today, skipping.")
            else:
                print(f"⏳ Forecast queued for {details_fc['notify_time']} (now {now_dt.hour}h).")
        else:
            print("🚫 Forecast: no kp crossing threshold.")

if __name__ == "__main__":
    run()
