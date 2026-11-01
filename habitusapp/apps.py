from django.apps import AppConfig


class HabitusappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'habitusapp'

    def ready(self):
        import habitusapp.signals  # noqa
