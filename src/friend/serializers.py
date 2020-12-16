from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework_jwt.settings import api_settings
from friend.models import FriendList, FriendRequest
from account.serializers import AccountSerializer
from account.models import Account


JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class FriendListSerializer(serializers.ModelSerializer):

    class Meta:
        model = FriendList
        fields = ('friends',)

class FriendRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = FriendRequest
        fields = ('id', 'sender')