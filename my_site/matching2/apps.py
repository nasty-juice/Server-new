from django.apps import AppConfig


class Matching2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matching2'
    
    def ready(self):
        import matching2.signals
