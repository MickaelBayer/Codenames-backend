from django.db import models
from django.conf import settings
from django.utils import timezone

from private_chat.utils import find_or_create_private_chat


class FriendList(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friends")

    def __str__(self):
        return self.user.username

    def add_friend(self, account):
        """
        Add a new friend
        """
        if not account in self.friends.all():
            self.friends.add(account)
            chat = find_or_create_private_chat(self.user, account)
            if not chat.is_active:
                chat.is_active = True
                chat.save()

    def remove_friend(self, account):
        """
        Remove a friend
        """
        if account in self.friends.all():
            self.friends.remove(account)
            chat = find_or_create_private_chat(self.user, account)
            if chat.is_active:
                chat.is_active = False
                chat.save()

    def unfriend(self, removee):
        """
        Initiate the action of unfriending someone
        """
        remover_friend_list = self # person terminating the frienship
        # remove friend from remover friend list
        remover_friend_list.remove_friend(removee)
        # remove the remover from removee friend list
        removee_friend_list = FriendList.objects.get(user=removee)
        removee_friend_list.remove_friend(self.user)

    def is_mutual_friend(self, account):
        """
        Is this a friend ? 
        """
        if account in self.friends.all():
            return True
        return False


class FriendRequest(models.Model):
    """
    A friend request consist in 2 main parts:
        1. SENDER:
            - Person sending/initiating the friend request
        2. RECIEVER:
            - Person recieving the friend request
    """

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    reciever = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reciever")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender.username

    def accept(self):
        """
        Accept a friend request
        Update both SENDER and RECIEVER friend lists
        """
        reciever_friend_list = FriendList.objects.get(user=self.reciever)
        sender_friend_list = FriendList.objects.get(user=self.sender)
        if reciever_friend_list and sender_friend_list:
            reciever_friend_list.add_friend(self.sender)
            sender_friend_list.add_friend(self.reciever)
            self.is_active = False
            self.save()

    def decline(self):
        """
        Decline a friend request.
        It is declined by setting the is_active to false.
        """
        self.is_active = False
        self.save()

    def cancel(self):
        """
        Cancel a friend request.
        It is cancelled by setting the is_active to false.
        This is only different with respect to declining through the notification that is generated
        """
        self.is_active = False
        self.save()