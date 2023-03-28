import datetime
import typing
from typing import Optional
import json
import asyncio
from asyncio import Queue, Task
from app.store.bot.dataclassess import (
    Update,
    MessageUpdateObject,
    EventUpdateObject,
    Message,
    Event
)

if typing.TYPE_CHECKING:
    from app.web.app import Application


# status
PLAYERS_AMOUNT = 2
REGISTERED = "registered"
ACTIVE = "active"
FINISHED = "finished"
# waiting status
THINKING = "thinking"
THINKING10 = "thinking10"
SPEAKER = "speaker"
ANSWER = "answer"


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot_worker_tasks: Optional[list[Task]] = None
        self.bot_queue = asyncio.Queue()
        self.bot_worker_number = 1

    async def publish_in_bot_queue(self, updates: list):
        for update in updates:
            self.bot_queue.put_nowait(update)

    async def _bot_worker(self):
        while True:
            message = await self.bot_queue.get()
            await self.handle_updates(message)
            self.bot_queue.task_done()

    # async def handle_updates(self, update):
    #     update = await self.prepare_message(update)
    #     user_id = update.object.user_id
    #     text = update.object.body
    #     message = Message(user_id=user_id, text=text)
    #     await self.app.store.vk_api.publish_in_sender_queue(message)

    @staticmethod
    def prepare_message(message: dict):
        if message["type"] == "message_new":
            return Update(
                type=message["type"],
                object=MessageUpdateObject(
                    id=message["object"]["message"]["id"],
                    user_id=message["object"]["message"]["from_id"],
                    peer_id=message["object"]["message"]["peer_id"],
                    text=message["object"]["message"]["text"],
                ),
            )
        if message["type"] == "message_event":
            return Update(
                type=message["type"],
                object=EventUpdateObject(
                    id=message["object"]["event_id"],
                    user_id=message["object"]["user_id"],
                    peer_id=message["object"]["peer_id"],
                    command=message["object"]["payload"]["command"],
                )
            )

    async def stop(self):
        await self.bot_queue.join()
        if self.bot_worker_tasks is not None:
            for t in self.bot_worker_tasks:
                t.cancel()

    async def start_bot_workers(self):
        self.bot_worker_tasks = [
            asyncio.create_task(self._bot_worker()) for _ in range(self.bot_worker_number)
        ]

    async def handle_updates(self, update: Update):
        update = self.prepare_message(update)
        user_id = update.object.user_id
        peer_id = update.object.peer_id
        if update.type == 'message_event':
            command = update.object.command
            event = Event(user_id=user_id, peer_id=peer_id, command=command)
            try:
                await self._event_handler(event)
            except Exception as err:
                self.app.store.vk_api.send_message("Error occurred: ", err)
        elif update.type == 'message_new':
            text = update.object.text
            message = Message(user_id=user_id, peer_id=peer_id, text=text)
            try:
                await self._message_handler(message)
            except Exception as err:
                self.app.store.vk_api.send_message("Error occurred: ", err)

    def make_message(self, text: str, user_id: int, peer_id: int, keyboard: dict = None):
        if keyboard is not None:
            start_button = self.make_button(
                {"type": "callback",
                 "payload": {"command": keyboard["command"]},
                 "label": keyboard["label"]},
                color="primary",
            )
            buttons = [[start_button], ]
            keyboard = json.dumps(self.build_keyboard(buttons=buttons))
        return Message(user_id=user_id, peer_id=peer_id, text=text, keyboard=keyboard)

    @staticmethod
    def build_keyboard(
            buttons: list[list[dict]],
            params: Optional[dict] = None,
            inline: Optional[bool] = False,
            one_time: Optional[bool] = True) -> dict:
        if params is not None:
            keyboard = params
        else:
            keyboard = {}
        keyboard["buttons"] = buttons
        keyboard["one_time"] = one_time
        keyboard["inline"] = inline
        return keyboard

    @staticmethod
    def make_button(params: dict, color: Optional[str] = None) -> dict:
        button = {"action": params}
        if color is not None:
            button["color"] = color
        return button

    def create_game_message(self, text, user_id: int, peer_id: int):
        return self.make_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={"command": "register", "label": "Присоединиться к игре"}
        )

    def start_game_message(self, text, user_id: int, peer_id: int):
        return self.make_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={"command": "start", "label": "Начать игру"}
        )

    async def _event_handler(self, event: Event):
        if event.command == "register":
            # breakpoint()
            game = await self.app.store.game.get_game_sql_model(chat_id=event.peer_id, status=REGISTERED)
            player = await self.app.store.game.get_player_by_vk_id_sql_model(vk_id=event.user_id)
            user = await self.app.store.vk_api.get_vk_user_by_id(user_id=event.user_id)
            players = []
            new_players = []
            if player is None:
                new_players.append({"vk_id": user["user_id"],
                                    "name": user["name"],
                                    "last_name": user["last_name"]})
            else:
                players.append(player)
            full_name = f'{user["name"]} {user["last_name"]}'
            if game is None:
                # if game hasn't been created we create it
                game = await self.app.store.game.create_game(
                    chat_id=event.peer_id,
                    created_at=datetime.datetime.now(),
                    players=players,
                    new_players=new_players
                )
                message = Message(text=f"{full_name}, Вы зарегистрированы. Ждем остальных участников.",
                                  user_id=event.user_id,
                                  peer_id=event.peer_id)
            # if game has been already created, we add a player to it
            else:
                players = game.players
                # if player is already added to this game and he clicks Register button again
                if player is not None and event.user_id in [player.vk_id for player in players]:
                    text = f"{full_name}, Вы уже зарегистрированы как участник в этой игре. " \
                           "Ждём подключения остальных участников..."
                    message = Message(text=text,
                                      user_id=event.user_id,
                                      peer_id=event.peer_id)
                # if a player is new at all or he was added but to another game
                else:
                    # if he is a new player at all
                    if player is None:
                        player = await self.app.store.game.create_player(vk_id=user["user_id"],
                                                                         name=user["name"],
                                                                         last_name=user["last_name"],
                                                                         games=[game])
                    # if player is already added, but not to this game, we add him to this game
                    else:
                        link = await self.app.store.game.link_player_to_game(
                            player_id=player.id, game_id=game.id
                        )
                    if len(game.players) + 1 == PLAYERS_AMOUNT:
                        text = "Все участники в сборе. Начинаем игру."
                        players = self.app.store.game.get_player_list(event.peer_id)
                        breakpoint()
                        message = self.start_game_message(text=text,
                                                          user_id=event.user_id,
                                                          peer_id=event.peer_id)
                    else:
                        message = Message(text=f"{full_name}, Вы зарегистрированы."
                                               " Ждем остальных участников.",
                                          user_id=event.user_id,
                                          peer_id=event.peer_id)
            await self.app.store.vk_api.publish_in_sender_queue(message)
            return

    async def _message_handler(self, message: Message):
        user = await self.app.store.vk_api.get_vk_user_by_id(user_id=message.user_id)
        full_name = f'{user["name"]} {user["last_name"]}'
        text = message.text.strip().lower()
        if text == "hello":
            game = await self.app.store.game.get_game_sql_model(chat_id=message.peer_id, status=ACTIVE)
            if game is not None:
                message.text = f"{full_name}, Вы уже играете! Лучше думайте над вопросами!"
                await self.app.store.vk_api.publish_in_sender_queue(
                    message
                )
                return
            game = await self.app.store.game.get_game_sql_model(chat_id=message.peer_id, status=REGISTERED)
            if game is None:
                text = f"{full_name}, Добрый день! Присоединяйтесь к игре."
                message = self.create_game_message(text=text,
                                                   user_id=message.user_id,
                                                   peer_id=message.peer_id)
                await self.app.store.vk_api.publish_in_sender_queue(message)
                return
            players = game.players
            if message.user_id in [player.vk_id for player in players]:
                message.text = f"{full_name}, Вы уже зарегистрированы как участник в этой игре. " \
                               "Ждём подключения остальных участников..."
            else:
                players = [f"{player.name} {player.last_name}" for player in game.players]
                players = " ,".join(players)
                text = f"{full_name}, идёт регистрация участников игры. " \
                       "Хотите зарегистрироваться? " \
                       "С нами следующие игроки: " + players
                message = self.create_game_message(text=text,
                                                   user_id=message.user_id,
                                                   peer_id=message.peer_id)
            await self.app.store.vk_api.publish_in_sender_queue(message)
            return

    async def send_goodbuy(self):
        games = await self.app.store.game.list_games()
        breakpoint()
        for game in games:
            chat_id = game.chat_id
            for player in game.players:
                vk_id = player.vk_id
                message = Message(text="Game over", peer_id=chat_id, user_id=vk_id)
                await self.app.store.vk_api.publish_in_sender_queue(message)
