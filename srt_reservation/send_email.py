import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, sender=None, recipient=None, app_password=None):

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(msg)
        print("이메일 전송 완료")

