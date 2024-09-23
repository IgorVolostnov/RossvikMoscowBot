import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from aiosmtplib import SMTP
import os


logging.basicConfig(level=logging.INFO)


async def send_mail(subject_letter: str, to_mail: str, message_text: str):
    message = MIMEMultipart()
    message["From"] = os.environ["EMAIL"]
    message["To"] = to_mail
    message["Subject"] = subject_letter
    message.attach(MIMEText(f"<html><body>{message_text}</body></html>", "html", "utf-8"))

    smtp_client = SMTP(hostname="smtp.mail.ru", port=465, use_tls=True)
    async with smtp_client:
        await smtp_client.login(os.environ["EMAIL"], os.environ["PASSWORD"])
        await smtp_client.send_message(message)


async def send_message(subject_letter: str, to_mail: str, message_text: str):
    await send_mail(subject_letter, to_mail, f'<h1>{message_text}</h1>')
