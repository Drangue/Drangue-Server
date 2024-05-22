from dotenv import load_dotenv
import os
from mailersend import emails
class EmailSender:
    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("MAILER_SENDER_API_KEY")
        self.mailer = emails.NewEmail(api_key)
        self.sender_email = "MS_M5j3Co@trial-pr9084zywvmgw63d.mlsender.net"
        self.reply_email = "MS_M5j3Co@trial-pr9084zywvmgw63d.mlsender.net"

    def send_email(self, recipient_name, recipient_email, subject, html_content, plaintext_content):
        mail_body = {}
        mail_from = {
            "name": "Drangue No Reply",
            "email": self.sender_email,
        }
        recipients = [
            {
                "name": recipient_name,
                "email": recipient_email,
            }
        ]
        reply_to = [
            {
                "name": "Drangue",
                "email": self.reply_email,
            }
        ]
        self.mailer.set_mail_from(mail_from, mail_body)
        self.mailer.set_mail_to(recipients, mail_body)
        self.mailer.set_subject(subject, mail_body)
        self.mailer.set_html_content(html_content, mail_body)
        self.mailer.set_plaintext_content(plaintext_content, mail_body)
        self.mailer.set_reply_to(reply_to, mail_body)
        return self.mailer.send(mail_body)