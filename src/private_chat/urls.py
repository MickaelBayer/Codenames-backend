from django.urls import path
from private_chat.views import PrivateChatRoomView, PrivateChatRoomFindOrCreateView


urlpatterns = [
    path('', PrivateChatRoomView.as_view(), name='private-chat'),
    path('<user_id>/', PrivateChatRoomFindOrCreateView.as_view(), name='private-chat-with-user')
]