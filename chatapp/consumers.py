import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from players.models import Challenge, Squad
from django.db.models import Q
from chatapp.models import ChallengeGroupChat, PersonalChat as PersonalChatModel
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from notification.task import send_user_action_notification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        challenge_id = self.scope['url_route']['kwargs']['challenge_id']
        challenges = await self.get_challenge(self.scope['user'], challenge_id)
        room_name = f"{self.scope['user'].id}{challenge_id}"

        if challenges:
            # print(f"{self.scope['user']} - join - {challenge_id}")
            await self.channel_layer.group_add(room_name, self.channel_name)
            await self.channel_layer.group_add(challenge_id, self.channel_name)
            await self.accept()
            pre_messages = await self.get_user_chat_history(self.scope['user'], challenge_id)
            for msg in pre_messages:
                await self.channel_layer.group_send(
                    str(room_name), {
                        "type": "chat.history",
                        "message": {
                            "message": {"id": str(msg.id), "text": msg.message},
                            "challenge": challenge_id,
                            "timestamp": msg.created_at.strftime("%d/%m/%Y, %H:%M:%S"),
                            "is_sender": True if msg.users.id == self.scope['user'].id else False,
                            "user": {
                                "username": msg.users.username,
                                "fullname": msg.users.get_full_name(),
                                "profile_pic": msg.users.profile_pic.url if msg.users.profile_pic else ""
                            }
                        }}
                )

        else:
            await self.close()

        # for challenge in challenges:
        #     print(f"{self.scope['user']} - join - {challenge.challenge_id}")
        #     await self.channel_layer.group_add(challenge.challenge_id, self.channel_name)

    async def disconnect(self, close_code):
        leave = await self.leave_room()

    async def receive(self, text_data=None, bytes_data=None):
        # print("receive text_data -- ", text_data)
        challenge_id = self.scope['url_route']['kwargs']['challenge_id']
        data = json.loads(text_data)
        msg = await self.save_chat(data)
        user = msg.users

        await self.channel_layer.group_send(
            challenge_id, {
                "type": "chat.message",
                "message": {
                    "message": {"id": str(msg.id), "text": msg.message},
                    "challenge": challenge_id,
                    "timestamp": msg.created_at.strftime("%d/%m/%Y, %H:%M:%S"),
                    "user": {
                        "username": user.username,
                        "fullname": user.get_full_name(),
                        "profile_pic": user.profile_pic.url if user.profile_pic else ""
                    }
                },
                "sender_id": user.id
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        try:
            sender_id = event["sender_id"]
            is_sender = self.scope["user"].id == sender_id
            message['is_sender'] = is_sender
        except:
            pass

        await self.send(text_data=json.dumps(message))

    async def chat_history(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def leave_room(self):
        challenge_id = self.scope['url_route']['kwargs']['challenge_id']

        # challenges = await self.get_challenge(self.scope['user'])
        # for challenge in challenges:
        #     print(f"{self.scope['user']} - leave - {challenge.challenge_id}")
        await self.channel_layer.group_discard(challenge_id, self.channel_name)

    @database_sync_to_async
    def get_challenge(self, user, challenge_id):
        user_squad = Squad.objects.filter(
            Q(created_by=user) |
            Q(players=user)
        )
        user_squad_list = [squad.id for squad in user_squad]

        return Challenge.objects.filter(
            Q(first_squad__id__in=user_squad_list) |
            Q(second_squad__id__in=user_squad_list),
            is_accepted=True,
            result_date__gt=datetime.now().date() - timedelta(days=1),
            challenge_id=challenge_id
        ).first()

    @database_sync_to_async
    def get_user_chat_history(self, user, challenge_id):
        queryset = list(
            ChallengeGroupChat.objects.select_related("challenge", "users").filter(
                # Q(
                #     Q(challenge__first_squad__players=user) |
                #     Q(challenge__second_squad__players=user),
                # ),
                challenge__challenge_id=challenge_id
            ).order_by('created_at').distinct()
        )
        return queryset

    @database_sync_to_async
    def save_chat(self, data):
        challenge_id = self.scope['url_route']['kwargs']['challenge_id']
        return ChallengeGroupChat.objects.create(
            challenge=Challenge.objects.get(challenge_id=challenge_id),
            message=data['message'],
            users=self.scope['user']
        )


class PersonalChat(AsyncWebsocketConsumer):

    async def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']

        user_ids = sorted([str(self.scope['user'].id), str(user_id)])
        self.room_name = f"private_chat_{user_ids[0]}_{user_ids[1]}"
        single_room = str(self.scope["user"].id)
        await self.channel_layer.group_add(self.room_name, self.channel_name)  # for both user
        await self.channel_layer.group_add(single_room, self.channel_name)  # for only current or connector
        await self.accept()

        pre_messages = await self.get_chat_history()

        for msg in pre_messages:
            try:
                post_id = await sync_to_async(lambda: msg.post.id)()
            except:
                post_id = ""

            await self.channel_layer.group_send(
                single_room, {
                    "type": "chat_message",
                    "message": {
                        "message": {"id": str(msg.id), "text": msg.message},
                        "timestamp": msg.created_at.strftime("%d/%m/%Y, %H:%M:%S"),
                        "is_sender": True if msg.sender.id == self.scope['user'].id else False,
                        "user": {
                            "username": msg.sender.username,
                            "fullname": msg.sender.get_full_name(),
                            "profile_pic": msg.sender.profile_pic.url if msg.sender.profile_pic else ""
                        },
                        "post_id": post_id
                    }}
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data.get("message")
        user = self.scope["user"]

        if message:
            msg = await self.save_message(
                message=message
            )
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat_message",
                    "message": {
                        "message": {"id": str(msg.id), "text": msg.message},
                        "timestamp": msg.created_at.strftime("%d/%m/%Y, %H:%M:%S"),
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "fullname": user.get_full_name(),
                            "profile_pic": user.profile_pic.url if user.profile_pic else ""
                        }
                    },
                    "sender_id": user.id
                }
            )

    async def chat_message(self, event):
        message = event["message"]
        try:
            sender_id = event["sender_id"]
            is_sender = self.scope["user"].id == sender_id
            message['is_sender'] = is_sender
        except:
            pass

        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def get_chat_history(self):
        sender_id = self.scope["user"].id
        receiver_id = self.scope['url_route']['kwargs']['user_id']
        queryset = list(PersonalChatModel.objects.select_related("sender", "receiver").filter(
            Q(sender_id=sender_id, receiver_id=receiver_id) |
            Q(receiver_id=sender_id, sender_id=receiver_id)
        ).order_by('created_at').distinct()
                        )

        return queryset

    @database_sync_to_async
    def save_message(self, message):
        sender_id = self.scope["user"].id
        receiver_id = self.scope['url_route']['kwargs']['user_id']
        message_obj = PersonalChatModel.objects.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )

        # notification

        notification_obj = {"action": "/user-personal-chat", "sender": self.scope["user"].username,
                            "receiver": message_obj.receiver.username,
                            "object_id": f"{message_obj.id}", "message": f"{message}"}
        send_user_action_notification.delay(
            **notification_obj
        )

        return message_obj
