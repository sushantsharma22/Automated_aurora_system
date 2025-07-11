# aurora/notify.py

import smtplib, ssl, os
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_email(recipients, city, ev):
    """
    HTML email for real-time alerts.
    """
    for r in recipients:
        msg = EmailMessage()
        msg["Subject"] = f"🌌 Aurora Alert for {city['name']} – {ev['score']}% Chance Tonight"
        msg["From"] = f"Aurora Alert System <{os.environ['MAIL_FROM']}>"
        msg["To"] = r["email"]

        name = r.get("name", "there")  # Fallback if name is missing
        d = ev["details"]

        plain_text = f"""Hello {name},

Aurora Alert for {city['name']}:
- Kp index: {d['kp']}
- Local time: {d['time']}
- Cloud cover: {d['cloud_pct']}%
- Moon: {d['moon_pct']}% illuminated
- Sunrise: {d['sunrise']}
- Sunset: {d['sunset']}

View forecast map: https://www.swpc.noaa.gov/products/aurora-30-minute-forecast

You're receiving this alert because you're subscribed to aurora updates for {city['name']}.
Reply with "unsubscribe" to opt out."""

        html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
          <h2>🌌 Aurora Alert for {city['name']}</h2>
          <p>Hello {name},</p>
          <p>
            Heads up! Based on current space weather, there's a <strong>{ev['score']}%</strong> chance of seeing the aurora tonight in <strong>{city['name']}</strong>.
          </p>
          <ul>
            <li><strong>Kp index:</strong> {d['kp']}</li>
            <li><strong>Local Time:</strong> {d['time']}</li>
            <li><strong>Cloud Cover:</strong> {d['cloud_pct']}%</li>
            <li><strong>Moon Illumination:</strong> {d['moon_pct']}%</li>
            <li><strong>Sunrise:</strong> {d['sunrise']}</li>
            <li><strong>Sunset:</strong> {d['sunset']}</li>
          </ul>
          <p>🔗 <a href="https://www.swpc.noaa.gov/products/aurora-30-minute-forecast" target="_blank">View Forecast Map</a></p>
          <hr>
          <p style="font-size:0.85em; color:#666;">
            You’re receiving this alert because you subscribed to updates for {city['name']}.<br>
            To stop receiving these, simply reply with “unsubscribe”.
          </p>
        </body></html>
        """

        msg.set_content(plain_text)
        msg.add_alternative(html, subtype="html")

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
            s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
            s.send_message(msg)


def send_forecast_email(recipients, city, details):
    """
    Plain-text forecast alert email.
    """
    for r in recipients:
        msg = EmailMessage()
        msg["Subject"] = (
            f"🔮 Aurora Forecast for {city['name']} – "
            f"Kp {details['kp']} at {details['event_time']} UTC"
        )
        msg["From"] = f"Aurora Alert System <{os.environ['MAIL_FROM']}>"
        msg["To"] = r["email"]

        name = r.get("name", "there")  # Personalize with fallback

        body = (
            f"Hello {name},\n\n"
            f"Aurora activity is expected soon in {city['name']}:\n"
            f"• Kp Index: {details['kp']}\n"
            f"• Peak Time (UTC): {details['event_time']}\n"
            f"• Your alert threshold: {details['kp_min']}\n\n"
            f"You’re receiving this alert because you're subscribed to updates for {city['name']}.\n"
            f"Reply with \"unsubscribe\" to stop receiving future alerts.\n"
        )

        msg.set_content(body)

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
            s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
            s.send_message(msg)
