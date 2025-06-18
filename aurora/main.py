from aurora import fetch, process, notify, config
import csv, base64, os, datetime as dt

def load_recipients(city_name):
    """CSV stored in a GitHub secret – base64-encoded, one line per recipient."""
    rows = base64.b64decode(os.environ["RECIPIENT_CSV"]).decode().splitlines()
    return [dict(email=r[1], name=r[2])
            for r in csv.reader(rows) if r[0] == city_name]

def run():
    today = dt.date.today()
    for city in config.CITIES:
        data = dict(
            kp=fetch.kp_now(),
            cloud=fetch.cloud_pct(city["lat"], city["lon"]),
            sun=fetch.sun_times(city["lat"], city["lon"], today),
            moon=fetch.moon_illumination(today),
        )
        ev = process.evaluate(city, data)
        if ev["send"]:
            recips = load_recipients(city["name"])
            if recips:
                notify.send_email(recips, city, ev)

if __name__ == "__main__":
    run()
