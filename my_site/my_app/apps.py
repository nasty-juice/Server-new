from django.apps import AppConfig


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_app'

    def ready(self):
        # 신호를 등록
        import my_app.signals