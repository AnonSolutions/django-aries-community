from django.apps import AppConfig


class AriesCommunityConfig(AppConfig):
    name = 'aries_community'

    def ready(self):
        import aries_community.signals
        print("App is ready!!!")
