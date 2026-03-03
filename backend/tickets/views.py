from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ticket,Category,TicketStatus
from .serializers import TicketSerializer,CategorySerializer,TicketStatusSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsAgent
from rest_framework.exceptions import PermissionDenied


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all() 
    serializer_class = CategorySerializer
    # permission_classes = [permissions.IsAuthenticated]

class TicketStatusViewSet(viewsets.ModelViewSet):
    queryset = TicketStatus.objects.all()
    serializer_class = TicketStatusSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return Ticket.objects.all()
        elif user.role == 'agent':
            return Ticket.objects.all()
        elif user.role == 'customer':
            return Ticket.objects.filter(customer=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != 'customer':
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save(customer=self.request.user)



    # def get_permissions(self):
    
    #     if self.action == "create":
    #         return [IsAuthenticated(), IsCustomer()]

    #     elif self.action in ["update", "partial_update"]:
    #         return [IsAuthenticated(), IsAgent()]

    #     elif self.action == "destroy":
    #         return [IsAuthenticated(), IsAdmin()]

    #     return [IsAuthenticated()]

    # def get_queryset(self):
    #     user = self.request.user

    #     if user.role == "CUSTOMER":
    #         return Ticket.objects.filter(customer=user)

    #     if user.role == "AGENT":
    #         return Ticket.objects.filter(assigned_to=user)

    #     return Ticket.objects.all()

    

    #DefaultFilters
    # {# filter_backend=[DjangoFilterBackend,SearchFilter]
    # filterset_fields=['status']
    # search_fields =['title','periority']
