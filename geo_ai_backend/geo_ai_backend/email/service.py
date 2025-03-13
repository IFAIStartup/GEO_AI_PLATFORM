import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from geo_ai_backend.config import settings


def send_email(receiver_email: str, subject: str, template: str) -> None:
    """Send notification to user email."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.MAIL_FROM
    message["To"] = receiver_email
    message.attach(MIMEText(template, "html"))

    if settings.ARABIC_STAND:
        send_email_arabic(receiver_email=receiver_email, message=message.as_string())
    else:
        send_email_default(receiver_email=receiver_email, message=message.as_string())


def send_email_arabic(receiver_email: str, message: str) -> None:
    """Send email using TLS (Port 587)"""
    server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
    server.ehlo()  
    server.starttls()  
    server.ehlo()
    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)  
    server.sendmail(settings.MAIL_FROM, receiver_email, message)
    server.quit()


def send_email_default(receiver_email: str, message: str) -> None:
    """Send email using SSL (Port 465)"""
    with smtplib.SMTP_SSL(
        host=settings.MAIL_SERVER,
        port=settings.MAIL_PORT,
        context=ssl.create_default_context(),
    ) as server:
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(
            from_addr=settings.MAIL_FROM,
            to_addrs=receiver_email,
            msg=message,
        )
