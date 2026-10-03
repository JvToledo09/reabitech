from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        import usuarios.signals  # noqa
        from usuarios.signals import conectar_signals_automaticos
        conectar_signals_automaticos()