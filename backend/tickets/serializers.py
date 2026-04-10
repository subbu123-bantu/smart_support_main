from rest_framework import serializers
from .models import TicketComment

from tickets.services.ticketcreate import create_ticket
from .ai import log_prediction, predict_ticket
from .services.assignment import assign_ticket_to_agent
from .models import Ticket, Category, TicketPredictionLog

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Ticket
        fields = ["id","title","description", "status","priority","category","category_name","assigned_to","customer","user_ticket_id","assigned_to_name","customer_name", ]
        read_only_fields = ["customer", "user_ticket_id"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        return value

    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user:
            raise serializers.ValidationError("User not found")

        return create_ticket(validated_data, request.user)
    
    def update(self, instance, validated_data):
        if "category" in validated_data:
            instance.category = validated_data["category"]

        if "priority" in validated_data:
            instance.priority = validated_data["priority"]

        if "status" in validated_data:
            instance.status = validated_data["status"]

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            if request.user.role == "customer":
                data.pop("id", None)

        return data
    

class TicketCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "ticket",
            "user",
            "username",
            "user_role",
            "message",
            "is_internal",
            "created_at",
        ]
        read_only_fields = ["user", "ticket", "username", "user_role", "created_at"]