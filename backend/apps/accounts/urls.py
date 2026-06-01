"""
Authentication URL patterns.

Mounted at /api/v1/auth/ in config/api_urls.py.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ResetPasswordView,
    VerifyEmailView,
)

urlpatterns = [
    # ── Authentication ────────────────────────────
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    # ── Email ─────────────────────────────────────
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    # ── Password ──────────────────────────────────
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    # ── Profile ───────────────────────────────────
    path("me/", MeView.as_view(), name="auth-me"),
]
