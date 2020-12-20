from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    GenericAPIView,
    UpdateAPIView
)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from account.serializers import (
    AccountRegistrationSerializer,
    AccountLoginSerializer,
    AccountSerializer,
    AccountUpateSerializer
)
from account.models import Account

from friend.models import FriendList, FriendRequest
from friend.utils import get_friend_request_or_false
from friend.friend_request_status import FriendRequestStatus
from friend.serializers import FriendListSerializer, FriendRequestSerializer

from django.contrib.auth import authenticate, login, logout
from django.db.models.query_utils import Q

import json


class AccountRegistrationView(CreateAPIView):

    register_serializer_class = AccountRegistrationSerializer
    login_serializer_class = AccountLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        register_serializer = self.register_serializer_class(data=request.data)
        register_serializer.is_valid(raise_exception=True)
        register_serializer.create(register_serializer.data)
        login_serializer = self.login_serializer_class(data=request.data)
        login_serializer.is_valid()
        status_code = status.HTTP_201_CREATED
        response = JSONRenderer().render({
            'success': True,
            'status_code': status_code,
            'message': 'User registred in successfully',
            'user': login_serializer.data['user'],
            'token': login_serializer.data['token']
        })
        return Response(response,status=status_code)


class AccountLoginView(RetrieveAPIView):

    serializer_class = AccountLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_code = status.HTTP_200_OK
        response = JSONRenderer().render({
            'success': True,
            'status_code': status_code,
            'message': 'User logged in successfully',
            'user': serializer.data['user'],
            'token': serializer.data['token']
        })
        return Response(response, status=status_code)


class AccountProfileView(RetrieveAPIView):
    
    serializer_class = AccountSerializer
    friend_list_serializer_class = FriendListSerializer
    friend_request_serializer_class = FriendRequestSerializer
    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def get(self, request):
        try:
            account = Account.objects.get(id= request.user.id)
            data = self.serializer_class(account).data
            friend_requests = FriendRequest.objects.filter(reciever=account, is_active=True)
            try:
                friend_list = FriendList.objects.get(user=account)
            except FriendList.DoesNotExist:
                friend_list = FriendList(user=account)
                friend_list.save()
            request_sent = None
            pending_friend_request_id = None
            data['is_self'] = True
            data['is_friend'] = False
            data['request_sent'] = request_sent
            data['friend_requests'] = self.friend_request_serializer_class(friend_requests, many=True).data
            data['friend_list'] = self.friend_list_serializer_class(friend_list).data['friends']
            data['pending_friend_request_id'] = pending_friend_request_id
            status_code = status.HTTP_200_OK
            response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'User profile fetched successfully',
                'data': data
            })
        except Exception as e:
            status_code = status.HTTP_404_NOT_FOUND
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'User does not exist',
                'error': str(e)
            })
        return Response(response, status=status_code)


