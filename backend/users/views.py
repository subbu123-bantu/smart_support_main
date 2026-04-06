from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from .permissions import IsAdmin,IsAgent,IsCustomer
from .pagination import CustomPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import  PermissionDenied
from .models import AgentProfile

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes=[IsAdmin]

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role.lower()  
    })

    response.set_cookie(key="access", value=str(refresh.access_token), httponly=True, secure=False, samesite='Lax', max_age=3000)
    response.set_cookie(key="refresh", value=str(refresh), httponly=True, secure=False, samesite='Lax', max_age=86400)

    return response

   
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    response = Response({"message": "Logged out successfully"})
    response.delete_cookie("access")
    response.delete_cookie("refresh")
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agents(request):
    if request.user.role.lower() != 'admin':
        raise PermissionDenied("Only admins can view agents.")
    
    profiles = AgentProfile.objects.select_related('user').prefetch_related('categories')
    
    result = []
    for profile in profiles:
        result.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'is_available': profile.is_available,
            'categories': [cat.name for cat in profile.categories.all()]
        })
    
    return Response(result)
