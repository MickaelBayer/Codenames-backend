from private_chat.models import PrivateChatRoom
from django.db.models.query_utils import Q
from django.db.models import Count


def find_or_create_private_chat(user1, user2):
    """
    Find or create a 2 users chat room
    """
    try:
        chat = PrivateChatRoom.objects.annotate(num_users=Count('users')).filter(Q(num_users=2) & Q(users__in=[user1])).get(users__in=[user2]) 
    except PrivateChatRoom.DoesNotExist:
        chat = PrivateChatRoom()
        chat.save()
        chat.users.add(user1)
        chat.users.add(user2)
        chat.save()
    return chat
