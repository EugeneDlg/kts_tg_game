import asyncio
import datetime
import json
import random
import re
import time
import typing
from logging import getLogger

from app.store.bot.dataclassess import (
    Event,
    EventUpdateObject,
    Message,
    MessageUpdateObject,
    Update,
)

if typing.TYPE_CHECKING:
    from rabbitmq.rabbitmq import Rabbitmq
    from app.store.game.accessor import GameAccessor

# status
REGISTERED = "registered"
ACTIVE = "active"
FINISHED = "finished"
# waiting status
THINKING = "thinking"
THINKING10 = "thinking10"
CAPTAIN = "captain"
ANSWER = "answer"
EXPIRED = "expired"
WAIT_OK = "ok"
TOP = "top"

# commands
START = "start"
REGISTER = "register"
HELLO = "hello"
AGAIN = "again"


class BotManager:
    def __init__(self, rabbitmq: "Rabbitmq", game: "GameAccessor"):
        self.rabbitmq = rabbitmq
        self.game = game
        self.logger = getLogger("bot_manager")
        self.round_task = {}
        self.top_task = {}
        self.captain_task = {}
        self.answer_task = {}

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
                ),
            )

    async def handle_updates(self, update: Update):
        update = self.prepare_message(update)
        user_id = update.object.user_id
        peer_id = update.object.peer_id
        questions_ids = await self.game.get_question_ids()
        if len(questions_ids) == 0:
            text = "В базе данных нет вопросов! Запуск игры невозможен."
            await self.publish_message(text=text, peer_id=peer_id)
            return
        if update.type == "message_event":
            command = update.object.command
            event_id = update.object.event_id
            event = Event(
                user_id=user_id,
                peer_id=peer_id,
                command=command,
                event_id=event_id,
            )
            try:
                await self.event_handler(event)
            except GameException as err:
                kwargs = {
                    "text": err.text,
                    "user_id": user_id,
                    "peer_id": peer_id,
                }
                if err.event_answer:
                    kwargs["event_data"] = {"type": "show_snackbar"}
                    kwargs["event_id"] = event_id
                await self.publish_message(**kwargs)
            except Exception as err:
                self.logger.info(err)
        elif update.type == "message_new":
            text = update.object.text
            message = Message(user_id=user_id, peer_id=peer_id, text=text)
            try:
                await self.message_handler(message)
            except GameException as err:
                kwargs = {
                    "text": err.text,
                    "user_id": user_id,
                    "peer_id": peer_id,
                }
                await self.publish_message(**kwargs)
            except Exception as err:
                self.logger.info(err)

    def make_message(
        self,
        text: str,
        peer_id: int,
        user_id: int = None,
        keyboard: dict = None,
        event_data: dict = None,
        event_id: str = None,
    ):
        if keyboard is not None:
            buttons = []
            if keyboard.get("buttons") is not None:
                for button in keyboard["buttons"]:
                    _button = self.make_button(
                        {
                            "type": "callback",
                            "payload": {"command": button["command"]},
                            "label": button["label"],
                        },
                        color="primary",
                    )
                    buttons.append([_button])
            inline = True if keyboard.get("inline") else False
            one_time = True if keyboard.get("one_time") else False
            keyboard = json.dumps(
                self.build_keyboard(
                    buttons=buttons, inline=inline, one_time=one_time
                )
            )
        return Message(
            user_id=user_id,
            peer_id=peer_id,
            text=text,
            keyboard=keyboard,
            event_data=event_data,
            event_id=event_id,
        )

    @staticmethod
    def build_keyboard(
        buttons: list[list[dict]],
        inline: bool | None = False,
        one_time: bool | None = False,
    ) -> dict:
        keyboard = {"buttons": buttons, "one_time": one_time, "inline": inline}
        return keyboard

    @staticmethod
    def make_button(params: dict, color: str | None = None) -> dict:
        button = {"action": params}
        if color is not None:
            button["color"] = color
        return button

    async def create_game_message(self, text, user_id: int, peer_id: int):
        await self.publish_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={
                "buttons": [
                    {"command": REGISTER, "label": "Присоединиться к игре"}
                ]
            },
        )

    async def publish_start_message(self, text, user_id: int, peer_id: int):
        await self.publish_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={"buttons": [{"command": START, "label": "Начать игру"}]},
        )

    async def publish_speaker_selection_message(
        self, game_id: int, peer_id: int, text: str
    ):
        # breakpoint()
        captain = await self.game.get_captain(id=game_id)
        game = await self.game.get_game_by_id(id=game_id)
        other_players = [
            player for player in game.players if player.vk_id != captain.vk_id
        ]
        buttons = [
            {
                "command": f"speaker{player.vk_id}",
                "label": f"{player.name} {player.last_name}",
            }
            for player in other_players
        ]
        buttons.append(
            {"command": f"speaker{captain.vk_id}", "label": "Капитан"}
        )
        keyboard = {"buttons": buttons}
        await self.publish_message(
            text=text, peer_id=peer_id, keyboard=keyboard
        )

    async def next_round_message(self, peer_id: int):
        text = "Следующий раунд!"
        await self.publish_message(text=text, peer_id=peer_id, keyboard={})

    async def spin_top_message(self, peer_id: int):
        text = "Капитан, крутите волчок, чтобы выбрать вопрос"
        await self.publish_message(
            text=text,
            peer_id=peer_id,
            keyboard={"buttons": [{"command": TOP, "label": "Крутить волчок"}]},
        )

    async def publish_message(
        self,
        text: str,
        peer_id: int,
        keyboard: dict = None,
        user_id: int = None,
        event_data: dict = None,
        event_id: str = None,
    ):
        message = self.make_message(
            text=text,
            peer_id=peer_id,
            keyboard=keyboard,
            user_id=user_id,
            event_data=event_data,
            event_id=event_id,
        )
        await self.rabbitmq.publish(message.serialize())
        # await self.app.store.vk_api.publish_in_sender_queue(message)

    async def event_handler(self, event: Event):
        command = str(event.command)
        if command == REGISTER:
            await self.register_handler(event)
        if command == START:
            await self.start_handler(event)
        if "speaker" in command:
            await self.speaker_handler(event)
        if command == AGAIN:
            await self.again_game_handler(event)
        if command == TOP:
            await self.top_handler(event)

    async def message_handler(self, message: Message):
        text = message.text.strip().lower()
        if text == HELLO:
            await self.hello_message_handler(message)
        else:
            await self.answer_message_handler(message)

    async def activate_top_timer(self, game_id: int, peer_id: int):
        task = asyncio.create_task(
            self.spin_top_and_show_answer(game_id=game_id, peer_id=peer_id)
        )
        self.top_task[game_id] = task

    async def spin_top_and_show_answer(self, game_id: int, peer_id: int):
        timer = self.app.config.game.top_timer
        await asyncio.sleep(timer)
        game = await self.game.get_game_by_id(id=game_id)
        question = await self.game.get_question(
            game.current_question_id
        )
        text = f'Внимание, вопрос! "{question.text}".'
        await self.publish_message(text=text, peer_id=peer_id)
        text = "Время пошло!"
        await self.publish_message(text=text, peer_id=peer_id)
        params = {"wait_status": THINKING, "wait_time": int(time.time())}
        await self.game.update_game(id=game.id, **params)
        await self.activate_thinking_timer(game_id=game.id, peer_id=peer_id)

    async def activate_thinking_timer(self, game_id: int, peer_id: int):
        task = asyncio.create_task(
            self.think_and_choose_speaker(game_id=game_id, peer_id=peer_id)
        )
        self.round_task[game_id] = task

    async def think_and_choose_speaker(self, game_id: int, peer_id: int):
        timer = self.app.config.game.thinking_timer
        captain_timer = self.app.config.game.captain_timer
        await asyncio.sleep(timer)
        params = {"wait_status": CAPTAIN, "wait_time": 0}
        await self.game.update_game(id=game_id, **params)
        text = (
            f"Время на обсуждение вышло. Капитан, выберите отвечающего. У вас есть "
            f"{self.get_literal_time(captain_timer)}."
        )
        await self.publish_speaker_selection_message(
            game_id=game_id, peer_id=peer_id, text=text
        )
        await self.activate_captain_timer(
            game_id=game_id, peer_id=peer_id, timer=captain_timer
        )

    async def activate_captain_timer(
        self, game_id: int, peer_id: int, timer: int
    ):
        task = asyncio.create_task(
            self.wait_and_continue(
                game_id=game_id, peer_id=peer_id, timer=timer
            )
        )
        self.captain_task[game_id] = task

    async def activate_answer_timer(
        self, game_id: int, peer_id: int, timer: int
    ):
        task = asyncio.create_task(
            self.wait_and_continue(
                game_id=game_id, peer_id=peer_id, timer=timer
            )
        )
        self.answer_task[game_id] = task

    async def wait_and_continue(self, game_id: int, peer_id: int, timer: int):
        await asyncio.sleep(timer)
        game = await self.game.get_game_by_id(game_id)
        new_my_points = game.my_points + 1
        params = {
            "wait_status": EXPIRED,
            "wait_time": 0,
            "my_points": new_my_points,
        }
        await self.game.update_game(id=game_id, **params)
        text = (
            f"К сожалению, время истекло. Очко за этот раунд переходит мне. "
            f"Счёт {new_my_points}:{game.players_points}"
        )
        await self.publish_message(text=text, peer_id=peer_id, keyboard={})
        if new_my_points == self.app.config.game.max_points:
            await self.finish_game(
                game_id=game_id, peer_id=peer_id, winner="me"
            )
            return
        await self.next_round_message(peer_id=peer_id)
        await self.spin_top_message(peer_id=peer_id)

    async def before_register_handler(self, event: Event):
        user = await self.game.get_player_by_vk_id(
            vk_id=event.user_id
        )
        if user is None:
            await self.request_user_info(user_vk_id=event.user_id)
            return
        await self.register_handler(event=event)

    async def register_handler(self, event: Event):
        user = await self.game.get_player_by_vk_id(
            vk_id=event.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.game.get_game(
            chat_id=event.peer_id, status=ACTIVE
        )
        if game is not None:
            raise GameException(
                "Некорректная команда. Игра уже идёт", event_answer=True
            )
        game = await self.game.get_game(
            chat_id=event.peer_id, status=REGISTERED
        )
        player = await self.game.get_player_by_vk_id(
            vk_id=event.user_id
        )
        players = []
        new_players = []
        if player is None:
            new_players.append(
                {
                    "vk_id": user["user_id"],
                    "name": user["name"],
                    "last_name": user["last_name"],
                }
            )
        else:
            players.append(player)
        if game is None:
            # if game hasn't been created we create it
            game = await self.game.create_game(
                chat_id=event.peer_id,
                created_at=datetime.datetime.now(),
                players=players,
                new_players=new_players,
            )
            text = (
                f"{full_name}, Вы зарегистрированы. Ждем остальных участников."
            )
            await self.publish_message(
                text=text,
                user_id=event.user_id,
                peer_id=event.peer_id,
                event_id=event.event_id,
                event_data={"type": "show_snackbar"},
            )
            await self.publish_message(text=text, peer_id=event.peer_id)
        # if game has been already created, we add a player to it
        else:
            players = game.players
            # if player is already added to this game, and he clicks Register button again
            if player is not None and event.user_id in [
                player.vk_id for player in players
            ]:
                text = f"{full_name}, Вы уже зарегистрированы как участник в этой игре. "
                await self.publish_message(
                    text=text,
                    user_id=event.user_id,
                    peer_id=event.peer_id,
                    event_id=event.event_id,
                    event_data={"type": "show_snackbar"},
                )
            # if a player is new at all, or he was added but to another game
            else:
                # if he is a new player at all
                if player is None:
                    player = await self.game.create_player(
                        vk_id=user["user_id"],
                        name=user["name"],
                        last_name=user["last_name"],
                        games=[game],
                    )
                # if a player is already added, but not to this game, we add him to this game
                else:
                    await self.game.link_player_to_game(
                        player_id=player.id, game_id=game.id
                    )
                # refresh game instance after adding a new player
                game = await self.game.get_game(
                    chat_id=event.peer_id, status=REGISTERED
                )
                # if all players are registered for the game
                if len(game.players) == self.app.config.game.players:
                    captain = random.choice(game.players)
                    params = {"captain": captain}
                    await self.game.update_game(id=game.id, **params)
                    text = (
                        f"{full_name}, Вы зарегистрированы. "
                        f"Итак, все участники в сборе. Начинаем игру."
                    )
                    await self.publish_message(
                        text=text,
                        user_id=event.user_id,
                        peer_id=event.peer_id,
                        event_id=event.event_id,
                        event_data={"type": "show_snackbar"},
                    )
                    text += (
                        f" Капитаном выбран: {captain.name} {captain.last_name}. "
                        "Он будет назначать отвечающего на вопрос в каждом раунде. "
                        "Вы готовы? Капитан нажимает кнопку старта."
                    )
                    await self.publish_start_message(
                        text=text, user_id=event.user_id, peer_id=event.peer_id
                    )
                else:
                    await self.publish_message(
                        text=f"{full_name}, "
                        "Вы зарегистрированы."
                        " Ждем остальных участников.",
                        user_id=event.user_id,
                        peer_id=event.peer_id,
                        event_id=event.event_id,
                        event_data={"type": "show_snackbar"},
                    )
                    await self.publish_message(
                        text=f"{full_name}, "
                        "Вы зарегистрированы."
                        " Ждем остальных участников.",
                        peer_id=event.peer_id,
                    )

    async def request_user_info(self, user_vk_id: int):


    async def start_handler(self, event: Event):
        user = await self.app.store.vk_api.get_vk_user_by_id(
            user_id=event.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        chat_id = event.peer_id
        game = await self.game.get_game(
            chat_id=chat_id, status=REGISTERED
        )
        if game is None:
            raise GameException("Некорректная команда", event_answer=True)
        player = await self.game.get_player_by_vk_id(
            vk_id=event.user_id
        )
        if player is None:
            raise GameException(
                f"{full_name}, вы не зарегистрированы как игрок!",
                event_answer=True,
            )
        captain = await self.game.get_captain(id=game.id)
        if captain is None:
            raise GameException("Капитан не назначен!")
        if captain.vk_id != player.vk_id:
            raise GameException(
                f"{full_name}, вы не капитан, поэтому не можете начать игру!",
                event_answer=True,
            )
        params = {"status": "active"}
        await self.game.update_game(id=game.id, **params)
        if game.round == 0:
            text = (
                "Итак, начинаем игру. На обсуждение даётся "
                f"{self.get_literal_time(self.app.config.game.thinking_timer)}, "
                "после чего даётся ещё "
                f"{self.get_literal_time(self.app.config.game.captain_timer)}, в течение которых "
                f"капитан должен выбрать игрока, дающего ответ на вопрос. На ввод ответа отведено "
                f"{self.get_literal_time(self.app.config.game.answer_timer)}. "
                "Крутить волчок и выбирать отвечающего может только капитан команды. "
                f"Счёт до {self.app.config.game.max_points} очков. Первый раунд!"
            )
            await self.publish_message(
                text=text,
                user_id=event.user_id,
                peer_id=event.peer_id,
                keyboard={},
            )
        await self.spin_top_message(peer_id=event.peer_id)

    async def speaker_handler(self, event: Event):
        user = await self.app.store.vk_api.get_vk_user_by_id(
            user_id=event.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.game.get_game(
            chat_id=event.peer_id, status=ACTIVE
        )
        command = event.command
        m = re.search(r"^speaker(\d+)", command)
        speaker_id = int(m.group(1))
        speaker = await self.game.get_player_by_vk_id(speaker_id)
        if game is None:
            raise GameException("Некорректная команда.")
        if game.wait_status not in [CAPTAIN, EXPIRED]:
            return
        await self.game.delete_speaker(game_id=game.id)
        captain = await self.game.get_captain(id=game.id)
        if captain.vk_id != event.user_id:
            raise GameException(
                f"{full_name}, Вы не капитан, поэтому не можете выбирать",
                event_answer=True,
            )
        if game.wait_status == EXPIRED:
            raise GameException(
                "К сожалению, время истекло. Вы не успели ответить."
            )
        if game.wait_status == CAPTAIN:
            self.captain_task[game.id].cancel()
            captain_title = " капитан" if captain.vk_id == speaker.vk_id else ""
            text = (
                f"На вопрос отвечает{captain_title} {speaker.name} {speaker.last_name}. "
                f"На ответ у вас есть {self.get_literal_time(self.app.config.game.answer_timer)}"
            )
            await self.publish_message(
                text=text, peer_id=event.peer_id, keyboard={}
            )
            params = {"wait_status": ANSWER, "wait_time": 0, "speaker": speaker}
            await self.game.update_game(id=game.id, **params)
            await self.activate_answer_timer(
                game_id=game.id,
                peer_id=event.peer_id,
                timer=self.app.config.game.answer_timer,
            )

    async def again_game_handler(self, event):
        text = "Идёт регистрация участников игры"
        keyboard = {
            "buttons": [{"command": REGISTER, "label": "Присоединиться к игре"}]
        }
        await self.publish_message(
            text=text, peer_id=event.peer_id, keyboard=keyboard
        )

    async def top_handler(self, event: Event):
        user = await self.app.store.vk_api.get_vk_user_by_id(
            user_id=event.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.game.get_game(
            chat_id=event.peer_id, status=ACTIVE
        )
        round_ = game.round
        captain = await self.game.get_captain(id=game.id)
        if captain.vk_id != event.user_id:
            raise GameException(
                f"{full_name}, Вы не капитан, поэтому не можете крутить волчок",
                event_answer=True,
            )
        round_ += 1
        params = {"wait_status": WAIT_OK, "wait_time": 0, "round": round_}
        await self.game.update_game(id=game.id, **params)
        questions_ids = await self.game.get_question_ids()
        question_id = random.choice(questions_ids)
        params = {"current_question_id": question_id}
        await self.game.update_game(id=game.id, **params)
        await self.game.mark_question_as_used(
            game_id=game.id, question_id=question_id
        )
        await self.publish_message(
            text="Волчок выбирает вопрос...", peer_id=event.peer_id, keyboard={}
        )
        await self.activate_top_timer(game_id=game.id, peer_id=event.peer_id)

    async def hello_message_handler(self, message: Message):
        user = await self.app.store.vk_api.get_vk_user_by_id(
            user_id=message.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.game.get_game(
            chat_id=message.peer_id, status=ACTIVE
        )
        if game is not None:
            raise GameException(
                f"{full_name}, некорректная команда. Игра уже идёт."
            )
        game = await self.game.get_game(
            chat_id=message.peer_id, status=REGISTERED
        )
        if game is None:
            text = f"{full_name}, Добрый день! Присоединяйтесь к игре."
            await self.create_game_message(
                text=text, user_id=message.user_id, peer_id=message.peer_id
            )
        else:
            players = game.players
            if message.user_id in [player.vk_id for player in players]:
                text = (
                    f"{full_name}, Вы уже зарегистрированы как участник в этой игре. "
                    "Ждём подключения остальных участников..."
                )
                await self.publish_message(
                    text=text, user_id=message.user_id, peer_id=message.peer_id
                )
            else:
                players = [
                    f"{player.name} {player.last_name}"
                    for player in game.players
                ]
                players = " ,".join(players)
                text = (
                    f"{full_name}, идёт регистрация участников игры. "
                    "Хотите зарегистрироваться? "
                    "С нами следующие игроки: " + players
                )
                await self.publish_message(
                    text=text, user_id=message.user_id, peer_id=message.peer_id
                )

    async def answer_message_handler(self, message):
        text = message.text.strip().lower()
        user = await self.app.store.vk_api.get_vk_user_by_id(
            user_id=message.user_id
        )
        full_name = f'{user["name"]} {user["last_name"]}'
        game = await self.game.get_game(
            chat_id=message.peer_id, status=ACTIVE
        )
        if game is None:
            raise GameException(f"{full_name}, некорректная команда.")
        if game.wait_status == THINKING:
            reminder = (
                game.wait_time
                + self.app.config.game.thinking_timer  # type: ignore # noqa: E711
                - int(time.time())  # type: ignore # noqa: E711
            )
            raise GameException(
                f"{full_name}, ещё идёт обсуждение. Осталось {self.get_literal_time(reminder)}"
            )
        if game.wait_status not in [ANSWER, EXPIRED]:
            return
        speaker = await self.game.get_speaker(id=game.id)
        current_question = await self.game.get_question(
            game.current_question_id
        )
        if speaker.vk_id != message.user_id:
            raise GameException(
                f"{full_name}, Вы не назначены отвечающим на вопрос"
            )
        if game.wait_status == EXPIRED:
            raise GameException(
                "К сожалению, время истекло. Вы не успели ответить."
            )
        if game.wait_status == ANSWER:
            self.answer_task[game.id].cancel()
            params = {"wait_status": WAIT_OK, "wait_time": 0}
            await self.game.update_game(id=game.id, **params)
            if text not in current_question.answer[0].text.lower():
                new_my_points = game.my_points + 1
                params = {"my_points": new_my_points}
                await self.game.update_game(id=game.id, **params)
                text = (
                    f"К сожалению, вы ответили неправильно. Очко за этот раунд переходит мне. "
                    f"Счёт {new_my_points}:{game.players_points}"
                )
                await self.publish_message(text=text, peer_id=message.peer_id)
                if new_my_points == self.app.config.game.max_points:
                    await self.finish_game(
                        game_id=game.id, peer_id=message.peer_id, winner="me"
                    )
                    return
            else:
                new_your_points = game.players_points + 1
                params = {"players_points": new_your_points}
                await self.game.update_game(id=game.id, **params)
                await self.update_score(game_id=game.id)
                text = (
                    f"Вы совершенно правы!. Очко за этот раунд достаётся вам. "
                    f"Счёт {game.my_points}:{new_your_points}"
                )
                await self.publish_message(text=text, peer_id=message.peer_id)
                if new_your_points == self.app.config.game.max_points:
                    await self.finish_game(
                        game_id=game.id, peer_id=message.peer_id, winner="you"
                    )
                    return
            await self.next_round_message(peer_id=message.peer_id)
            await self.spin_top_message(peer_id=message.peer_id)

    async def finish_game(self, game_id: int, peer_id: int, winner: str):
        game = await self.game.get_game_by_id(id=game_id)
        params = {"status": FINISHED}
        await self.game.update_game(id=game_id, **params)
        await self.game.unmark_questions_as_used(game_id=game_id)
        scores = ""
        for player in game.players:
            points = await self.game.get_total_score(
                player_id=player.id
            )
            scores += f"{player.name} {player.last_name} - {points}; "
        scores_text = (
            f"Итоговый счёт {game.my_points}:{game.players_points}. "
            f" Счёт по игрокам: {scores}"
        )
        if winner == "me":
            text = (
                "Вы проиграли! Надеюсь, в следующий раз вам повезёт. "
                + scores_text  # type: ignore # noqa: E711
            )
            await self.publish_message(text=text, peer_id=peer_id, keyboard={})
        elif winner == "you":
            text = "Вы выиграли! Искренне поздравляю! " + scores_text
            await self.publish_message(text=text, peer_id=peer_id, keyboard={})
        else:
            text = "Победила дружба:) Игра закончилась вничью. " + scores_text
            await self.publish_message(text=text, peer_id=peer_id, keyboard={})
        text = "Хотите ли сыграть ещё?"
        await self.publish_message(
            text=text,
            peer_id=peer_id,
            keyboard={"buttons": [{"command": AGAIN, "label": "Играть ещё"}]},
        )

    async def update_score(self, game_id: int):
        game = await self.game.get_game_by_id(id=game_id)
        for player in game.players:
            await self.game.update_player_score(
                player_id=player.id, game_id=game_id
            )

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
            elif 1 < seconds < 5 or (condition and 1 < reminder < 5):
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
