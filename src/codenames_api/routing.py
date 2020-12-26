# https://channels.readthedocs.io/en/latest/installation.html
# https://gist.github.com/lzakharov/5ff829160b4ec1064082aa3c2f144bc0
# if needed with jwt : https://hashnode.com/post/using-django-drf-jwt-authentication-with-django-channels-cjzy5ffqs0013rus1yb9huxvl
# or https://medium.com/@master.rta/django-channels-web-socket-authentication-approaches-3a56954b4120
import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.http import AsgiHandler
from django.urls import path
from django.conf import settings
from codenames_api.channels_middleware import JwtTokenAuthMiddleware
from public_chat.consumers import PublicChatConsumer
from private_chat.consumers import PrivateChatConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codenames_api.settings')
django.setup()

application = ProtocolTypeRouter({
	#'http': AsgiHandler(),
	'websocket': AllowedHostsOriginValidator(
		JwtTokenAuthMiddleware(
			URLRouter([
				path("public-chat/<room_id>/", PublicChatConsumer.as_asgi()),
				path("private-chat/<room_id>/", PrivateChatConsumer.as_asgi()),
			])
		)
	),
})