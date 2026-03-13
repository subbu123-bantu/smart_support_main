from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ticket,Category
from .serializers import TicketSerializer,CategorySerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin, IsAgent
from rest_framework.exceptions import PermissionDenied
from users.pagination import CustomPagination
from rest_framework.decorators import api_view
from users.filters import TicketFilter


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all() 
    serializer_class = CategorySerializer
    # permission_classes = [permissions.IsAuthenticated]

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description']
    filterset_class = TicketFilter

    def get_queryset(self):
        user = self.request.user

        if user.role in ['admin', 'agent']:
            return Ticket.objects.all()

        if user.role == 'customer':
            return Ticket.objects.filter(customer=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != 'customer':
            raise PermissionDenied("Only customers can create tickets.")
        serializer.save(customer=self.request.user)

    def update(self, request, *args, **kwargs):

        ticket = self.get_object()

        if request.user.role == 'customer':
            raise PermissionDenied("Customers cannot update ticket status")

        return super().update(request, *args, **kwargs)

@api_view(['GET'])
def ticket_stats(request):

    stats = Ticket.objects.values('status').annotate(count=Count('status'))

    data = {
        "open": 0,
        "in_progress": 0,
        "closed": 0
    }

    for item in stats:
        data[item["status"]] = item["count"]

    data["total"] = Ticket.objects.count()

    return Response(data)
