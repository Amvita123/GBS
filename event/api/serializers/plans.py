from event.models import EventPlan
from rest_framework import serializers


class EventPlanSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = EventPlan
        fields = [
            "id", "name", "description", "price", "features"
        ]

    def get_name(self, obj):
        return obj.get_name_display()


class CheckoutSerializer(serializers.Serializer):
    plan = serializers.PrimaryKeyRelatedField(queryset=EventPlan.objects.filter(is_active=True, is_deleted=False))
