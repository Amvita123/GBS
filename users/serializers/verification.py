from rest_framework import serializers
from users.models import IdentityVerification, AthleteTypes, DocumentType, ReferralOrganization, SchoolDocument
from datetime import date


class IdentityVerificationSerializer(serializers.ModelSerializer):
    refer_by = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = IdentityVerification
        fields = ['legal_full_name', "photo", "athlete_type", "dob", "document_type", "identity_img",
                  "parent_legal_name", "parent_email", "parent_phone_number", "is_under", "status", "remark", "reject_reason",
                  "created_at", "id", "refer_by", "school_document", "school_document_type", "parent_verified"
                  ]

        read_only_fields = ["status", "remark", "created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["document_type"] = ""
        if instance.document_type:
            representation["document_type"] = instance.document_type.title

        representation["athlete_type"] = ""
        if instance.athlete_type:
            representation["athlete_type"] = instance.athlete_type.title
        return representation

    def validate(self, attrs):
        dob = attrs.get("dob")
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        attrs["is_under"] = age < 18

        if attrs["is_under"]:
            if not attrs.get("parent_legal_name") or not attrs.get("parent_email") or not attrs.get(
                    "parent_phone_number"):
                raise serializers.ValidationError({
                    "parent_info": "Parent name, email, and phone number are required for users under 18."
                })

        user_type = self.context.get("user_type")
        if user_type == "player":
            if not attrs.get("athlete_type"):
                raise serializers.ValidationError({
                    "athlete_type": "This field is required."
                })

            if not attrs.get("document_type"):
                raise serializers.ValidationError({
                    "document_type": "This field is required."
                })

        school_document_type = attrs.get("school_document_type")
        if school_document_type:
            if not attrs.get("school_document"):
                raise serializers.ValidationError({
                    "school_document": "This field is required."
                })

        return attrs

    def validate_refer_by(self, value):
        if value:
            if not ReferralOrganization.objects.filter(name=value).exists():
                raise serializers.ValidationError(
                    "This referral organization does not exist. Please enter the correct name."
                )
        return value


class AthleteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteTypes
        fields = ["id", "title"]


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "title"]


class ResendParentConsent(serializers.Serializer):
    verification = serializers.PrimaryKeyRelatedField(
        queryset=IdentityVerification.objects.all()
    )
    parent_email = serializers.EmailField(required=False)
    parent_legal_name = serializers.CharField(required=False)
    parent_phone_number = serializers.CharField(max_length=15, required=False)


class ReferralOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralOrganization
        fields = ["id", "name"]


class SchoolDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolDocument
        fields = ["id", "name"]
