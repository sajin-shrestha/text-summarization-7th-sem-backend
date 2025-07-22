from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SummaryHistory, UserProfile

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # UserProfile is created automatically by signal
        return user

class SummarySerializer(serializers.Serializer):
    input_text = serializers.CharField(max_length=3072)

class SummaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryHistory
        fields = ['id', 'input_text', 'summary_text', 'created_at']