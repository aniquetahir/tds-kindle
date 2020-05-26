# Import smtplib for the actual sending function
import smtplib
import os

# Here are the email package modules we'll need
from email.message import EmailMessage


def send_mail(mail_from: str, mail_to: str, subject: str,
              server: str, port: int = 0, username: str = None,
              password: str = None, files=None, preamble=None):
    # Create the container email message.
    msg = EmailMessage()
    msg['Subject'] = subject
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = mail_from
    msg['To'] = mail_to

    if preamble:
        msg.preamble = preamble+'\n'

    # Open the files in binary mode.  Use imghdr to figure out the
    # MIME subtype for each specific image.
    if files:
        for file in files:
            with open(file['path'], 'rb') as fp:
                file_data = fp.read()
            msg.add_attachment(file_data, maintype=file['type'],
                               subtype = file['subtype'],
                               filename=os.path.basename(file['path']) )

    # Send the email via our own SMTP server.
    with smtplib.SMTP_SSL(server, port) as s:
        if username:
            s.login(username, password)
        s.send_message(msg)


