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
        body = """Dear Train Manager,

We appreciate your role in ensuring smooth rail operations. Our platform is designed to streamline the process of receiving and addressing complaints related to IRCTC rail services.

You can now efficiently track and manage passenger concerns through our app, ensuring swift resolution and improved service quality. Our system securely handles all data with modern encryption standards, maintaining confidentiality and compliance.

🔹 Important Notice: This is an automated email. For operational inquiries or complaint escalations, please use the complaint management section within our app.

Thank you for your dedication to passenger service. We value your efforts and look forward to supporting you in delivering a seamless travel experience.

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
