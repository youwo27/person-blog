"""
Authentication & user management views.

Endpoints:
- POST /api/v1/auth/register/          Register new user
- POST /api/v1/auth/login/             Login → JWT tokens
- POST /api/v1/auth/logout/            Logout → blacklist token
- POST /api/v1/auth/refresh/           Refresh access token
- POST /api/v1/auth/verify-email/      Verify email address
- POST /api/v1/auth/forgot-password/   Send reset email
- POST /api/v1/auth/reset-password/    Reset password
- GET  /api/v1/auth/me/                Current user profile
- PATCH /api/v1/auth/me/               Update profile
- PATCH /api/v1/auth/change-password/  Change password
"""

import uuid

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

from common.throttling import LoginRateThrottle, RegisterRateThrottle

from .models import Subscriber, User
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SubscriberCreateSerializer,
    SubscriberSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
)
from .tasks import send_password_reset_email, send_verification_email, send_welcome_email
from .utils import generate_password_reset_token, generate_verification_token


# ═══════════════════════════════════════════════════
# Register
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Register new user",
    description="Create a new account. Triggers email verification.",
    request=RegisterSerializer,
    responses={201: None, 400: None},
    tags=["auth"],
)
class RegisterView(APIView):
    """Register a new user account."""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        # Generate verification token
        user.email_verification_token = generate_verification_token()
        user.save(update_fields=["email_verification_token"])

        # Send verification email asynchronously
        try:
            send_verification_email.delay(user.id)
        except Exception:
            # If Celery is not running, don't fail the registration
            pass

        return Response(
            {
                "success": True,
                "message": "Registration successful. Please check your email to verify your account.",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════
# Login
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Login",
    description="Authenticate and receive JWT access + refresh tokens.",
    tags=["auth"],
)
class LoginView(BaseTokenObtainPairView):
    """
    Login — extends simplejwt's TokenObtainPairView.

    Uses CustomTokenObtainPairSerializer for:
    - Account lockout checking
    - Failed login tracking
    - Custom token claims (role, email_verified, display_name)
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            data = serializer.validate(serializer.initial_data)
            return Response({"success": True, **data})
        except Exception as exc:
            return Response(
                {"success": False, "error": {"code": "authentication_failed", "message": str(exc)}},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ═══════════════════════════════════════════════════
# Logout
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Logout",
    description="Blacklist the refresh token so it can no longer be used.",
    tags=["auth"],
)
class LogoutView(APIView):
    """Logout — blacklist the provided refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response({"success": True, "message": "Logged out successfully."})
        except TokenError:
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": "Invalid or expired token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )




# ═══════════════════════════════════════════════════
# Email Verification
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Verify email",
    description="Verify an email address using the token sent after registration.",
    tags=["auth"],
)
class VerifyEmailView(APIView):
    """Verify email address with the verification token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.context["verify_user"]

        # Skip if already verified
        if user.email_verified:
            return Response({"success": True, "message": "Email already verified."})

        user.email_verified = True
        user.email_verification_token = ""
        user.save(update_fields=["email_verified", "email_verification_token"])

        # Send welcome email
        try:
            send_welcome_email.delay(user.id)
        except Exception:
            pass

        return Response({"success": True, "message": "Email verified successfully! You can now log in."})


# ═══════════════════════════════════════════════════
# Password Reset (Forgot / Reset)
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Request password reset",
    description="Send a password reset email to the given address.",
    tags=["auth"],
)
class ForgotPasswordView(APIView):
    """Send password reset email."""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data.get("email", "")

        # Always return success to prevent email enumeration
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            user = User.objects.get(email__iexact=email)
            reset_token = generate_password_reset_token(user.id)
            try:
                send_password_reset_email.delay(user.id, reset_token)
            except Exception:
                pass

        return Response({
            "success": True,
            "message": "If the email is registered, a password reset link has been sent.",
        })


@extend_schema(
    summary="Reset password",
    description="Reset password using the token from the reset email.",
    tags=["auth"],
)
class ResetPasswordView(APIView):
    """Reset password with a time-limited reset token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.context["reset_user"]
        user.set_password(serializer.validated_data["new_password"])
        user.login_attempts = 0
        user.locked_until = None
        user.save()

        return Response({"success": True, "message": "Password reset successfully. You can now log in."})


# ═══════════════════════════════════════════════════
# Profile (Me)
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Get profile",
    description="Return the current user's profile.",
    tags=["auth"],
)
class MeView(APIView):
    """Read / update current user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        summary="Update profile",
        description="Update the current user's profile fields.",
        request=UserUpdateSerializer,
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        # Return full profile after update
        profile_serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response({"success": True, "data": profile_serializer.data})


# ═══════════════════════════════════════════════════
# Change Password
# ═══════════════════════════════════════════════════


@extend_schema(
    summary="Change password",
    description="Change the current user's password. Requires old password.",
    tags=["auth"],
)
class ChangePasswordView(APIView):
    """Change password — requires old password for verification."""

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"success": True, "message": "Password changed successfully."})


# ═══════════════════════════════════════════════════
# Subscriber ViewSet (kept from Round 2)
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List subscribers", description="List newsletter subscribers. Admin only.", tags=["subscribers"]),
    create=extend_schema(summary="Subscribe", description="Subscribe to the newsletter.", tags=["subscribers"]),
    destroy=extend_schema(summary="Unsubscribe", description="Remove a subscriber. Admin only.", tags=["subscribers"]),
)
class SubscriberViewSet(viewsets.ModelViewSet):
    """
    Newsletter subscriber management.
    - List/Destroy: Admin only
    - Create: Public
    """

    queryset = Subscriber.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return SubscriberCreateSerializer
        return SubscriberSerializer

    def get_permissions(self):
        if self.action in ("list", "destroy", "update", "partial_update"):
            return [IsAdminUser()]
        return []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=400,
            )
        subscriber = serializer.save()
        return Response(
            {"success": True, "message": "Successfully subscribed.", "data": SubscriberSerializer(subscriber).data},
            status=201,
        )
