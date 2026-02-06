from rest_framework.permissions import BasePermission
from django.contrib.sites.models import Site
import requests
from django.conf import settings
from coach.models import OrganizationTransaction


class IsCoachUser(BasePermission):
    """
    Custom permission to allow only users with role 'coach' to create objects.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == "coach"


class IsCoachFanUser(BasePermission):
    """
    Custom permission to allow only users with role 'coach' or 'fan' to create objects.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.user_role == "coach" or request.user.user_role == "fan")


class IsCoachOrPlayer(BasePermission):
    """
    Custom permission to allow only users with role 'coach' or 'player' to create objects.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.user_role == "coach" or request.user.user_role == "player")


def organization_paypal_checkout_session(price, user, organization):
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
                "cancel_url": f"{current_site.domain}/users/verification-payment/cancel/",
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

            OrganizationTransaction.objects.create(
                organization=organization,
                user=user,
                session_id=payment_response["id"],
                amount=price
            )

            approve_link = next(link["href"] for link in payment_response["links"] if link["rel"] == "approve")
            return {
                "detail": "Your Organization created successfully.",
                "id": payment_response['id'],
                "link": approve_link
            }
        except Exception as e:
            print("error", e)

    except Exception as e:
        print(e)

        return {"detail": f"fail to create payment due to  {str(e)}"}

    return {"detail": "fail to create payment"}

