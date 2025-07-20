"""
core/apps.py
------------
AppConfig for the core app.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Run when the app is ready.
        Import signals and other initialization code here.
        Avoid database queries during app initialization.
        """
        # Import signals to ensure they are registered
        try:
            import core.signals
        except ImportError:
            pass

        # Note: Site configuration moved to management command
        # to avoid database access during app initialization

        # إضافة استيراد الإشارة الخاصة بإنشاء Owner تلقائيًا
        from . import signals_owner
