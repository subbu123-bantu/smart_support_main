from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Try cookie first
        raw_token = request.COOKIES.get("access")
        
        # Fall back to Authorization header
        if raw_token is None:
            header = request.headers.get("Authorization", "")
            if header.startswith("Bearer "):
                raw_token = header.split(" ")[1]

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")