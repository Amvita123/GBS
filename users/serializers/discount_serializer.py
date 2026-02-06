from rest_framework import serializers
from users.models.discount_management import DiscountCode
from users.models.discount_management import DiscountCodeUsage

class ValidateDiscountCodeSerializer(serializers.Serializer):
    discount_code = serializers.CharField(required=True)
    def validate_discount_code(self, value):
        user = self.context["request"].user
        try:
            discount = DiscountCode.objects.get(code_identifier=value)
        except DiscountCode.DoesNotExist:
            raise serializers.ValidationError("Invalid discount code")
        if discount.usage_limit == discount.current_usage:
            raise serializers.ValidationError("Discount code expired")
        if DiscountCodeUsage.objects.filter(user=user, discount=discount).exists():
            raise serializers.ValidationError("You already used this code")
        return value

