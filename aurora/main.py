from aurora import fetch, process, notify, config
import csv, base64, os, datetime as dt

# 🧪 Toggle this to True to force send emails (for testing)
FORCE_SEND = True

def load_recipients(city_name):
    """CSV stored in a GitHub secret – base64-encoded, one line per recipient."""
    rows = base64.b64decode(os.environ["RECIPIENT_CSV"]).decode().splitlines()
    return [dict(email=r[1], name=r[2])
            for r in csv.reader(rows) if r[0] == city_name]

def run():
    today = dt.date.today()
    for city in config.CITIES:
        print(f"\n🔍 Evaluating: {city['name']}")

        # Fetch all relevant data
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
