
# class TicketSerializer(serializers.ModelSerializer):
#     class Meta:
#         model =Ticket
#         fields='__all__'
#         read_only_fields=['customer']

from rest_framework import serializers
from .models import Ticket, Category, TicketStatus

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatus
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Ticket
        fields = '__all__'
        