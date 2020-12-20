from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime
from public_chat.models import PublicChatRoom, PublicRoomChatMessage



NEW_MESSAGE_TYPE = 0

user = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection
        """
        print("[PublicChatConsumer] connect: " + str(self.scope['user']))
        await self.accept()
        self.room_id = None

    async def disconnect(self, code):
        """
        Called when the websocket for any reason
        """
        print("[PublicChatConsumer] disconnect")
        try:
            if self.room_id != None:
               await self.leave_room(self.room_id) 
        except Exception:
            pass

    async def receive_json(self, content):
        """
        called when we get a text frame.
        Channels will JSON-decode the payload and pass it as the first argiment.
        """
        command = content.get("command", None)
        print("[PublicChatConsumer] recieve json: " + str(command))
        try:
            if command == 'send':
                if len(content['message'].lstrip()) == 0:
                    # HTTPstatus 422
                    raise ClientError(422, "You can not send an empty message.")
                await self.send_room(content['room_id'], content['message'])
            elif command == 'join':
                await self.join_room(content['room_id'])
            elif command == 'leave':
                await self.leave_room(content['room_id'])
        except ClientError as e:
            await self.handle_client_error(e)
        

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone send a message to a room
        """
        print("[PublicChatConsumer][send_room] send a message to room " + str(room_id))
        if self.room_id != None:
            if str(room_id) != str(self.room_id):
                raise ClientError(403, "Room acces denied.")
            if not is_authenticated(self.scope['user']):
                raise ClientError(403, "Yoi must be authenticated to chat.")
        else:
            raise ClientError(403, "Room acces denied.")
        room = await get_room_or_error(room_id)
        await create_public_room_chat_message(room, self.scope['user'], message)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message", # relate to the method chat_message
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "message": message
            }
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat
        """
        # send a message down to the client
        print("[PublicChatConsumer] chat_message from user #: " + str(event['user_id']))
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
            "message_type": NEW_MESSAGE_TYPE,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['user_id'],
            "message": event['message'],
            "timestamp": timestamp            
        })

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a JOIN command
        """
        print("[PublicChatConsumer][join_room] room_id: " + str(room_id))
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)
        # add user to the users list for room
        if is_auth:
            await connect_user(room, self.scope['user'])
        # store that they're in the room
        self.room_id = room.id
        # add them to the group so they get room messages
        await self.channel_layer.group_add(room.group_name, self.channel_name)
        # tell the client to finish opening the room
        await self.send_json({
            "join": str(room_id),
            "username": self.scope['user'].username
        })
    
    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a LEAVE command
        """
        print("[PublicChatConsumer][leave_room] room_id: " + str(room_id))
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)
        # remove user from users list for room
        await disconnect_user(room, self.scope['user'])
        # Remove that they're in the room
        self.room_id = None
        # Remove them to the group so they no longer receive room messages
        await self.channel_layer.group_discard(room.group_name, self.channel_name)
    



    async def handle_client_error(self, error):
        """
        Called when a client error is raised and send a the data to user
        """
        errorData = {}
        errorData['error'] = error.code
        if error.message:
            errorData['message'] = error.message
            # send directly to the client, not the group
            await self.send_json(errorData)
        return


def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False

@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)

@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)

@database_sync_to_async
def get_room_or_error(room_id):
    """
    try do fetch a room
    """
    try:
        room = PublicChatRoom.objects.get(pk=room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError(404, "Could not find this room.")
    return room

@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    return PublicRoomChatMessage.objects.create(user=user, room=room, content=message)


class ClientError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client
    """

    def __init__(self, code, message):
        super().__init__(code)
        self.code = code
        if message:
            self.message = message


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