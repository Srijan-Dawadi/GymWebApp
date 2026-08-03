from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """Health check endpoint for desktop app readiness polling."""

    def get(self, request):
        # Check database connectivity
        from django.db import connection
        try:
            connection.ensure_connection()
            db_status = 'ok'
        except Exception as e:
            db_status = f'error: {e}'

        # Check if ML models are loadable (optional, can be slow)
        ml_status = 'unknown'
        try:
            from face_service import _get_face_app
            face_app = _get_face_app()
            ml_status = 'ok' if face_app else 'unavailable'
        except Exception:
            ml_status = 'error'

        return JsonResponse({
            'status': 'healthy' if db_status == 'ok' else 'degraded',
            'database': db_status,
            'ml_models': ml_status,
            'version': '1.0.0',
        })


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
