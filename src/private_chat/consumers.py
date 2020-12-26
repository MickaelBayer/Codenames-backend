from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from public_chat.serializers import LazyRoomChatMessageEncoder, calculate_timestamp
from django.core.paginator import Paginator
import json

from private_chat.models import PrivateChatRoom, PrivateRoomChatMessage
from friend.models import FriendList
from account.serializers import AccountSerializer
from private_chat.exceptions import ClientError

from django.utils import timezone
from public_chat.constants import (
    DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE,
    MSG_TYPE_CONNECTED_USER_COUNT,
    MSG_TYPE_NEW_MESSAGE
)


class PrivateChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("[PrivateChatConsumer] connect: " + str(self.scope["user"]))

        # let everyone connect. But limit read/write to authenticated users
        await self.accept()

        # the room_id will define what it means to be "connected". If it is not None, then the user is connected.
        self.room_id = None


    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        print("[PrivateChatConsumer] receive_json")
        command = content.get("command", None)
        try:
            if command == "join":
                await self.join_room(content['room_id'])
            elif command == "leave":
                await self.leave_room(content['room_id'])
            elif command == "send":
                if len(content['message'].lstrip()) == 0:
                    # HTTPstatus 422
                    raise ClientError(422, "You can not send an empty message.")
                await self.send_room(content['room_id'], content['message'])
            elif command == "get_chatroom_messages":
                room = await get_room_or_error(content['room_id'], self.scope['user'])
                payload = await get_room_chat_message(room, content['page_number'])
                if payload != None:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, "Something went wrong retrieving chatroom messages.")
            elif command == "get_user_info":
                pass
        except ClientError as e:
            await self.handle_client_error(e)


    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the room
        print("[PrivateChatConsumer] disconnect")
        try:
            if self.room_id != None:
                await self.leave_room(self.room_id)
        except Exception as e:
            pass


    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
        print("[PrivateChatConsumer] join_room: " + str(room_id))
        try:
            room = await get_room_or_error(room_id, self.scope['user'])
        except ClientError as e:
            return await self.handle_client_error(e)
        # Store thas we are in the room
        self.room_id = room_id
        # Add them to the group so they receive the room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )
        # send message back to the client
        await self.send_json({
            "join": str(room_id),
            "username": self.scope['user'].username
        })



    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        print("[PrivateChatConsumer] leave_room")
        room = await get_room_or_error(room_id, self.scope['user'])
        # Notify the group that someone left
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.leave",
                "room_id": room_id,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "profile_image": self.scope['user'].profile_image.url
            }
        )
        self.room_id = None
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name
        )
        await self.send_json({
            "leave": str(room_id)
        })


    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        print("[PrivateChatConsumer] send_room")
        if self.room_id != None:
            # TODO WTF is this test
            if str(room_id) != str(self.room_id):
                raise ClientError(403, "Room acces denied. ")
        else:
            raise ClientError(403, "Room acces denied. ")
        if not is_authenticated(self.scope['user']):
            raise ClientError(403, "You must be authenticated to chat.")
        room = await get_room_or_error(room_id, self.scope['user'])
        await create_room_chat_message(room, self.scope['user'], message)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "profile_image": self.scope["user"].profile_image.url,
                "username": self.scope["user"].username,
                "user_id": self.scope["user"].id,
                "message": message,
            }
        )

    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        print("[PrivateChatConsumer] chat_join: " + str(self.scope["user"].id))


    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        print("[PrivateChatConsumer] chat_leave")


    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        print("[PrivateChatConsumer] chat_message")
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
            "message_type": MSG_TYPE_NEW_MESSAGE,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['user_id'],
            "message": event['message'],
            "timestamp": timestamp
        })


    async def send_messages_payload(self, messages, new_page_number):
        """
        Send a payload of messages to the ui
        """
        print("[PrivateChatConsumer] send_messages_payload. ")
        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number,
        })


    async def send_user_info_payload(self, user_info):
        """
        Send a payload of user information to the ui
        """
        print("[PrivateChatConsumer] send_user_info_payload. ")


    async def display_progress_bar(self, is_displayed):
        """
        1. is_displayed = True
            - Display the progress bar on UI
        2. is_displayed = False
            - Hide the progress bar on UI
        """
        print("DISPLAY PROGRESS BAR: " + str(is_displayed))


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
def get_room_or_error(room_id, user):
    """
    Tries to fetch a room for the user, checking permission along the way
    """
    try:
        room = PrivateChatRoom.objects.get(pk=room_id)
    except PrivateChatRoom.DoesNotExist:
        raise ClientError(404, "Invalid room. ")
    # Is this user allowed in this room
    if not user in room.users.all():
        raise ClientError(403, "You do not have the permission to chat in that room. ")
    return room

@database_sync_to_async
def create_room_chat_message(room, user, message):
    return PrivateRoomChatMessage.objects.create(user=user, room=room, content=message)

@database_sync_to_async
def get_room_chat_message(room, page_number):
    try:
        qs = PrivateRoomChatMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:  # if we have not reached the last page of result + 1
            new_page_number += 1
            serializer = LazyRoomChatMessageEncoder()
            payload['messages'] = serializer.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = None
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        return None