from django.conf import settings
import requests
from event.models import EventTransaction
from django.contrib.sites.models import Site
from requests.auth import HTTPBasicAuth


def paypal_checkout_session(plan, user, event):
    try:
        current_site = Site.objects.get_current()

        auth_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
            verify=True
        )
        print(auth_response)
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token", "")

        print("access_token -- ", access_token)

        payment_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": "USD", "value": float(plan.price)}}
            ],
            "application_context": {
                "return_url": f"{current_site.domain}/api/event/payment/success/",
                "cancel_url": f"{current_site.domain}/event/payment/cancel/"
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

            EventTransaction.objects.create(
                user=user,
                session_id=payment_response["id"],
                amount=plan.price,
                event_plan=plan,
                event=event
            )
            approve_link = next(link["href"] for link in payment_response["links"] if link["rel"] == "approve")
            return {
                "detail": "Event create successfully please pay to enable your events",
                "id": payment_response['id'],
                "link": approve_link
            }
        except Exception as e:
            print("error", e)

    except Exception as e:
        print(e)

        return {"detail": f"fail to create payment due to  {str(e)}"}

    return {"detail": "fail to create payment"}






