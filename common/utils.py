from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from django.conf import settings
import requests
from django.contrib.sites.models import Site


class CustomLimitOffsetPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'next': self.get_next_link() or 0,
            'previous': self.get_previous_link() or 0,
            'results': data
        })


def paypal_checkout_session(price, success_url, cancel_url, capture_id=""):
    try:
        current_site = Site.objects.get_current()

        auth_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
            verify=True
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get("access_token", "")

        print("access_token -- ", access_token)

        payment_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": "USD", "value": float(price)}}
            ],
            "application_context": {
                "return_url": f"{current_site.domain}{success_url}?capture={capture_id}",
                "cancel_url": f"{current_site.domain}{cancel_url}?capture={capture_id}"
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
            approve_link = next(link["href"] for link in payment_response["links"] if link["rel"] == "approve")
            return {
                "detail": "Payment url generate successfully",
                "id": payment_response['id'],
                "link": approve_link
            }
        except Exception as e:
            print("error", e)

    except Exception as e:
        print(e)

        return {"detail": f"fail to create payment due to  {str(e)}"}

    return {"detail": "fail to create payment"}

