from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django.db.models import Count

from .models import Ticket, Category
from .serializers import TicketSerializer, CategorySerializer
from .filters import TicketFilter
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ml.predict import predict_ticket

#CATEGORY

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


#TICKETS

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # Optional (you can keep or remove later)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'description', 'status']
    filterset_class = TicketFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.all()

        #DEBUG
        print("QUERY PARAMS:", self.request.query_params)

        #STATUS FILTER
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status__iexact=status)

        #PRIORITY FILTER
        priority = self.request.query_params.get('priority')
        if priority and priority != "all":
            queryset = queryset.filter(priority__iexact=priority)

        #SEARCH FILTER
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # ROLE-BASED FILTER
        if user.role == 'customer':
            queryset = queryset.filter(customer=user)

        return queryset

    # Only customers can create tickets
    def perform_create(self, serializer):
        if self.request.user.role != 'customer':
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save(customer=self.request.user)

    # Update control
    def update(self, request, *args, **kwargs):
        ticket = self.get_object()

        if request.user.role == 'customer':
            raise PermissionDenied("Customers cannot update tickets.")

        if request.user.role == 'agent' and ticket.assigned_to != request.user:
            raise PermissionDenied("You can only update assigned tickets.")

        return super().update(request, *args, **kwargs)


# DASHBOARD STATS

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_stats(request):
    user = request.user

    if user.role in ['admin', 'agent']:
        queryset = Ticket.objects.all()
    else:
        queryset = Ticket.objects.filter(customer=user)

    stats = queryset.values('status').annotate(count=Count('status'))

    print(f"User: {user.username}, Role: {user.role}")
    print(f"Queryset count: {queryset.count()}")
    print(f"Stats: {list(stats)}")

    data = {
        "open": 0,
        "in_progress": 0,
        "closed": 0
    }

    for item in stats:
        data[item["status"]] = item["count"]

    data["total"] = queryset.count()

    return Response(data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_ticket_api(request):
    text = request.data.get("text", "")
    if not text:
        return Response({"error": "No text provided"}, status=400)

    try:
        prediction = predict_ticket(text)
        return Response(prediction)
    except Exception as e:
        print(f"Prediction error: {e}")
        return Response({"error": "Prediction failed", "details": str(e)}, status=500)