from django.apps import AppConfig


class MatchingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matching'
    
    def ready(self):
        import matching.signals  # 신호를 가져옵니다.