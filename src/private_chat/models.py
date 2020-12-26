from django.db import models
from django.conf import settings


def get_chat_image_filepath(self, filename):
    return f'chat_image/{str(self.pk)}/{"chat_image.png"}'

def get_default_chat_image():
    return "default_chat_image/chat_image.png"

class PrivateChatRoom(models.Model):
    """
    A private chat room for users to chat
    """
    title = models.CharField(max_length=255, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='users', help_text="users authorized in the private chat")
    connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='connected_users', help_text="users connected to the chat")
    is_active = models.BooleanField(default=True)
    chat_image = models.ImageField(max_length=255, upload_to=get_chat_image_filepath, null=True, blank=True, default=get_default_chat_image)

    def __str__(self):
        return f"Private chat {self.title}"
    
    @property
    def group_name(self):
        """
        Returns the channels group name that sockets should subscribe to
        to receive the messages as they are generated.
        """
        return f"PrivateChatRoom-{self.id}"

    def connect_user(self, user):
        """
        return True if the user is added to the connected_users list
        """
        is_user_added = False
        if user in self.users.all():
            if not user in self.connected_users.all():
                self.connected_users.add(user)
                self.save()
                is_user_added = True
            elif user in self.connected_users.all():
                is_user_added = True
        return is_user_added

    def disconnect_user(self, user):
        """
        return True if user is removed from the users list
        """
        is_user_removed = False
        if user in self.users.all():
            if user in self.connected_users.all():
                self.connected_users.remove(user)
                self.save()
                is_user_removed = True
        return is_user_removed

    def get_chat_image_filename(self):
        """
        return the name of the uploaded file
        """
        return str(self.chat_image)[str(self.chat_image).index(f'chat_image{str(self.pk)}/'):]


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

