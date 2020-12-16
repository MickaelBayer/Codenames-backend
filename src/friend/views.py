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

from account.models import Account
from account.serializers import AccountSerializer
from friend.models import FriendList, FriendRequest
from friend.serializers import FriendRequestSerializer

from django.db.models.query_utils import Q


class FriendRequestsSendersView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serializer_class = FriendRequestSerializer

    def get(self, request, user_id):
        user = request.user
        search_query = request.GET.get("q")
        response = None
        status_code = None
        try:
            account = Account.objects.get(pk=user_id)
        except Account.DoesNotExist:
            status_code = status.HTTP_404_NOT_FOUND
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': "This user does not exist."
            })
        if account == user:
            if search_query:
                friend_requests = FriendRequest.objects.filter(reciever=account, is_active=True).filter(Q(sender__email__icontains=search_query) | Q(sender__username__icontains=search_query))
            else:
                friend_requests = FriendRequest.objects.filter(reciever=account, is_active=True)
            datas = self.serializer_class(friend_requests, many=True).data
            for data in datas:
                data['sender'] = AccountSerializer(Account.objects.get(pk=data['sender'])).data
            status_code = status.HTTP_200_OK
            response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'Friend requests fetched successfully',
                'friend_requests': datas
            })
        else:
            status_code = status.HTTP_403_FORBIDDEN
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'You can not view another user\'s friend requests.'
            })
        return Response(response, status=status_code)


class FriendRequestCreateView(CreateAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def post(self, request):
        user = request.user
        reciever_id = request.data['reciever_id']
        response = None
        status_code = None
        if reciever_id:
            try:
                reciever = Account.objects.get(pk=reciever_id)
            except Account.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': "This user does not exist."
                })
            try:
                # get any friend request to check if one already pending
                friend_request = FriendRequest.objects.filter(sender=user, reciever=reciever)
                # find if any is acive
                try:
                    for request in friend_request:
                        if request.is_active:
                            raise Exception("You already send them a friend request.")
                    # if none active, create a new friend request
                    friend_request = FriendRequest(sender=user, reciever=reciever)
                    friend_request.save()
                    status_code = status.HTTP_201_CREATED
                    response = JSONRenderer().render({
                        'success': True,
                        'status_code': status_code,
                        'message': 'Friend request sent successfully'
                    })
                except Exception as e:
                    status_code = status.HTTP_400_BAD_REQUEST
                    response = JSONRenderer().render({
                        'success': False,
                        'status_code': status_code,
                        'message': str(e)
                    })
            except FriendRequest.DoesNotExist:
                # no friend request found
                friend_request = FriendRequest(sender=user, reciever=reciever)
                friend_request.save()
                status_code = status.HTTP_201_CREATED
                response = JSONRenderer().render({
                    'success': True,
                    'status_code': status_code,
                    'message': 'Friend request sent successfully.'
                })
            if not response:
                status_code = status.HTTP_400_BAD_REQUEST
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': "Something went wrong."
                })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': "User id is missing."
            })
        return Response(response, status=status_code)

class FriendRequestAcceptView(UpdateAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def get(self, request, friend_request_id):
        user = request.user
        response = None
        status_code = None
        if friend_request_id:
            try:
                friend_request = FriendRequest.objects.get(pk=friend_request_id)
                # confirm that is the correct request
                if friend_request.reciever == user:
                    # found it and accept it
                    friend_request.accept()
                    status_code = status.HTTP_201_CREATED
                    response = JSONRenderer().render({
                        'success': True,
                        'status_code': status_code,
                        'message': 'Friend request accepted.'
                    })
                else:
                    status_code = status.HTTP_403_FORBIDDEN
                    response = JSONRenderer().render({
                        'success': False,
                        'status_code': status_code,
                        'message': 'This friend request is not for you.'
                    })
            except FriendRequest.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': 'Friend request not found.'
                })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'Friend request id parameter not found.'
            })
        return Response(response, status=status_code)


class FriendRemoveView(DestroyAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def post(self, request):
        user = request.user
        reciever_user_id = request.data['reciever_user_id']
        response = None
        status_code = None
        if reciever_user_id:
            try:
                removee = Account.objects.get(pk=reciever_user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                status_code = status.HTTP_200_OK
                response = JSONRenderer().render({
                    'success': True,
                    'status_code': status_code,
                    'message': 'Friend removed successfully.'
                })
            except Exception as e:
                status_code = status.HTTP_400_BAD_REQUEST
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': f'Something went wrong: {str(e)}'
                })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'This friend could not be found.'
            })
        return Response(response, status=status_code)


class FriendRequestDeclineView(UpdateAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def get(self, request, friend_request_id):
        user = request.user
        response = None
        status_code = None
        if friend_request_id:
            try:
                friend_request = FriendRequest.objects.get(pk=friend_request_id)
                if friend_request.reciever == user:
                    friend_request.decline()
                    status_code = status.HTTP_201_CREATED
                    response = JSONRenderer().render({
                        'success': True,
                        'status_code': status_code,
                        'message': 'Friend request decline successfully.'
                    })
                else:
                    status_code = status.HTTP_403_FORBIDDEN
                    response = JSONRenderer().render({
                        'success': False,
                        'status_code': status_code,
                        'message': 'This friend request is not for you.'
                    })
            except FriendRequest.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': 'This friend request could not be found.'
                })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'Friend request id parameter not found.'
            })
        return Response(response, status=status_code)


