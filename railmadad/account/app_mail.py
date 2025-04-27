import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
load_dotenv()

import smtplib

def register_email(receivers_email):
    try:
        # Get email credentials from .env
        email_host = os.getenv("MAIL_SERVER")
        email_port = int(os.getenv("MAIL_PORT"))
        email_user = os.getenv("MAIL_USERNAME")
        email_pass = os.getenv("MAIL_PASSWORD")

        # Setup email
        msg = MIMEMultipart()
        msg["From"] = email_user
        msg["To"] = f"{receivers_email}"
        msg["Subject"] = "Welcome to Our App – Register Complaints Easily!"
        body = """Dear User,

Welcome to our app! We are committed to providing you with a seamless experience for registering complaints regarding IRCTC rail services.

You can submit your concerns directly through our app, and our team will ensure that they are addressed promptly. Rest assured, your account details, including passwords, are securely stored using modern encryption standards.

🔹 Important Notice: This is a no-reply email. For any queries, please use the complaint registration section in our app.

Thank you for choosing our platform. We value your feedback and look forward to serving you better.

Best regards,
Code Harmonics Team
"""

        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP Server and send email
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, receivers_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return e


def raise_complaint_mail(receivers_email):
    try:
        # Get email credentials from .env
        email_host = os.getenv("MAIL_SERVER")
        email_port = int(os.getenv("MAIL_PORT"))
        email_user = os.getenv("MAIL_USERNAME")
        email_pass = os.getenv("MAIL_PASSWORD")

        # Setup email
        msg = MIMEMultipart()
        msg["From"] = email_user
        msg["To"] = f"{receivers_email}"
        msg["Subject"] = "Your complaint has reached us"
        body = """
        Dear User,

We have successfully received your complaint regarding IRCTC rail services. Thank you for taking the time to share your concern with us.

Our team is currently reviewing your complaint and will take the necessary steps to ensure it is addressed promptly. You can track the status of your complaint anytime through the app.

🔹 Please Note: This is a no-reply email. If you have additional information to provide, kindly use the complaint section in the app to update your submission.

Your feedback is valuable in helping us improve the quality of service.

Best regards,  
Code Harmonics Team

        """

        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP Server and send email
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, receivers_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return e