# aurora/notify.py

import smtplib, ssl, os
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

def send_email(recipients, city, ev):
    """
    HTML email for *real-time* alerts.
    ev has 'score' and 'details' with kp, time, cloud_pct, sunrise, sunset, moon_pct.
    """
    msg = EmailMessage()
    msg["Subject"] = f"🌌 Aurora Alert {city['name']} – {ev['score']}%"
    msg["From"]    = os.environ["MAIL_FROM"]
    msg["To"]      = ", ".join(r["email"] for r in recipients)

    d = ev["details"]
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
      <h2>Aurora {city['name']} – {ev['score']}% Visibility</h2>
      <ul>
        <li><strong>Kp index:</strong> {d['kp']}</li>
        <li><strong>Time (local):</strong> {d['time']}</li>
        <li><strong>Cloud cover:</strong> {d['cloud_pct']}%</li>
        <li><strong>Moon illumination:</strong> {d['moon_pct']}%</li>
        <li><strong>Sunrise:</strong> {d['sunrise']}</li>
        <li><strong>Sunset:</strong> {d['sunset']}</li>
      </ul>
      <p>🗺️ <a href="https://www.swpc.noaa.gov/products/aurora-30-minute-forecast"
         target="_blank">NOAA 30-min Forecast Map</a></p>
      <hr>
      <p style="font-size:0.8em;">Subscribed to {city['name']} alerts.</p>
    </body></html>
    """
    msg.set_content("Aurora alert – view HTML version.")
    msg.add_alternative(html, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
        s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
        s.send_message(msg)


def send_forecast_email(recipients, city, details):
    """
    Plain-text email for *forecast* alerts.
    details has kp, event_time, kp_min.
    """
    msg = EmailMessage()
    msg["Subject"] = (
        f"🔮 Aurora Forecast {city['name']} – "
        f"Kp {details['kp']} at {details['event_time']}"
    )
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"]   = ", ".join(r["email"] for r in recipients)

    body = (
        f"NOAA 3-day forecast for {city['name']} predicts:\n"
        f"  • Kp index   = {details['kp']}\n"
        f"  • Event time = {details['event_time']} UTC\n"
        f"Threshold      = {details['kp_min']}\n"
    )
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
        s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
        s.send_message(msg)
