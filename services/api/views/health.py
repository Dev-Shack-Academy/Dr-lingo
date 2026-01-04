from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAdmin


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify the API is running.

    Returns:
        200 OK with a ping response
    """
    return Response({"status": "ok", "message": "pong"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_config(request):
    """
    Get current AI configuration for frontend defaults.

    Returns:
        AI provider settings including models for translation, completion, and embeddings.
    """
    ai_provider = getattr(settings, "AI_PROVIDER", "ollama")

    config = {
        "ai_provider": ai_provider,
    }

    if ai_provider == "ollama":
        config.update(
            {
                "translation_model": getattr(settings, "OLLAMA_TRANSLATION_MODEL", "granite:latest"),
                "completion_model": getattr(settings, "OLLAMA_COMPLETION_MODEL", "granite3.3:8b"),
                "embedding_model": getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5"),
                "embedding_provider": "ollama",
                "ollama_base_url": getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            }
        )
    elif ai_provider == "gemini":
        config.update(
            {
                "translation_model": getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"),
                "completion_model": getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"),
                "embedding_model": getattr(settings, "GEMINI_EMBEDDING_MODEL", "text-embedding-004"),
                "embedding_provider": "gemini",
            }
        )

    # Common defaults
    config.update(
        {
            "embedding_dimensions": 768,
            "chunking_strategy": "fixed-length",
            "chunk_length": 1000,
            "chunk_overlap": 200,
        }
    )

    return Response(config, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdmin])
def task_status(request, task_id):
    """
    Check the status of a Celery task.

    Args:
        task_id: The Celery task ID

    Returns:
        Task status and result if available
    """
    celery_enabled = getattr(settings, "CELERY_BROKER_URL", None) is not None

    if not celery_enabled:
        return Response(
            {"error": "Celery is not configured"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        from celery.result import AsyncResult

        result = AsyncResult(task_id)

        response_data = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }

        if result.ready():
            if result.successful():
                response_data["result"] = result.result
            else:
                response_data["error"] = str(result.result)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdmin])
def celery_status(request):
    """
    Check if Celery is available and workers are running.

    Returns:
        Celery status information
    """
    celery_enabled = getattr(settings, "CELERY_BROKER_URL", None) is not None

    if not celery_enabled:
        return Response(
            {
                "celery_enabled": False,
                "message": "Celery is not configured. Background tasks will run synchronously.",
            },
            status=status.HTTP_200_OK,
        )

    try:
        from config.celery import app

        # Try to ping workers
        inspect = app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            worker_count = len(active_workers)
            worker_names = list(active_workers.keys())
        else:
            worker_count = 0
            worker_names = []

        return Response(
            {
                "celery_enabled": True,
                "workers_available": worker_count > 0,
                "worker_count": worker_count,
                "worker_names": worker_names,
                "broker_url": settings.CELERY_BROKER_URL.split("@")[-1] if settings.CELERY_BROKER_URL else None,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "celery_enabled": True,
                "workers_available": False,
                "error": str(e),
                "message": "Celery is configured but workers may not be running",
            },
            status=status.HTTP_200_OK,
        )
