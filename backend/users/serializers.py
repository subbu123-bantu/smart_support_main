from rest_framework import serializers
from tickets.models import Category

from .models import AgentProfile, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class AgentProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=False,
    )
    category_names = serializers.SlugRelatedField(
        source="categories",
        many=True,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = AgentProfile
        fields = ["id", "username", "is_available", "categories", "category_names"]

    def update(self, instance, validated_data):
        categories = validated_data.pop("categories", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        if categories is not None:
            instance.categories.set(categories)

        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
            role="customer",
            is_active=True,
        )
