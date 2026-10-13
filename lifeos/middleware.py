from django.utils import timezone

from .models import VisionConfig


class VisionTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(VisionConfig.get_solo().timezone_name)
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
