import smtplib
from email.mime.text import MIMEText

def send_email(subject, body):
    sender = 'didals0521@gmail.com'
    recipient = 'didals0521@gmail.com'
    app_password = 'sshtaqduajqfbslu'  # 앱 비밀번호

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(msg)
        print("이메일 전송 완료")

# # 테스트
# send_email("", "웹사이트에서 조건을 만족했습니다. 확인하세요!")
