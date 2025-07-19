from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SummaryHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class SummarySerializer(serializers.Serializer):
    input_text = serializers.CharField(max_length=3072)

class SummaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryHistory
        fields = ['id', 'input_text', 'summary_text', 'created_at']