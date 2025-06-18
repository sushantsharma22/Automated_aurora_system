import smtplib, ssl, os
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

def send_email(recipients, city, ev):
    msg = EmailMessage()
    msg["Subject"] = f"🌌 Aurora Alert {city['name']} – {ev['score']}%"
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"]   = ", ".join(r["email"] for r in recipients)

    d = ev["details"]
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>🌌 Aurora Forecast for <b>{city['name']}</b></h2>
        <p><b>Chance:</b> <span style="color: green;">{ev['score']}%</span></p>
        <ul>
            <li><b>Kp Index:</b> {d['kp']}</li>
            <li><b>Cloud Cover:</b> {d['cloud']}%</li>
            <li><b>Moonlight:</b> {d['moon_pct']}%</li>
        </ul>
        <p><b>Prediction Time:</b><br>{d['time']}</p>
        <p>🗺️ <a href="https://www.swpc.noaa.gov/products/aurora-30-minute-forecast" target="_blank">
        NOAA 30-min Aurora Forecast Map</a></p>
        <hr>
        <p style="font-size: 0.85em;">You're receiving this alert because you're subscribed for aurora updates in {city['name']}.</p>
    </body>
    </html>
    """

    msg.set_content("Aurora alert attached as HTML.")
    msg.add_alternative(html, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
        s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
        s.send_message(msg)
