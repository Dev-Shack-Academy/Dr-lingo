import logging
import os
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(queue="maintenance")
def cleanup_old_audio_files(days_old: int = 30):
    """
    Delete audio files older than specified days.

    This task:
    1. Finds audio files older than threshold
    2. Deletes files from storage
    3. Updates database records
    4. Logs cleanup statistics

    Args:
        days_old: Delete files older than this many days

    Returns:
        dict with cleanup statistics
    """
    from api.models import ChatMessage

    logger.info(f"Starting audio cleanup for files older than {days_old} days")

    threshold = timezone.now() - timedelta(days=days_old)

    # Find messages with audio files older than threshold
    old_messages = ChatMessage.objects.filter(
        has_audio=True,
        audio_file__isnull=False,
        created_at__lt=threshold,
    )

    deleted_count = 0
    failed_count = 0
    bytes_freed = 0

    for message in old_messages:
        try:
            if message.audio_file:
                # Get file size before deletion
                try:
                    file_size = message.audio_file.size
                    bytes_freed += file_size
                except Exception:
                    pass

                # Delete the file
                message.audio_file.delete(save=False)
                message.audio_file = None
                message.save()
                deleted_count += 1

        except Exception as e:
            logger.error(f"Failed to delete audio for message {message.id}: {e}")
            failed_count += 1

    logger.info(
        f"Audio cleanup complete: {deleted_count} deleted, "
        f"{failed_count} failed, {bytes_freed / 1024 / 1024:.2f} MB freed"
    )

    return {
        "status": "success",
        "deleted": deleted_count,
        "failed": failed_count,
        "bytes_freed": bytes_freed,
    }


@shared_task(queue="maintenance")
def cleanup_expired_cache():
    """
    Clear expired cache entries.

    Note: Redis handles TTL automatically, but this can be used
    for manual cleanup or cache warming.
    """

    logger.info("Starting cache cleanup")

    # Redis handles expiration automatically
    # This task can be used for:
    # 1. Clearing specific cache patterns
    # 2. Cache statistics logging
    # 3. Cache warming for frequently accessed data

    try:
        # Get cache statistics if available
        # This depends on your cache backend

        return {
            "status": "success",
            "message": "Cache cleanup completed",
        }

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(queue="maintenance")
def cleanup_orphaned_files():
    """
    Find and remove orphaned media files.

    Files that exist on disk but have no database reference.
    """
    from api.models import ChatMessage

    logger.info("Starting orphaned file cleanup")

    media_root = settings.MEDIA_ROOT
    audio_dir = os.path.join(media_root, "chat_audio")

    if not os.path.exists(audio_dir):
        return {"status": "success", "message": "No audio directory"}

    # Get all files in audio directory
    disk_files = set()
    for filename in os.listdir(audio_dir):
        disk_files.add(filename)

    # Get all referenced files from database
    db_files = set()
    for message in ChatMessage.objects.filter(audio_file__isnull=False):
        if message.audio_file:
            db_files.add(os.path.basename(message.audio_file.name))

    # Find orphaned files
    orphaned = disk_files - db_files

    deleted_count = 0
    for filename in orphaned:
        try:
            filepath = os.path.join(audio_dir, filename)
            os.remove(filepath)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete orphaned file {filename}: {e}")

    logger.info(f"Orphaned file cleanup: {deleted_count} files deleted")

    return {
        "status": "success",
        "orphaned_found": len(orphaned),
        "deleted": deleted_count,
    }


@shared_task(queue="maintenance")
def database_maintenance():
    """
    Perform database maintenance tasks.

    - Vacuum/analyze for PostgreSQL
    - Update statistics
    - Check for issues
    """
    from django.db import connection

    logger.info("Starting database maintenance")

    try:
        with connection.cursor() as cursor:
            # For PostgreSQL
            if connection.vendor == "postgresql":
                # Analyze tables for query optimization
                cursor.execute("ANALYZE;")
                logger.info("PostgreSQL ANALYZE completed")

        return {"status": "success", "message": "Database maintenance completed"}

    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(queue="maintenance")
def generate_usage_report():
    """
    Generate daily usage statistics report.
    """
    from django.db.models import Count
    from django.db.models.functions import TruncDate

    from api.models import ChatMessage, ChatRoom

    logger.info("Generating usage report")

    today = timezone.now().date()

    # Messages per day (last 7 days)
    messages_by_day = (
        ChatMessage.objects.filter(created_at__date__gte=today - timedelta(days=7))
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Active rooms
    active_rooms = ChatRoom.objects.filter(messages__created_at__date=today).distinct().count()

    # Audio messages today
    audio_messages = ChatMessage.objects.filter(
        created_at__date=today,
        has_audio=True,
    ).count()

    report = {
        "date": today.isoformat(),
        "messages_by_day": list(messages_by_day),
        "active_rooms_today": active_rooms,
        "audio_messages_today": audio_messages,
    }

    logger.info(f"Usage report: {report}")

    return report
