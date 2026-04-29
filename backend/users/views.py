import logging
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from .models import AgentProfile
from .serializers import (
    RegisterSerializer,
    AgentProfileSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangeEmailSerializer,
)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from tickets.tasks import send_email_task

UserModel = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ["post"]

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
    http_method_names = ["post"]

    def post(self, request):
        return Response({"message": "Logged out successfully"})


class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserModel.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
            try:
                send_email_task.delay(
                    user.email,
                    "Reset your Smart Support password",
                    template_name="emails/password_reset.html",
                    context={
                        "username": user.username,
                        "reset_url": reset_url,
                    },
                )
            except Exception:
                logger.exception("Failed to queue password reset email for user_id=%s", user.id)

        return Response(
            {"message": "A reset link has been sent to your registered mail."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["post"]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    def patch(self, request):
        serializer = ChangeEmailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.email = serializer.validated_data["email"]
        request.user.save(update_fields=["email"])

        return Response(
            {
                "message": "Email updated successfully.",
                "email": request.user.email,
            },
            status=status.HTTP_200_OK,
        )


class AgentListView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def get(self, request):
        if request.user.role.lower() != 'admin':
            raise PermissionDenied("Only admins can view agents.")

        profiles = AgentProfile.objects.select_related('user').prefetch_related('categories')
        serializer = AgentProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class AgentProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

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