class AccountLogoutView(GenericAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def get(self, request):
        logout(request)
        status_code = status.HTTP_200_OK
        response = JSONRenderer().render({
            'success': True,
            'status_code': status_code,
            'message': 'User logged out successfully'
        })
        return Response(response, status=status_code)


class AccountView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serializer_class = AccountSerializer
    friend_list_serializer_class = FriendListSerializer
    friend_request_serializer_class = FriendRequestSerializer

    def get(self, request, user_id):
        """
        - logic is kind of tricky
            is_self (boolean)
                is_friend (boolean)
                    -1: NO_REQUEST_SENT
                    0: THEM_SENT_TO_YOU
                    1: YOU_SENT_TO_THEM
        """
        try:
            account = Account.objects.get(id=user_id)
            try:
                # friend list of viewed account
                friend_list = FriendList.objects.get(user=account)
            except FriendList.DoesNotExist:
                friend_list = FriendList(user=account)
                friend_list.save()
            friends = friend_list.friends.all()
            is_self = True
            is_friend = False
            user = request.user
            friend_requests = None
            request_sent = None
            pending_friend_request_id = None
            # Not your profile
            if user.is_authenticated and user != account:
                is_self = False
                if friends.filter(pk=user.id):
                    is_friend = True
                else:
                    # No friend cases:
                    # THEM_TO_YOU
                    if get_friend_request_or_false(sender=account, reciever=user) != False:
                        request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                        pending_friend_request_id = get_friend_request_or_false(sender=account, reciever=user).id
                    # YOU TO THEM
                    elif get_friend_request_or_false(sender=user, reciever=account) != False:
                        request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                    # NO REQUEST
                    else:
                        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
            # not logged in : should not happen
            elif not user.is_authenticated:
                is_self = False
            # Your profile
            else:
                try:
                    friend_requests = FriendRequest.objects.filter(reciever=user, is_active=True)
                except:
                    pass

            fetched_profile = self.serializer_class(account).data
            fetched_profile['is_self'] = is_self
            fetched_profile['is_friend'] = is_friend
            fetched_profile['request_sent'] = request_sent
            fetched_profile['friend_requests'] = self.friend_request_serializer_class(friend_requests, many=True).data
            fetched_profile['friend_list'] = self.friend_list_serializer_class(friend_list).data['friends']
            fetched_profile['pending_friend_request_id'] = pending_friend_request_id
            status_code = status.HTTP_200_OK
            response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'Profile fetched successfully',
                'data': fetched_profile
            })
        except Account.DoesNotExist as e:
            status_code = status.HTTP_404_NOT_FOUND
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'User does not exist',
                'error': str(e)
            })           
        
        return Response(response, status=status_code)


class AccountSearchView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serializer_class = AccountSerializer

    def get(self, request):
        search_query = request.GET.get("q")
        accounts = []
        if len(search_query) != 0:
            search_result = Account.objects.filter(Q(email__icontains=search_query) | Q(username__icontains=search_query)).distinct()
            for account in search_result:
                serialized_account = self.serializer_class(account).data
                if account.id == request.user.id:
                    serialized_account['is_self'] = True
                else:
                    serialized_account['is_self'] = False
                # get the friend list of the authenticated user
                try:
                    friend_list = FriendList.objects.get(user=request.user)
                except FriendList.DoesNotExist:
                    # TODO check what we wanna do here
                    serialized_account['is_friend'] = False
                if account in friend_list.friends.all():
                    serialized_account['is_friend'] = True
                else: 
                    serialized_account['is_friend'] = False
                accounts.append(serialized_account)
                accounts = sorted(accounts, key= lambda i: (i['username']))
        status_code = status.HTTP_200_OK  
        response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'Searched successfully',
                'data': accounts
            })
        return Response(response, status=status_code)


class AccountAllView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serializer_class = AccountSerializer

    def get(self, request):
        accounts = []
        search_result = Account.objects.filter()
        for account in search_result:
            serialized_account = self.serializer_class(account).data
            if account.id == request.user.id:
                serialized_account['is_self'] = True
            else:
                serialized_account['is_self'] = False
            # get the friend list of the authenticated user
            try:
                friend_list = FriendList.objects.get(user=request.user)
            except FriendList.DoesNotExist:
                # TODO check what we wanna do here
                serialized_account['is_friend'] = False
            if account in friend_list.friends.all():
                serialized_account['is_friend'] = True
            else: 
                serialized_account['is_friend'] = False
            accounts.append(serialized_account)
            accounts = sorted(accounts, key= lambda i: (i['username']))
        status_code = status.HTTP_200_OK  
        response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'All profiles fetched successfully',
                'data': accounts
            })
        return Response(response, status=status_code)


class AccountEditView(UpdateAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serializer_class = AccountUpateSerializer

    def post(self, request):
        if 'profile_image' in request.data:
            request.user.profile_image.delete()
        serializer = self.serializer_class(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        # delete old profile image so the name is preserved
        serializer.save()
        status_code = status.HTTP_201_CREATED
        response = JSONRenderer().render({
            'success': True,
            'status_code': status_code,
            'message': 'Profile updated in successfully',
            'user': AccountSerializer(serializer.instance).data
        })
        return Response(response,status=status_code)

