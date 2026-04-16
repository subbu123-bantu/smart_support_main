from rest_framework import viewsets, status
from .models import User, AgentProfile
from .serializers import UserSerializer, RegisterSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdmin
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.http import require_GET, require_POST
from rest_framework.exceptions import PermissionDenied


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]


@require_POST
@authentication_classes([])
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
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


@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    return Response({"message": "Logged out successfully"})


@require_GET
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agents(request):
    if request.user.role.lower() != 'admin':
        raise PermissionDenied("Only admins can view agents.")

    profiles = AgentProfile.objects.select_related('user')

    result = []
    for profile in profiles:
        result.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'is_available': profile.is_available,
        })

    return Response(result)
