from rest_framework import serializers
from common.models import Setting

class TermsConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['terms_conditions', 'privacy_policy']