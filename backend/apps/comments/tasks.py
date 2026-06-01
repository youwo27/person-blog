"""
Celery async tasks for comments — email notifications.

Triggers:
- New comment → notify post author
- Reply to comment → notify parent comment author
- Comment approved → notify comment author
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(name="comments.notify_post_author", max_retries=3, default_retry_delay=60)
def notify_post_author(comment_id: int):
    """
    Notify the post author when someone comments on their post.
    Skips if the commenter IS the post author.
    """
    from apps.comments.models import Comment

    try:
        comment = Comment.objects.select_related("post__author", "author").get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f"Comment {comment_id} not found for notify_post_author")
        return

    post = comment.post
    if comment.author_id == post.author_id:
        return  # Don't notify yourself

    post_url = f"{settings.SITE_URL}/posts/{post.slug}"
    subject = f"[{settings.SITE_NAME}] New comment on your post: {post.title}"
    message = (
        f"Hi {post.author.display_name},\n\n"
        f"{comment.author.display_name} commented on your post \"{post.title}\":\n\n"
        f"{comment.content[:300]}{'...' if len(comment.content) > 300 else ''}\n\n"
        f"View: {post_url}#comments\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=False,
        )
        logger.info(f"Post author notification sent to {post.author.email} for comment {comment_id}")
    except Exception as exc:
        logger.error(f"Failed to send post author notification: {exc}")
        raise


@shared_task(name="comments.notify_comment_reply", max_retries=3, default_retry_delay=60)
def notify_comment_reply(comment_id: int):
    """
    Notify the parent comment author when someone replies to their comment.
    """
    from apps.comments.models import Comment

    try:
        comment = Comment.objects.select_related("parent__author", "author", "post").get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f"Comment {comment_id} not found for notify_comment_reply")
        return

    if not comment.parent:
        return  # Not a reply

    if comment.author_id == comment.parent.author_id:
        return  # Don't notify yourself

    post_url = f"{settings.SITE_URL}/posts/{comment.post.slug}"
    subject = f"[{settings.SITE_NAME}] Reply to your comment on: {comment.post.title}"
    message = (
        f"Hi {comment.parent.author.display_name},\n\n"
        f"{comment.author.display_name} replied to your comment on \"{comment.post.title}\":\n\n"
        f"\"{comment.content[:300]}{'...' if len(comment.content) > 300 else ''}\"\n\n"
        f"View: {post_url}#comment-{comment_id}\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[comment.parent.author.email],
            fail_silently=False,
        )
        logger.info(f"Reply notification sent to {comment.parent.author.email} for comment {comment_id}")
    except Exception as exc:
        logger.error(f"Failed to send reply notification: {exc}")
        raise


@shared_task(name="comments.notify_comment_approved", max_retries=3, default_retry_delay=60)
def notify_comment_approved(comment_id: int):
    """
    Notify the comment author that their comment has been approved.
    """
    from apps.comments.models import Comment

    try:
        comment = Comment.objects.select_related("author", "post").get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f"Comment {comment_id} not found for notify_comment_approved")
        return

    post_url = f"{settings.SITE_URL}/posts/{comment.post.slug}"
    subject = f"[{settings.SITE_NAME}] Your comment has been approved"
    message = (
        f"Hi {comment.author.display_name},\n\n"
        f"Your comment on \"{comment.post.title}\" has been approved and is now visible:\n\n"
        f"\"{comment.content[:300]}{'...' if len(comment.content) > 300 else ''}\"\n\n"
        f"View: {post_url}#comment-{comment_id}\n\n"
        f"— {settings.SITE_NAME}"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[comment.author.email],
            fail_silently=False,
        )
        logger.info(f"Approval notification sent to {comment.author.email} for comment {comment_id}")
    except Exception as exc:
        logger.error(f"Failed to send approval notification: {exc}")
        raise
