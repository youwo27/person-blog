"""
Celery async tasks for accounts app.

Tasks:
- send_verification_email: Send email verification link after registration
- send_password_reset_email: Send password reset link
- send_welcome_email: Send welcome email after email verification
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.models import User

logger = logging.getLogger(__name__)


@shared_task(name="accounts.send_verification_email", max_retries=3, default_retry_delay=60)
def send_verification_email(user_id: int):
    """
    Send email verification link to the user.

    The verification link points to the frontend which then calls the API.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"send_verification_email: User {user_id} not found")
        return

    if not user.email_verification_token:
        user.email_verification_token = uuid.uuid4().hex
        user.save(update_fields=["email_verification_token"])

    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.email_verification_token}"
    subject = f"[{settings.SITE_NAME}] Verify your email address"
    message = (
        f"Hi {user.display_name},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verification_url}\n\n"
        f"If you did not create this account, please ignore this email.\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {user.email}")
    except Exception as exc:
        logger.error(f"Failed to send verification email to {user.email}: {exc}")
        raise


@shared_task(name="accounts.send_password_reset_email", max_retries=3, default_retry_delay=60)
def send_password_reset_email(user_id: int, reset_token: str):
    """
    Send password reset link to the user.

    The reset link points to the frontend which then calls the API.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"send_password_reset_email: User {user_id} not found")
        return

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = f"[{settings.SITE_NAME}] Reset your password"
    message = (
        f"Hi {user.display_name},\n\n"
        f"You requested a password reset. Click the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {user.email}: {exc}")
        raise


@shared_task(name="accounts.send_welcome_email", max_retries=2, default_retry_delay=120)
def send_welcome_email(user_id: int):
    """Send welcome email after email verification."""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(f"send_welcome_email: User {user_id} not found")
        return

    subject = f"Welcome to {settings.SITE_NAME}!"
    message = (
        f"Hi {user.display_name},\n\n"
        f"Your email has been verified. Welcome to {settings.SITE_NAME}!\n\n"
        f"You can now log in and start contributing.\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {user.email}: {exc}")
        raise


# Needed for uuid in send_verification_email
import uuid
