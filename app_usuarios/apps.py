from django.apps import AppConfig

class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_usuarios'

    def ready(self):
        import app_usuarios.models  # This imports the signals
