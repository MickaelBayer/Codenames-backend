from django.urls import path
from friend.views import (
    FriendRequestCreateView,
    FriendRequestsSendersView,
    FriendRequestAcceptView,
    FriendRemoveView,
    FriendRequestDeclineView,
    FriendRequestCancelView
)

urlpatterns = [
    path('accept-friend-request/<friend_request_id>/', FriendRequestAcceptView.as_view(), name='accept-friend-request'),
    path('friend-cancel/', FriendRequestCancelView.as_view(), name='cancel-friend-request'),
    path('friend-decline/<friend_request_id>/', FriendRequestDeclineView.as_view(), name='decline-friend-request'),
    path('friend-remove/', FriendRemoveView.as_view(), name='remove-friend'),
    path('friend-request/', FriendRequestCreateView.as_view(), name='friend-request'),
    path('friend-request/<user_id>/', FriendRequestsSendersView.as_view(), name='friend-requests'),
]