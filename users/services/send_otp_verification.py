from django.template.loader import render_to_string
import random
from django.core.cache import cache
from users.task import auth_mail_send, send_sms
from datetime import datetime


def send_otp_to_mail(username, user_email, phone_number):
    otp = random.randint(100000, 999999)
    html_message = render_to_string('mail/otp_verification.html', {
        'username': username.title(),
        'otp': otp,
        "year": str(datetime.now().year)
    })
    cache.set(f"otp_{user_email}", otp, 60*10)
    subject = 'OTP for Verification'
    auth_mail_send.delay(subject, html_message, user_email)

    sms_body = f"""
    Hello {username} from Athlete Rated! Your one-time password (OTP) is: {otp}. It will expire in 10 minutes. Do not share this code with anyone.
    """

    send_sms.delay(phone_number, sms_body)


def send_forget_password_otp(fullname, user_email, phone_number):
    otp = random.randint(100000, 999999)
    html_message = render_to_string('mail/otp_verification.html', {
        'username': fullname.title(),
        'otp': otp,
        "year": str(datetime.now().year)
    })
    cache.set(f"forget_otp_{user_email}", otp, 60 * 10)
    subject = 'Forget password email verification'
    auth_mail_send.delay(subject, html_message, user_email)

    sms_body = f"""
    Hello {fullname}, you requested to reset your password for Athlete Rated. 
    Your one-time password (OTP) is: {otp}. It will expire in 10 minutes. 
    Do not share this code with anyone.
    """
    send_sms.delay(phone_number, sms_body)
