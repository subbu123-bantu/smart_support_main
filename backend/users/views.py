from rest_framework import viewsets, status
from .models import User, AgentProfile
from .serializers import UserSerializer, RegisterSerializer, AgentProfileSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdmin
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "user": {
                "role": user.role.lower(),
                "username": user.username,
                "email": user.email,
                "access": str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"message": "Logged out successfully"})


class AgentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role.lower() != 'admin':
            raise PermissionDenied("Only admins can view agents.")

        profiles = AgentProfile.objects.select_related('user').prefetch_related('categories')
        serializer = AgentProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class AgentProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, agent_id):
        if request.user.role.lower() != 'admin':
            raise PermissionDenied("Only admins can update agents.")

        try:
            profile = AgentProfile.objects.select_related('user').prefetch_related('categories').get(user__id=agent_id)
        except AgentProfile.DoesNotExist:
            return Response({"error": f"No AgentProfile found for user id {agent_id}"}, status=404)

        serializer = AgentProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
