from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        """Warm the InsightFace model and anti-spoof session in a background
        thread so the first attendance scan isn't slow.
        Only runs in the main server process (skipped during migrations etc.).
        """
        import os
        # Avoid warming during management commands like migrate, shell, etc.
        # RUN_MAIN is set by Django's auto-reloader for the main worker process.
        if os.environ.get('RUN_MAIN') != 'true':
            return

        import threading

        def _warm():
            try:
                import logging
                logger = logging.getLogger(__name__)
                from face_service import _get_face_app, _get_spoof_session
                logger.info('Warming InsightFace model...')
                _get_face_app()
                _get_spoof_session()
                logger.info('Face recognition models ready.')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    'Model warm-up failed (non-fatal): %s', e
                )

        t = threading.Thread(target=_warm, daemon=True, name='face-model-warmup')
        t.start()
