from django.apps import AppConfig

class AppFinanzasConfig(AppConfig):
    name = 'app_finanzas'

    def ready(self):
        import app_finanzas.signals
