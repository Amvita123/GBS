from django.contrib.sites.models import Site
import requests
from django.conf import settings
from django.template.loader import render_to_string
from users.task import auth_mail_send
from datetime import datetime
from django.utils.html import strip_tags
from django.core.mail import send_mail
from users.models import VerificationTransaction
import requests
from users.models.discount_management import DiscountCode
from rest_framework import serializers
from users.models import DiscountCodeUsage


def verification_paypal_checkout_session(price, user, verification_obj, discount=None):
    try:
        current_site = Site.objects.all().first()
        auth_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
            verify=True
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token", "")

        payment_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": "USD", "value": float(price)}}
            ],
            "application_context": {
                "return_url": f"{current_site.domain}/users/verification-payment/success/",
                "cancel_url": f"{current_site.domain}/users/verification-payment/cancel/"
            }
        }

        print(f"{settings.PAYPAL_API_BASE}/v2/checkout/orders")

        payment_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=payment_payload
        )

        try:
            payment_response = payment_response.json()
            print(payment_response)

            if discount:
                verification_obj.discount = discount
                verification_obj.save(update_fields=["discount"])

            VerificationTransaction.objects.get_or_create(
                user=user,
                session_id=payment_response["id"],
                amount=price,
                verification=verification_obj
            )

            # VerificationTransaction.objects.get_or_create(
            #     user=user,
            #     verification=verification_obj,
            #     defaults={
            #         "session_id": payment_response["id"],
            #         "amount": price
            #     }
            # )

            approve_link = next(link["href"] for link in payment_response["links"] if link["rel"] == "approve")
            return {
                "detail": "Your Document upload successfully.",
                "id": payment_response['id'],
                "link": approve_link
            }
        except Exception as e:
            print("error", e)

    except Exception as e:
        print(e)

        return {"detail": f"fail to create payment due to  {str(e)}"}

    return {"detail": "fail to create payment"}


def send_parent_verification_mail(verification_obj,):
    html_message = render_to_string('mail/parent_verification.html', {
        'athlete_name': verification_obj.legal_full_name,
        "parent_name": verification_obj.parent_legal_name,
        "dob": verification_obj.dob,
        "document_type": verification_obj.document_type.title,
        "verification_link": f"https://athleterated.com/users/parent-verification/{verification_obj.id}"

    })
    subject = 'Child Account verification'
    # auth_mail_send.delay(subject, html_message, verification_obj.parent_email)

    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [verification_obj.parent_email],
            html_message=html_message
        )
        return "mail sent successfully."
    except Exception as e:
        return f"error to send mail: \n {str(e)}"

def get_discounted_amount_value(base_pay, request):
    amount = base_pay
    discount_obj = None
    discount_code = request.data.get("discount_code")

    if discount_code:
        try:
            discount_obj = DiscountCode.objects.get(code_identifier=discount_code)

            if DiscountCodeUsage.objects.filter(user=request.user, discount=discount_obj).exists():
                raise serializers.ValidationError({"detail": "You have already used this discount code."})

            if discount_obj.usage_limit and discount_obj.current_usage >= discount_obj.usage_limit:
                raise serializers.ValidationError({"detail": "Discount code limit exceed"})

            if discount_obj.is_active and discount_obj.usage_limit != discount_obj.current_usage:
                discount_amount = (amount * discount_obj.code_value) / 100
                amount = amount - discount_amount
        except DiscountCode.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid discount code."})
    return round(amount, 2), discount_obj