from rest_framework.permissions import BasePermission
from django.conf import settings

class IsMainServer(BasePermission):

    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key')
        expected_key = getattr(settings, 'MAIN_SERVER_API_KEY', None)
        return api_key == expected_key and expected_key is not None