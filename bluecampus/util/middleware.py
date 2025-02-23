import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f'Request received: {request.method} {request.path}')
        response = self.get_response(request)
        logger.info(f'Response sent: {response.status_code}')
        return response
    


class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_host() == 'demo.bluecampus.ng':
            settings.DEBUG = True
        else:
            settings.DEBUG = False

        response = self.get_response(request)
        return response