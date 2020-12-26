from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    GenericAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from private_chat.models import PrivateChatRoom
from private_chat.utils import find_or_create_private_chat
from itertools import chain
from django.db.models.query_utils import Q
from account.serializers import AccountSerializer
from account.models import Account
from friend.models import FriendList


class PrivateChatRoomView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    account_serialiser_class = AccountSerializer

    def get(self, request):
        # find all the rooms this user is part of
        rooms = PrivateChatRoom.objects.filter(users__in=[request.user], is_active=True)
        private_chats = []
        status_code = status.HTTP_200_OK
        # message_and_friend:
        # {"room_id": id, "users": Account[]}
        for room in rooms:
            title = ''
            is_title_set = False
            chat_image = room.chat_image.url
            if room.title:
                title = room.title
            else:
                if len(room.users.all()) ==2:
                    if (room.users.all()[0] == request.user):
                        title = room.users.all()[1].username
                        chat_image = room.users.all()[1].profile_image.url
                        is_title_set = True
                    else:
                        title = room.users.all()[0].username
                        chat_image = room.users.all()[0].profile_image.url
                        is_title_set = True
            users = []
            for user in room.users.all():
                users.append(self.account_serialiser_class(user).data)
                if not is_title_set and user != request.user:
                    if title != '':
                        title += ', '
                    title += user.username
            private_chats.append({
                "id" : room.id,
                "title": title,
                "chatImage": chat_image,
                "users": users
            })
        response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'private_chats': private_chats
            })
        return Response(response, status=status_code)


class PrivateChatRoomFindOrCreateView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    account_serialiser_class = AccountSerializer

    def get(self, request, user_id):
        response = None
        status_code = None
        # find the user we want to chat with
        if user_id:
            try:
                user = Account.objects.get(id=user_id)
            except Account.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': 'This user does not exist.'
                })
            friend_list = FriendList.objects.get(user=request.user)
            # if we are friend
            if friend_list.is_mutual_friend(user):
                room = find_or_create_private_chat(request.user, user)
                status_code = status.HTTP_200_OK
                response = JSONRenderer().render({
                    'success': True,
                    'status_code': status_code,
                    'message': 'Private chat room retreived successfully.',
                    'room_id': room.id
                })
            else:
                status_code = status.HTTP_401_UNAUTHORIZED
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': 'You can ony chat with friends.'
                })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'The request is missing a user_id.'
            })
        return Response(response, status=status_code)