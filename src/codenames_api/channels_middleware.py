
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from django.contrib.auth.models import AnonymousUser


class JwtTokenAuthMiddleware:
    """
    JWT token authorization middleware for Django Channels 2
    """

    inner = None

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope, receive, send):
        try:
            coockies = str(dict(scope['headers'])[b'cookie']).split(';')
            token = ''
            for coockie in coockies:
                if 'authorization=' in coockie:
                    token = coockie.split('=')
                    token = token[-1] if token[-1][-1] != "'" else token[-1][:-1]
            # split the bearer tag
            token_header = token.split(" ")[1]
            data = {'token': token_header}
            valid_data = VerifyJSONWebTokenSerializer().validate(data)
            user = valid_data['user']
            scope['user'] = user
        except:
            scope['user'] = AnonymousUser()
        return self.inner(scope, receive, send)