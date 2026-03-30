from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Ticket, Category
from .serializers import TicketSerializer, CategorySerializer
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ai import predict_ticket


# CATEGORY #

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# TICKETS #

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        # Base queryset based on role
        if user.role == 'admin':
            queryset = Ticket.objects.all()

        elif user.role == 'agent':
            queryset = Ticket.objects.filter(assigned_to__user=user)

        else:  # customer
            queryset = Ticket.objects.filter(customer=user)

        # Apply filters (NOW this actually works)
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        search = self.request.query_params.get('search')

        if status:
            queryset = queryset.filter(status__iexact=status)

        if priority and priority.lower() != "all":
            queryset = queryset.filter(priority__iexact=priority)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset


    def perform_create(self, serializer):
        user = self.request.user

        if user.role != 'customer':
            raise PermissionDenied("Only customers can create tickets.")

        ticket = serializer.save(customer=user)

        text = f"{ticket.title or ''} {ticket.description or ''}"
        result = predict_ticket(text)

        ticket.category = result["category"]
        ticket.priority = result["priority"]
        ticket.predicted_category = result["category"]
        ticket.predicted_priority = result["priority"]

        ticket.save()


    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user

        if user.role == 'customer':
            raise PermissionDenied("Customers cannot update tickets.")

        # FIX: correct comparison
        if user.role == 'agent' and ticket.assigned_to.user != user:
            raise PermissionDenied("You can only update your assigned tickets.")

        return super().update(request, *args, **kwargs)
    



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_stats(request):
    user = request.user

    # Correct role-based filtering
    if user.role == 'admin':
        queryset = Ticket.objects.all()

    elif user.role == 'agent':
        queryset = Ticket.objects.filter(assigned_to__user=user)

    else:
        queryset = Ticket.objects.filter(customer=user)

    stats = queryset.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        closed=Count('id', filter=Q(status='closed')),
    )

    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_ticket_api(request):
    text = request.data.get("text", "")

    if not text:
        return Response({"error": "No text provided"}, status=400)

    result = predict_ticket(text)
    return Response(result)