from public_chat.constants import MSG_TYPE_NEW_MESSAGE
from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturalday
from datetime import datetime


class LazyRoomChatMessageEncoder(Serializer):

    def get_dump_object(self, obj):
        dumped_obj = {}
        dumped_obj.update({'message_type': MSG_TYPE_NEW_MESSAGE})
        dumped_obj.update({'user_id': obj.user.id})
        dumped_obj.update({'username': obj.user.username})
        dumped_obj.update({'message': obj.content})
        dumped_obj.update({'profile_image': obj.user.profile_image.url})
        dumped_obj.update({'timestamp': calculate_timestamp(obj.timestamp)})
        return dumped_obj


def calculate_timestamp(timestamp):
    """
    1. Today or yesterday:
        - ex: 'today at 10:56 AM'
        - ex: 'yesterday at 5:19 PM'
    2. other:
        - ex: '05/06/2020'
    """
    # Today or yesterday
    if (naturalday(timestamp) == "today" or naturalday(timestamp) == "yesterday"):
        str_time = datetime.strftime(timestamp, "%I:%M %p")  # see datetime doc
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    # other days
    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
    return ts