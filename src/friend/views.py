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


class FriendListView(RetrieveAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication
    serialize_class = AccountSerializer

    def get(self, request, user_id):
        user = request.user
        search_query = request.GET.get("q")
        response = None
        status_code = None
        if user_id:
            try:
                this_user = Account.objects.get(pk=user_id)
            except Account.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': "This user does not exist."
                })
            try:
                friend_list = FriendList.objects.get(user=this_user)
            except FriendList.DoesNotExist:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': f"Could not find a friend list for {this_user.username}."
                })
            # must be friend to see a users list
            if user != this_user: # if it s not your friend list
                if not user in friend_list.friends.all():
                    status_code = status.HTTP_403_FORBIDDEN
                    response = JSONRenderer().render({
                        'success': False,
                        'status_code': status_code,
                        'message': "You must be friend with a user to access this."
                    })
            friends = []
            auth_user_friend_list = FriendList.objects.get(user=user)
            for friend in friend_list.friends.all():
                if not search_query:
                    account = self.serialize_class(friend).data
                    account['is_friend'] = auth_user_friend_list.is_mutual_friend(friend)
                    account['is_self'] = friend == user
                    friends.append(account)
                else:
                    if search_query in friend.username or search_query in friend.email:
                        account = self.serialize_class(friend).data
                        account['is_friend'] = auth_user_friend_list.is_mutual_friend(friend)
                        account['is_self'] = friend == user
                        friends.append(account)
            friends = sorted(friends, key= lambda i: (i['username']))
            status_code = status.HTTP_200_OK
            response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': "Friend list fetched successfully.",
                'friends': friends
            })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'Missing patrameters in url.'
            })
        return Response(response, status=status_code)


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
            datas = sorted(datas, key= lambda i: (i['sender']['username']))
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
                friend_requests = FriendRequest.objects.filter(Q(sender=user, reciever=reciever) | Q(sender=reciever, reciever=user)).filter(is_active=True)
                # find if any is acive
                try:
                    for request in friend_requests:
                        if request.is_active:
                            raise Exception("A friend request already exist.")
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
                # if this friend requste is not active, it should not be considered
                if friend_request.is_active:
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
                else:
                    status_code = status.HTTP_404_NOT_FOUND
                    response = JSONRenderer().render({
                        'success': False,
                        'status_code': status_code,
                        'message': 'Friend request not found.'
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


class FriendRequestCancelView(UpdateAPIView):

    permission_classes = (IsAuthenticated,)
    authentification_class = JSONWebTokenAuthentication

    def post(self, request):
        user = request.user
        reciever_id = request.data['reciever_id']
        response = None
        status_code = None
        if reciever_id:
            reciever = Account.objects.get(pk=reciever_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, reciever=reciever, is_active=True)
            except Exception as e:
                status_code = status.HTTP_404_NOT_FOUND
                response = JSONRenderer().render({
                    'success': False,
                    'status_code': status_code,
                    'message': 'Friend request does not exist.'
                })
            # there should be only ever be one friend request in the set, but cancel in a loop, just in case
            for request in friend_requests:
                request.cancel()
            status_code = status.HTTP_201_CREATED
            response = JSONRenderer().render({
                'success': True,
                'status_code': status_code,
                'message': 'Friend request cancelled successfully.'
            })
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            response = JSONRenderer().render({
                'success': False,
                'status_code': status_code,
                'message': 'Request body is missiong reciever_id.'
            })
        return Response(response, status=status_code)
        