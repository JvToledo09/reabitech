# ==============================================================================
# REABITECH — APP MENSAGERIA
# AppsConfig: registra signals ao iniciar
# ==============================================================================

from django.apps import AppConfig


class MensageriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mensageria'
    verbose_name = 'Mensageria Interna'

    def ready(self):
        """Registra os signals automaticamente."""
        try:
            import mensageria.signals  # noqa: F401
        except Exception:
            pass
