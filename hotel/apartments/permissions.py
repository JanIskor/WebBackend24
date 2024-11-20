from rest_framework import permissions, authentication, exceptions
from django.contrib.auth.models import User
from django.conf import settings
# import redis

# # Connect to our Redis instance
# session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

# class AuthBySessionID(authentication.BaseAuthentication):
#     def authenticate(self, request):
#         session_id = request.COOKIES.get("session_id")
#         if session_id is None:
#             raise exceptions.AuthenticationFailed("Нужно авторизоваться")
#         try:
#             username = session_storage.get(session_id).decode("utf-8")
#         except Exception as e:
#             raise exceptions.AuthenticationFailed("session_id not found")
#         user = User.objects.filter(username=username).first()
#         if user is None:
#             raise exceptions.AuthenticationFailed("No such user")
#         #request.user = user
#         return user, None