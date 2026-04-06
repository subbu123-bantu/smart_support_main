from rest_framework import serializers

from .services.ticketservices import create_ticket
from .ai import log_prediction, predict_ticket
from .services.assignment import assign_ticket
from .models import Ticket, Category, TicketPredictionLog

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    category = serializers.StringRelatedField()
    class Meta:
        model = Ticket
        fields = '__all__'
<<<<<<< HEAD
    category = serializers.StringRelatedField() 
    class Meta:
        model = Ticket
        fields = "__all__"
=======
>>>>>>> 815f769 (working on sending a mail to user)
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
<<<<<<< HEAD
    
=======

>>>>>>> 815f769 (working on sending a mail to user)
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

<<<<<<< HEAD
        # Hide ID from customers, show ID to admin/agent
        if request and hasattr(request, "user"):
            user = request.user
            if user.role == "customer":
=======
        if request and request.user.is_authenticated:
            if request.user.role == "customer":
>>>>>>> 815f769 (working on sending a mail to user)
                data.pop("id", None)

        return data