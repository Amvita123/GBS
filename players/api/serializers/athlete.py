from rest_framework import serializers
from players.models import SchoolGrade


class SchoolGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolGrade
        fields = ("id", "name", )


