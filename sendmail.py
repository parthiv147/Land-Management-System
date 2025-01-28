import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sender_email = 'mushraf9a@gmail.com'
password = 'brhn kaft lwva vwov'

def send_email(receiver_email,subject,body,sender=sender_email,password=password):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach the Plain Body
        msg.attach(MIMEText(body,'plain'))
        # Attach the HTML Body
        # msg.attach(MIMEText(body,'html'))
        
        # Connecting to mail server
        server = smtplib.SMTP_SSL('smtp.gmail.com',465)
        server.login(sender,password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print('Error in sending mail:',e)
        return False