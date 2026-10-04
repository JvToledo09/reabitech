from django.apps import AppConfig


class ConsultasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consultas'
    verbose_name = 'Agenda de Consultas'

    def ready(self):
        # Registra signals (notificações automáticas)
        from . import signals  # noqa: F401