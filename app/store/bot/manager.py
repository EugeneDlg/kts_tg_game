import datetime
import time
import random
import typing
from typing import Optional
import json
from logging import getLogger
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
REGISTERED = "registered"
ACTIVE = "active"
FINISHED = "finished"
# waiting status
THINKING = "thinking"
THINKING10 = "thinking10"
SPEAKER = "speaker"
ANSWER = "answer"
EXPIRED = "expired"


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot_worker_tasks: Optional[list[Task]] = None
        self.bot_queue = asyncio.Queue()
        self.bot_worker_number = 1
        self.logger = getLogger("bot_manager")

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
                    event_id=message["object"]["event_id"],
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
            event_id = update.object.event_id
            event = Event(user_id=user_id, peer_id=peer_id, command=command, event_id=event_id)
            try:
                await self._event_handler(event)
            except GameException as err:
                kwargs = {"text": err.text, "user_id": user_id, "peer_id": peer_id}
                if err.event_answer:
                    kwargs["event_data"] = {"type": "show_snackbar"}
                    kwargs["event_id"] = event_id
                message = Message(**kwargs)
                await self.app.store.vk_api.publish_in_sender_queue(message)
            except Exception as err:
                self.logger.info(err)
        elif update.type == 'message_new':
            text = update.object.text
            message = Message(user_id=user_id, peer_id=peer_id, text=text)
            try:
                await self._message_handler(message)
            except GameException as err:
                kwargs = {"text": err.text, "user_id": user_id, "peer_id": peer_id}
                if err.event_answer:
                    kwargs["event_data"] = {"type": "show_snackbar"}
                message = Message(**kwargs)
                await self.app.store.vk_api.publish_in_sender_queue(message)
            except Exception as err:
                self.logger.info(err)

    def make_message(self, text: str, peer_id: int, user_id: int = None, keyboard: dict = None):
        if keyboard is not None:
            buttons = []
            if keyboard.get("buttons") is not None:
                for button in keyboard["buttons"]:
                    _button = self.make_button(
                        {"type": "callback",
                         "payload": {"command": button["command"]},
                         "label": button["label"]},
                        color="primary",
                    )
                    buttons.append([_button])
            inline = True if keyboard.get("inline") else False
            one_time = True if keyboard.get("one_time") else False
            keyboard = json.dumps(self.build_keyboard(buttons=buttons,
                                                      inline=inline,
                                                      one_time=one_time))
        return Message(user_id=user_id, peer_id=peer_id, text=text, keyboard=keyboard)

    @staticmethod
    def build_keyboard(
            buttons: list[list[dict]],
            inline: Optional[bool] = False,
            one_time: Optional[bool] = False) -> dict:
        keyboard = {"buttons": buttons, "one_time": one_time, "inline": inline}
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
            keyboard={"buttons": [{"command": "register", "label": "Присоединиться к игре"}]}
        )

    def start_game_message(self, text, user_id: int, peer_id: int):
        return self.make_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={"buttons": [{"command": "start", "label": "Начать игру"}]}
        )

    async def _event_handler(self, event: Event):
        # retrieve info about a user by VK API
        user = await self.app.store.vk_api.get_vk_user_by_id(user_id=event.user_id)
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.app.store.game.get_game(chat_id=event.peer_id, status=ACTIVE)
        if game is not None:
            round = game.round
        if event.command == "register":
            game = await self.app.store.game.get_game(chat_id=event.peer_id, status=ACTIVE)
            if game is not None:
                raise GameException("Некорректная команда", event_answer=True)
            game = await self.app.store.game.get_game(chat_id=event.peer_id, status=REGISTERED)
            player = await self.app.store.game.get_player_by_vk_id(vk_id=event.user_id)
            players = []
            new_players = []
            if player is None:
                new_players.append({"vk_id": user["user_id"],
                                    "name": user["name"],
                                    "last_name": user["last_name"]})
            else:
                players.append(player)
            if game is None:
                # if game hasn't been created we create it
                game = await self.app.store.game.create_game(
                    chat_id=event.peer_id,
                    created_at=datetime.datetime.now(),
                    players=players,
                    new_players=new_players
                )
                text = f"{full_name}, Вы зарегистрированы. Ждем остальных участников."
                message = Message(text=text,
                                  user_id=event.user_id,
                                  peer_id=event.peer_id,
                                  event_id=event.event_id,
                                  event_data={"type": "show_snackbar"})
                await self.app.store.vk_api.publish_in_sender_queue(message)
                message = Message(text=text,
                                  user_id=event.user_id,
                                  peer_id=event.peer_id)
            # if game has been already created, we add a player to it
            else:
                players = game.players
                # if player is already added to this game, and he clicks Register button again
                if player is not None and event.user_id in [player.vk_id for player in players]:
                    text = f"{full_name}, Вы уже зарегистрированы как участник в этой игре. " \
                        # "Ждём подключения остальных участников..."

                    message = Message(text=text,
                                      user_id=event.user_id,
                                      peer_id=event.peer_id,
                                      event_id=event.event_id,
                                      event_data={"type": "show_snackbar"})
                # if a player is new at all, or he was added but to another game
                else:
                    # if he is a new player at all
                    if player is None:
                        player = await self.app.store.game.create_player(vk_id=user["user_id"],
                                                                         name=user["name"],
                                                                         last_name=user["last_name"],
                                                                         games=[game])
                    # if a player is already added, but not to this game, we add him to this game
                    else:
                        link = await self.app.store.game.link_player_to_game(
                            player_id=player.id, game_id=game.id
                        )
                    # refresh game instance after adding a new player
                    game = await self.app.store.game.get_game(
                        chat_id=event.peer_id, status=REGISTERED
                    )
                    # if all players are registered for the game
                    if len(game.players) == self.app.config.game.players:
                        captain = random.choice(game.players)
                        params = {"captain": captain}
                        await self.app.store.game.update_game(id=game.id, **params)
                        text = f"{full_name}, Вы зарегистрированы. Итак, все участники в сборе. Начинаем игру. " \
                               f"Капитаном выбран: {captain.name} {captain.last_name}. " \
                               "Он будет назначать отвечающего на вопрос в каждом раунде. " \
                               "Время обсуждения вопроса - " \
                               f"{self.get_literal_time(self.app.config.game.thinking_time)}. " \
                               "Вы готовы? Капитан нажимает кнопку старта."
                        message = self.start_game_message(text=text,
                                                          user_id=captain.vk_id,
                                                          peer_id=event.peer_id)
                    else:
                        message = Message(text=f"{full_name}, Вы зарегистрированы."
                                               " Ждем остальных участников.",
                                          user_id=event.user_id,
                                          peer_id=event.peer_id)
            await self.app.store.vk_api.publish_in_sender_queue(message)
        if event.command == "start":
            chat_id = event.peer_id
            game = await self.app.store.game.get_game(chat_id=chat_id, status=REGISTERED)
            if game is None:
                raise GameException("Некорректная команда", event_answer=True)
            player = await self.app.store.game.get_player_by_vk_id(vk_id=event.user_id)
            if player is None:
                raise GameException(f"{full_name}, вы не зарегистрированы как игрок!", event_answer=True)
            captain = await self.app.store.game.get_captain(id=game.id)
            if captain is None:
                raise GameException("Капитан не назначен!")
            if captain.vk_id != player.vk_id:
                raise GameException(f"{full_name}, вы не капитан, поэтому не можете начать игру!",
                                    event_answer=True)
            params = {"status": "active"}
            await self.app.store.game.update_game(id=game.id, **params)
            if game.round == 0:
                text = "Итак, начинаем игру. На обсуждение даётся " \
                       f"{self.get_literal_time(self.app.config.game.thinking_time)}, " \
                       "после чего капитан должен выбрать игрока, " \
                       "дающего ответ на вопрос."
                message = self.make_message(text=text, user_id=event.user_id, peer_id=event.peer_id,
                                            keyboard={})
                await self.app.store.vk_api.publish_in_sender_queue(message)
            questions_ids = await self.app.store.game.get_question_ids()
            question_id = random.choice(questions_ids)
            question = await self.app.store.game.get_question(question_id)
            text = f"Вопрос номер {(game.round + 1)}. \"{question.text}\"."
            message = self.make_message(text=text, user_id=event.user_id, peer_id=event.peer_id)
            await self.app.store.vk_api.publish_in_sender_queue(message)
            text = "Время пошло!"
            message = self.make_message(text=text, user_id=event.user_id, peer_id=event.peer_id)
            await self.app.store.vk_api.publish_in_sender_queue(message)
            params = {"wait_status": "thinking", "wait_time": int(time.time())}
            await self.app.store.game.update_game(id=game.id, **params)
            await self.activate_round_timer(game_id=game.id, peer_id=event.peer_id,
                                            timer=self.app.config.game.thinking_time)
        # if event.command

    async def _message_handler(self, message: Message):
        user = await self.app.store.vk_api.get_vk_user_by_id(user_id=message.user_id)
        full_name = f'{user["name"]} {user["last_name"]}'
        text = message.text.strip().lower()
        if text == "hello":
            game = await self.app.store.game.get_game(chat_id=message.peer_id, status=ACTIVE)
            if game is not None:
                raise GameException(f"{full_name}, некорректная команда")
            game = await self.app.store.game.get_game(chat_id=message.peer_id, status=REGISTERED)
            if game is None:
                text = f"{full_name}, Добрый день! Присоединяйтесь к игре."
                message = self.create_game_message(text=text,
                                                   user_id=message.user_id,
                                                   peer_id=message.peer_id)
            else:
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

    # async def warning_send(self, text: str, user_id: int, peer_id: int):
    #     message = self.create_game_message(
    #         text=text,
    #         user_id=user_id,
    #         peer_id=peer_id
    #     )
    #     await self.app.store.vk_api.publish_in_sender_queue(message)
    #
    # async def send_goodbuy(self):
    #     games = await self.app.store.game.list_games()
    #     for game in games:
    #         chat_id = game.chat_id
    #         for player in game.players:
    #             vk_id = player.vk_id
    #             message = Message(text="Game over", peer_id=chat_id, user_id=vk_id)
    #             await self.app.store.vk_api.publish_in_sender_queue(message)

    async def activate_round_timer(self, game_id: int, peer_id: int, timer: int):
        self.round_task = {}
        task = asyncio.create_task(self.wait_and_select_speaker(
            game_id=game_id,
            peer_id=peer_id,
            timer=timer
        ))
        self.round_task[game_id] = task

    async def wait_and_select_speaker(self, game_id: int, timer: int, peer_id: int):
        await asyncio.sleep(timer)
        params = {"wait_status": "select_speaker", "wait_time": 0}
        await self.app.store.game.update_game(id=game_id, **params)
        text = f"Время вышло. Капитан, выберите отвечающего. У вас есть " \
               f"{self.get_literal_time(self.app.config.game.captain_time)}."
        message = await self.speaker_selection_message(
            game_id=game_id, peer_id=peer_id, text=text
        )
        await self.app.store.vk_api.publish_in_sender_queue(message)

    async def speaker_selection_message(self, game_id: int, peer_id: int, text: str):
        # breakpoint()
        captain = await self.app.store.game.get_captain(id=game_id)
        game = await self.app.store.game.get_game_by_id(id=game_id)
        other_players = [player for player in game.players if player.vk_id != captain.vk_id]
        buttons = [
            {"command": player.vk_id, "label": f"{player.name} {player.last_name}"}
            for player in other_players
        ]
        keyboard = {"buttons": buttons, "inline": True}
        message = self.make_message(text=text, peer_id=peer_id, keyboard=keyboard)
        return message

    @staticmethod
    def get_literal_time(t: int):
        if t <= 0:
            return "0 секунд"
        result = ""
        minutes = t // 60
        seconds = t - minutes * 60
        if minutes > 0:
            condition = minutes // 10 in range(2, 10)
            reminder = minutes - minutes // 10 * 10
            if minutes == 1 or (condition and reminder == 1):
                minute_suff = "минута"
            elif 1 < minutes < 5 or (condition and 1 < reminder < 5):
                minute_suff = "минуты"
            else:
                minute_suff = "минут"
            display_minutes = f"{minutes} {minute_suff}"
            result += display_minutes
        if seconds > 0:
            condition = seconds // 10 in range(2, 10)
            reminder = seconds - seconds // 10 * 10
            if seconds == 1 or (condition and reminder == 1):
                second_suff = "секунда"
            elif 1 < minutes < 5 or (condition and 1 < reminder < 5):
                second_suff = "секунды"
            else:
                second_suff = "секунд"
            display_seconds = f"{seconds} {second_suff}"
            result += " " + display_seconds
        return result


class GameException(Exception):
    def __init__(self, text: str, event_answer=False):
        self.text = text
        self.event_answer = event_answer

    def __str__(self):
        return str(self.text)
