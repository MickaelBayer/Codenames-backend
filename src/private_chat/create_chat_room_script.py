from friend.models import FriendList
from private_chat.utils import find_or_create_private_chat

friend_lists = FriendList.objects.all()
for f in friend_lists:
 for friend in f.friends.all():
    print(f"friend of {f.user} : {friend}")
    chat = find_or_create_private_chat(f.user, friend)
    chat.is_active = True
    chat.save()