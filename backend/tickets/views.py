from http import cookies
import traceback

from requests import request
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import JsonResponse, PermissionDenied
from django.db.models import Q, Count
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Ticket, Category, TicketPredictionLog
from .serializers import TicketSerializer, CategorySerializer
from users.permissions import IsAdmin
from users.pagination import CustomPagination
from .ai import predict_ticket
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
#CATEGORY
class test_backend(APIView):
    def list(self, request):
        return Response({"message": "Backend is working!"})

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]


# TICKETS 

class TicketViewSet(viewsets.ModelViewSet):
    # authentication_classes = [CookieJWTAuthentication]
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]  # ✅ add this
    filterset_fields = ['status', 'priority']              # ✅ add this
    search_fields = ['title', 'description']      

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.all()

        if not user.is_authenticated:
            return Ticket.objects.none()

        if user.role.lower() == "admin":
            # filter by assigned/unassigned if query param present
            assigned = self.request.query_params.get('assigned')
            if assigned == 'true':
                queryset = queryset.filter(assigned_to__isnull=False)
            elif assigned == 'false':
                queryset = queryset.filter(assigned_to__isnull=True)
            return queryset

        if user.role.lower() == "agent":
            return queryset.filter(assigned_to=user)

        if user.role.lower() == "customer":
            return queryset.filter(customer=user)

        return Ticket.objects.none()

    #CREATE

    def perform_create(self, serializer):
        if self.request.user.role.lower() != 'customer':
            raise PermissionDenied("Only customers can create tickets.")

        serializer.save(customer=self.request.user)
        print("REQUEST USER:", self.request.user)
        print("AUTH:", self.request.auth)
    #UPDATE

    def update(self, request, *args, **kwargs):
        ticket = self.get_object()
        user = request.user

        if user.role.lower() == 'customer':
            raise PermissionDenied("Customers cannot update tickets.")

        if user.role.lower() == 'agent' and ticket.assigned_to != user:
            raise PermissionDenied("You can only update your assigned tickets.")

        # Agent can only update status
        if user.role.lower() == 'agent':
            allowed_fields = {'status'}
            if not set(request.data.keys()).issubset(allowed_fields):
                raise PermissionDenied("Agents can only update ticket status.")

        return super().update(request, *args, **kwargs)  # ✅ call update, not partial_update


#STATS

@api_view(['GET'])

def ticket_stats(request):
    user = request.user
    try:
        if user.role.lower() == 'admin':
            queryset = Ticket.objects.all()
        elif user.role.lower()== 'agent':
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
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def assign_ticket(request, ticket_id):
    user = request.user
    if user.role.lower() != 'admin':
        raise PermissionDenied("Only admins can assign tickets.")

    ticket = Ticket.objects.get(id=ticket_id)
    agent_id = request.data.get("assigned_to")

    if agent_id:
        from users.models import User
        agent = User.objects.get(id=agent_id)
        ticket.assigned_to = agent
    else:
        ticket.assigned_to = None  # unassign

    ticket.save()
    return Response({"message": "Ticket assigned", "assigned_to": str(ticket.assigned_to)})


# PREDICT API

@api_view(['POST'])

def predict_ticket_api(request):
    text = request.data.get("text", "")

    if not text:
        return Response({"error": "No text provided"}, status=400)

    result = predict_ticket(text)
    return Response(result)




































# @api_view(["POST"])

# def update_prediction_feedback(request, ticket_id):
#     is_correct = request.data.get("is_correct")

#     log = TicketPredictionLog.objects.filter(ticket_id=ticket_id).last()

#     if not log:
#         return Response({"error": "Log not found"}, status=404)

#     log.final_accepted = is_correct
#     log.save()

#     return Response({"message": "Feedback saved"})

# @api_view(["GET"])

# def prediction_accuracy(request):
#     from tickets.models import TicketPredictionLog

#     total = TicketPredictionLog.objects.count()
#     correct = TicketPredictionLog.objects.filter(final_accepted=True).count()

#     accuracy = (correct / total) * 100 if total > 0 else 0

#     return Response({
#         "total": total,
#         "correct": correct,
#         "accuracy": accuracy
#     })

# @api_view(["GET"])

# def check_assignments(request):
#     tickets = Ticket.objects.all().values(
#         "id",
#         "title",
#         "category__name",
#         "assigned_to__username"
#     )
#     return Response(list(tickets))