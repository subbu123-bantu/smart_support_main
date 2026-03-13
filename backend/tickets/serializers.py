
# class TicketSerializer(serializers.ModelSerializer):
#     class Meta:
#         model =Ticket
#         fields='__all__'
#         read_only_fields=['customer']

from rest_framework import serializers
from .models import Ticket, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        return value
        