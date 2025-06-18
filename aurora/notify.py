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
    html = (f"<p><b>{city['name']}</b> chance: <b>{ev['score']}%</b><br>"
            f"Kp={d['kp']} · Cloud={d['cloud']}% · Moon={d['moon_pct']}%</p>"
            f"<p>Prediction time: {d['time']}</p>"
            f'<p>Live map: <a href="https://www.swpc.noaa.gov/products/'
            f'aurora-30-minute-forecast">NOAA 30-min forecast</a></p>')
    msg.set_content(html, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as s:
        s.login(os.environ["MAIL_FROM"], os.environ["MAIL_APP_PASS"])
        s.send_message(msg)
