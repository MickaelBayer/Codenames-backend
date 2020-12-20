# https://channels.readthedocs.io/en/latest/installation.html
# https://gist.github.com/lzakharov/5ff829160b4ec1064082aa3c2f144bc0
# if needed with jwt : https://hashnode.com/post/using-django-drf-jwt-authentication-with-django-channels-cjzy5ffqs0013rus1yb9huxvl
# or https://medium.com/@master.rta/django-channels-web-socket-authentication-approaches-3a56954b4120
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from codenames_api.channels_middleware import JwtTokenAuthMiddleware
from public_chat.consumers import (PublicChatConsumer)

application = ProtocolTypeRouter({
	'websocket': AllowedHostsOriginValidator(
		JwtTokenAuthMiddleware(
			URLRouter([
				path("public-chat/<room_id>/", PublicChatConsumer.as_asgi()),
			])
		)
	),
})