from django.db import models
from django.conf import settings


class PrivateChatRoom(models.Model):
    """
    A private chat room for 2 users to chat
    """
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user1")
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user2")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Private chat between {user1} and {user2}"
    
    @property
    def group_name(self):
        """
        Returns the channels group name that sockets should subscribe to
        to receive the messages as they are generated.
        """
        return f"PrivateChatRoom-{self.id}"


class PrivateRoomChatMessageManager(models.Manager):
    
    def by_room(self, room):
        qs = PrivateRoomChatMessage.objects.filter(room=room).order_by("-timestamp")
        return qs


class PrivateRoomChatMessage(models.Model):
    """
    Private chat message create by a user inside a room
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    objects = PrivateRoomChatMessageManager()

    def __str__(self):
        return self.content

