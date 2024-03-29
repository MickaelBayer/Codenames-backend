from django.contrib import admin
from friend.models import FriendList, FriendRequest


class FriendListAdmin(admin.ModelAdmin):

    list_filter = ['user']
    list_display = ['user', 'get_friends']
    search_fields = ['user']
    readonly_fields = ['user']

    class Meta:
        model = FriendList
    
    def get_friends(self, obj):
        return ", ".join([friend.username for friend in obj.friends.all()])

admin.site.register(FriendList, FriendListAdmin)


class FriendRequestAdmin(admin.ModelAdmin):

    list_filter = ['sender', 'reciever', 'is_active']
    list_display = ['sender', 'reciever', 'is_active']
    search_fields = ['sender__username', 'sender__email','reciever__username', 'reciever__email']

    class Meta:
        model = FriendRequest

admin.site.register(FriendRequest, FriendRequestAdmin)
