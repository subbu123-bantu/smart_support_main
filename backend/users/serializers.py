from rest_framework import serializers

from tickets.models import Category
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User not found")

        validated_data["customer"] = request.user

        # 🔥 FIX CATEGORY HERE
        category_name = validated_data.get("predicted_category")

        if category_name:
            category_obj, _ = Category.objects.get_or_create(name=category_name)
            validated_data["category"] = category_obj

        return super().create(validated_data)

class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🔥 ADD ROLE INTO TOKEN
        token['role'] = user.role

        return token