from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .services.assignment import assign_ticket
from .models import Ticket, Category
from .serializers import TicketSerializer, CategorySerializer
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ai import predict_ticket
from users.models import User
from django.http import HttpResponse    


# CATEGORY VIEWSET


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]

# TICKET VIEWSET

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # GET QUERYSET (ROLE BASED)
    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            queryset = Ticket.objects.all()

        elif user.role == 'agent':
            # FIX: correct relation
            queryset = Ticket.objects.filter(assigned_to=user)

        else:  # customer
            queryset = Ticket.objects.filter(customer=user)

        # Filters
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        search = self.request.query_params.get('search')

        if status:
            queryset = queryset.filter(status__iexact=status)

        if priority and priority.lower() != "all":
            queryset = queryset.filter(priority__iexact=priority)

        if search:
            vector = SearchVector('title', 'description', 'category__name')
            search_query = SearchQuery(search)

            queryset = queryset.annotate(
                search=vector,
                rank=SearchRank(vector, search_query)
            ).filter(
                search=search_query
            ).order_by('-rank')

    # CREATE TICKET
    def perform_create(self, serializer):
        user = self.request.user

        if user.role != 'customer':
            raise PermissionDenied("Only customers can create tickets.")

        with transaction.atomic():
            ticket = serializer.save(customer=user)

            # AI Prediction
            text = f"{ticket.title or ''} {ticket.description or ''}"
            result = predict_ticket(text)

            # FIX: map category string → Category object
            category = Category.objects.filter(name=result["category"]).first()

            if not category:
                # fallback category (ensure "others" exists in DB)
                category = Category.objects.filter(name="others").first()

            if category:
                ticket.category = category

            ticket.priority = result["priority"]
            ticket.predicted_category = result["category"]
            ticket.predicted_priority = result["priority"]

            ticket.save(update_fields=[
                "category",
                "priority",
                "predicted_category",
                "predicted_priority"
            ])

            # Assignment
            assigned_agent = assign_ticket(ticket)

            # Fallback assignment (IMPORTANT)
            if not assigned_agent:
                admin = User.objects.filter(role='admin').first()
                if admin:
                    ticket.assigned_to = admin
                    ticket.save(update_fields=["assigned_to"])

    # UPDATE TICKET
   
    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user

        if user.role == 'customer':
            raise PermissionDenied("Customers cannot update tickets.")

        # FIX: correct comparison
        if user.role == 'agent' and ticket.assigned_to != user:
            raise PermissionDenied("You can only update your assigned tickets.")

        return super().update(request, *args, **kwargs)

# TICKET STATS API

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_stats(request):
    user = request.user

    if user.role == 'admin':
        queryset = Ticket.objects.all()

    elif user.role == 'agent':
        queryset = Ticket.objects.filter(assigned_to=user)

    else:
        queryset = Ticket.objects.filter(customer=user)

    stats = queryset.aggregate(
        total=Count('id'),
        open=Count('id', filter=Q(status='open')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        closed=Count('id', filter=Q(status='closed')),
    )

    return Response(stats)

# AI PREDICTION API

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_ticket_api(request):
    text = request.data.get("text", "")

    if not text:
        return Response({"error": "No text provided"}, status=400)

    result = predict_ticket(text)
    return Response(result)

def test_backend(request):
    return HttpResponse("Backend is working!")