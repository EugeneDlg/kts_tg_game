import asyncio
import datetime
import json
import random
import re
import time
import typing
import logging
from logging import getLogger

from apps.bot.dataclassess import (
    Event,
    EventUpdateObject,
    InfoUpdateObject,
    Message,
    MessageUpdateObject,
    Update,
)
from apps.bot.enum import Command, Status, UpdateType

if typing.TYPE_CHECKING:
    from apps.game.accessor.accessor import GameAccessor
    from rabbitmq.rabbitmq import Rabbitmq

BLITZ_THINKING_FACTOR = 2
BLITZ_CAPTAIN_FACTOR = 2
BLITZ_ANSWER_FACTOR = 2


class BotManager:
    def __init__(self, rabbitmq: "Rabbitmq", game: "GameAccessor"):
        self.rabbitmq = rabbitmq
        self.game = game
        self.logger = getLogger("bot_manager")
        logging.basicConfig(level=logging.INFO)
        self.round_task = {}
        self.top_task = {}
        self.captain_task = {}
        self.answer_task = {}

    async def handle_updates(self, update: Update):
        """
        The intro handle method for all incoming updates
        :param update:
        :return:
        """
        update = self.deserialize(update)
        if update is None:
            return
        # processes VK user info response
        if update.type == UpdateType.vk_request:
            vk_user_request = update.object.vk_user_request
            name = update.object.name
            last_name = update.object.last_name
            peer_id = update.object.peer_id
            event_id = update.object.event_id
            message = Message(
                vk_user_request=vk_user_request,
                name=name,
                last_name=last_name,
                peer_id=peer_id,
                event_id=event_id,
            )
            await self.user_info_handler(message)
            return
        # processes an event message from chat
        user_id = update.object.user_id
        peer_id = update.object.peer_id
        if update.type == UpdateType.message_event:
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
                return
            except Exception as err:
                self.logger.info(err)
        # processes a new message from chat
        elif update.type == UpdateType.new_message:
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
                return
            except Exception as err:
                self.logger.info(err)

    async def event_handler(self, event: Event):
        command = str(event.command)
        if command == Command.register["command"]:
            await self.before_register_handler(event)
        if command == Command.start["command"]:
            await self.start_handler(event)
        if Command.speaker["command"] in command:
            await self.speaker_handler(event)
        if command == Command.again["command"]:
            await self.again_game_handler(event)
        if command == Command.top["command"]:
            await self.top_handler(event)

    async def message_handler(self, message: Message):
        text = message.text.strip().lower()
        if text == Command.hello["command"]:
            await self.hello_message_handler(message)
        elif text == Command.help["command"]:
            await self.help_message_handler(message)
        elif text == Command.scores["command"]:
            await self.scores_message_handler(message)
        elif text == Command.finish["command"]:
            await self.finish_message_handler(message)
        else:
            await self.answer_message_handler(message)

    async def user_info_handler(self, message: Message):
        """
        Requests information about a user from VK and proceeds game register process.
        It is used only for registering in a game
        :param message:
        :return:
        """
        vk_id = message.vk_user_request
        name = message.name
        last_name = message.last_name
        event_id = message.event_id
        peer_id = message.peer_id
        command = Command.register["command"]
        player = await self.game.create_player(
            vk_id=vk_id, name=name, last_name=last_name, games=[]
        )
        event = Event(
            event_id=event_id, user_id=vk_id, peer_id=peer_id, command=command
        )
        await self.register_handler(event=event)

    async def before_register_handler(self, event: Event):
        user = await self.game.get_player(vk_id=event.user_id)
        if user is None:
            await self.request_user_info(event=event)
            return
        await self.register_handler(event=event)

    async def register_handler(self, event: Event):
        user = player = await self.game.get_player(vk_id=event.user_id)
        full_name = f"{user.name} {user.last_name}"
        game = await self.game.get_game(
            chat_id=event.peer_id, status=Status.active
        )
        if game is not None:
            raise GameException(
                "Некорректная команда. Игра уже идёт", event_answer=True
            )
        game = await self.game.get_game(
            chat_id=event.peer_id, status=Status.registered.value
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
            rest_players = self.rabbitmq.config.game.players - 1
            text = (
                f"{full_name}, Вы зарегистрированы. Ждем остальных участников. "
            )
            await self.publish_message(
                text=text,
                user_id=event.user_id,
                peer_id=event.peer_id,
                event_id=event.event_id,
                event_data={"type": "show_snackbar"},
            )
            await asyncio.sleep(1)
            text = (
                f"{full_name}, Вы зарегистрированы. Ждем остальных участников. "
                "Для начала игры не хватает "
                f"ещё {self.get_word_players(rest_players)}"
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
                game = await self.game.get_game(
                    chat_id=event.peer_id, status=Status.registered.value
                )
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
                    chat_id=event.peer_id, status=Status.registered
                )
                # if all players are registered for the game
                if len(game.players) == self.rabbitmq.config.game.players:
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
                    rest_players = self.rabbitmq.config.game.players - len(
                        game.players
                    )
                    await self.publish_message(
                        text=f"{full_name}, "
                        "Вы зарегистрированы. "
                        "Ждем остальных участников.",
                        user_id=event.user_id,
                        peer_id=event.peer_id,
                        event_id=event.event_id,
                        event_data={"type": "show_snackbar"},
                    )
                    await self.publish_message(
                        text=f"{full_name}, "
                        "Вы зарегистрированы."
                        " Ждем остальных участников. Для начала игры не хватает "
                        f"ещё {self.get_word_players(rest_players)}",
                        peer_id=event.peer_id,
                    )

    async def start_handler(self, event: Event):
        user = await self.game.get_player(vk_id=event.user_id)
        full_name = f"{user.name} {user.last_name}"
        chat_id = event.peer_id
        game = await self.game.get_game(
            chat_id=chat_id, status=Status.registered.value
        )
        if game is None:
            raise GameException("Некорректная команда", event_answer=True)
        player = await self.game.get_player(vk_id=event.user_id)
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
            text = "Капитан, начинаем игру"
            await self.publish_message(
                text=text,
                user_id=event.user_id,
                peer_id=event.peer_id,
                event_id=event.event_id,
                event_data={"type": "show_snackbar"},
            )
            await asyncio.sleep(1)
            text = (
                "Итак, начинаем игру. На обсуждение даётся "
                f"{self.get_word_time(self.rabbitmq.config.game.thinking_timer)}, "
                "после чего даётся ещё "
                f"{self.get_word_time(self.rabbitmq.config.game.captain_timer)}, в течение которых "
                f"капитан должен выбрать игрока, дающего ответ на вопрос. На ввод ответа отведено "
                f"{self.get_word_time(self.rabbitmq.config.game.answer_timer)}. "
                "Крутить волчок и выбирать отвечающего может только капитан команды. "
                f"Счёт до {self.rabbitmq.config.game.max_points} очков. Первый раунд!"
            )
            await self.publish_message(
                text=text, user_id=event.user_id, peer_id=event.peer_id
            )

        await self.spin_top_message(peer_id=event.peer_id)

    async def speaker_handler(self, event: Event):
        user = await self.game.get_player(vk_id=event.user_id)
        full_name = f"{user.name} {user.last_name}"
        game = await self.game.get_game(
            chat_id=event.peer_id, status=Status.active
        )
        if game is None:
            raise GameException("Некорректная команда.")
        command = event.command
        m = re.search(r"^speaker(\d+)", command)
        speaker_id = int(m.group(1))
        speaker = await self.game.get_player(speaker_id)
        if game.wait_status not in [Status.captain.value, Status.expired.value]:
            return
        await self.game.delete_speaker(game_id=game.id)
        captain = await self.game.get_captain(id=game.id)
        if captain.vk_id != event.user_id:
            raise GameException(
                f"{full_name}, Вы не капитан, поэтому не можете выбирать",
                event_answer=True,
            )
        # this verification is just for sure. We should not get here normally
        if game.wait_status == Status.expired:
            raise GameException(
                "К сожалению, время истекло. Вы не успели ответить."
            )
        if game.wait_status == Status.captain:
            factor = BLITZ_ANSWER_FACTOR if game.blitz_round > 0 else 1
            self.captain_task[game.id].cancel()
            captain_title = " капитан" if captain.vk_id == speaker.vk_id else ""
            text = (
                f"На вопрос отвечает{captain_title} {speaker.name} {speaker.last_name}. "
                "На ответ у вас есть "
                f"{self.get_word_time(self.rabbitmq.config.game.answer_timer // factor)}"
            )
            await self.publish_message(
                text=text, peer_id=event.peer_id, keyboard={}
            )
            params = {
                "wait_status": Status.answer,
                "wait_time": 0,
                Command.speaker["command"]: speaker,
            }
            await self.game.update_game(id=game.id, **params)
            await self.activate_answer_timer(
                game_id=game.id,
                peer_id=event.peer_id,
                timer=self.rabbitmq.config.game.answer_timer // factor,
            )

    async def top_handler(self, event: Event):
        game = await self.game.get_game(
            chat_id=event.peer_id, status=Status.active
        )
        if game is None:
            GameException("Некорректная команда")
        await self.verify_questions(game_id=game.id)
        user = await self.game.get_player(vk_id=event.user_id)
        full_name = f"{user.name} {user.last_name}"
        round_ = game.round
        captain = await self.game.get_captain(id=game.id)
        if captain.vk_id != event.user_id:
            raise GameException(
                f"{full_name}, Вы не капитан, поэтому не можете крутить волчок",
                event_answer=True,
            )
        round_ += 1
        params = {
            "wait_status": Status.wait_ok.value,
            "wait_time": 0,
            "round": round_,
        }
        await self.game.update_game(id=game.id, **params)
        await self.publish_message(
            text="Волчок выбирает вопрос...", peer_id=event.peer_id, keyboard={}
        )
        await self.activate_top_timer(game_id=game.id, peer_id=event.peer_id)

    async def hello_message_handler(self, message: Message):
        await self.verify_questions()
        game = await self.game.get_game(
            chat_id=message.peer_id, status=Status.active
        )
        if game is not None:
            raise GameException("Некорректная команда. Игра уже идёт.")
        game = await self.game.get_game(
            chat_id=message.peer_id, status=Status.registered
        )
        if game is None:
            text = "Добрый день! Присоединяйтесь к игре."
            await self.register_game_message(
                text=text, user_id=message.user_id, peer_id=message.peer_id
            )
        else:
            players = game.players
            user = await self.game.get_player(vk_id=message.user_id)
            full_name = f"{user.name} {user.last_name}"
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
                    "Идёт регистрация участников игры. "
                    "Хотите зарегистрироваться? "
                    "С нами следующие игроки: " + players
                )
                await self.register_game_message(
                    text=text, user_id=message.user_id, peer_id=message.peer_id
                )

    async def answer_message_handler(self, message):
        text = message.text.strip().lower()
        user = await self.game.get_player(vk_id=message.user_id)
        if user is None:
            raise GameException(f"Некорректная команда.")
        full_name = f"{user.name} {user.last_name}"
        game = await self.game.get_game(
            chat_id=message.peer_id, status=Status.active.value
        )
        if game is None:
            raise GameException(f"{full_name}, некорректная команда.")
        if game.wait_status == Status.thinking:
            factor = BLITZ_THINKING_FACTOR if game.blitz_round > 0 else 1
            reminder = (
                game.wait_time
                + self.rabbitmq.config.game.thinking_timer // factor  # type: ignore # noqa: E711
                - int(time.time())  # type: ignore # noqa: E711
            )
            raise GameException(
                f"{full_name}, ещё идёт обсуждение. Осталось {self.get_word_time(reminder)}"
            )
        if game.wait_status not in [Status.answer, Status.expired]:
            return
        speaker = await self.game.get_speaker(id=game.id)
        current_question = await self.game.get_question(
            game.current_question_id
        )
        if speaker.vk_id != message.user_id:
            raise GameException(
                f"{full_name}, Вы не назначены отвечающим на вопрос"
            )
        ###
        if game.wait_status == Status.expired:
            raise GameException(
                "К сожалению, время истекло. Вы не успели ответить."
            )
        if game.wait_status == Status.answer:
            self.answer_task[game.id].cancel()
            params = {"wait_status": Status.wait_ok, "wait_time": 0}
            await self.game.update_game(id=game.id, **params)
            if text not in current_question.answer[0].text.lower():
                new_my_points = game.my_points + 1
                params = {"my_points": new_my_points, "blitz_round": 0}
                await self.game.update_game(id=game.id, **params)
                blitz_text = (
                    "Вы проиграли этот блиц. " if game.blitz_round > 0 else ""
                )
                text = (
                    f"К сожалению, вы ответили неправильно. {blitz_text}Очко за этот раунд переходит мне. "
                    f"Счёт {new_my_points}:{game.players_points}"
                )
                await self.publish_message(text=text, peer_id=message.peer_id)
                if new_my_points == self.rabbitmq.config.game.max_points:
                    await self.finish_game(
                        game_id=game.id, peer_id=message.peer_id, winner="me"
                    )
                    return
            else:
                blitz_text = ""
                if game.blitz_round > 0:
                    if game.blitz_round < 3:
                        text = "Вы правы! Блиц продолжается."
                        await self.publish_message(
                            text=text, peer_id=message.peer_id
                        )
                        await asyncio.sleep(2)
                        await self.proceed_blitz(
                            game_id=game.id, peer_id=message.peer_id
                        )
                        return
                    blitz_text = "Вы выиграли этот блиц! "
                    params = {"blitz_round": 0}
                    await self.game.update_game(id=game.id, **params)
                new_your_points = game.players_points + 1
                params = {"players_points": new_your_points}
                await self.game.update_game(id=game.id, **params)
                await self.update_score(game_id=game.id)
                text = (
                    f"Вы совершенно правы!. {blitz_text}Очко за этот раунд достаётся вам. "
                    f"Счёт {game.my_points}:{new_your_points}"
                )
                await self.publish_message(text=text, peer_id=message.peer_id)
                if new_your_points == self.rabbitmq.config.game.max_points:
                    await self.finish_game(
                        game_id=game.id, peer_id=message.peer_id, winner="you"
                    )
                    return
            await asyncio.sleep(2)
            await self.next_round_message(peer_id=message.peer_id)
            await asyncio.sleep(1)
            await self.spin_top_message(peer_id=message.peer_id)

    async def help_message_handler(self, message: Message):
        text = (
            "Приветствую вас в игре 'Что? Где? Когда?'\N{winking face}\n Играет команда знатоков "
            f"(в составе {self.rabbitmq.config.game.players} человек) против ведущего. "
            f"Игра ведётся до {self.rabbitmq.config.game.max_points} очков. "
            f"На обдумывание и обсуждение вопросов даётся "
            f"{self.get_word_time(self.rabbitmq.config.game.thinking_timer)}, "
            f"после чего капитан должен выбрать игрока, отвечающего на вопрос. На это капитану даётся "
            f"{self.get_word_time(self.rabbitmq.config.game.captain_timer)}. На ввод ответа у игрока есть "
            f"{self.get_word_time(self.rabbitmq.config.game.answer_timer)}. Так же волчок может выбрать сектор блиц, "
            f"где предлагается ответить на 3 более простых вопроса, но время обсуждения и ответа в два раза меньше. "
            f"Для регистрации в игре наберите '/hello'. Для просмотра счёта по игрокам '/scores'. Удачи в игре!"
        )
        await self.publish_message(text=text, peer_id=message.peer_id)

    async def scores_message_handler(self, message: Message):
        players = await self.game.list_players_by_game()
        if players is None or len(players) == 0:
            text = "В базе данных пока нет игроков"
        else:
            text = "Счёт по всем игрокам по всем играм: "
            for player in players:
                points = await self.game.get_total_score(player_id=player.id)
                text += f"{player.name} {player.last_name} - {points};  "
        await self.publish_message(text=text, peer_id=message.peer_id)

    async def finish_message_handler(self, message: Message):
        game = await self.game.get_game(
            chat_id=message.peer_id, status=Status.registered
        )
        if game is not None:
            await self._finish_game_procedure(game_id=game.id)
            text = "Игра завершена вручную"
        else:
            game = await self.game.get_game(
                chat_id=message.peer_id, status=Status.active
            )
            if game is not None:
                captain = await self.game.get_captain(game.id)
                if message.user_id != captain.vk_id:
                    text = "Только капитан может завершить игру"
                else:
                    await self._finish_game_procedure(game_id=game.id)
                    text = "Игра завершена вручную"
            else:
                text = "Игра для завершения не найдена"
        await self.publish_message(text=text, peer_id=message.peer_id, keyboard={})

    async def again_game_handler(self, event):
        """
        Used when the game is over and a user wants to start one more time
        :param event:
        :return:
        """
        text = f"Играем ещё раз"
        await self.publish_message(
            text=text,
            user_id=event.user_id,
            peer_id=event.peer_id,
            event_id=event.event_id,
            event_data={"type": "show_snackbar"},
        )
        await asyncio.sleep(1)
        text = "Идёт регистрация участников игры"
        keyboard = {
            "buttons": [
                {
                    "command": Command.register["command"],
                    "label": Command.register["label"],
                }
            ]
        }
        await self.publish_message(
            text=text, peer_id=event.peer_id, keyboard=keyboard
        )

    async def activate_top_timer(self, game_id: int, peer_id: int):
        """
        Creates acyncio task for spinning the top
        :param game_id:
        :param peer_id:
        :return:
        """
        task = asyncio.create_task(
            self.spin_top(game_id=game_id, peer_id=peer_id)
        )
        self.top_task[game_id] = task

    async def spin_top(self, game_id: int, peer_id: int):
        """
        Spins the spinning top to choose a sector
        :param game_id:
        :param peer_id:
        :return:
        """
        timer = self.rabbitmq.config.game.top_timer
        await asyncio.sleep(timer)
        is_blitz = await self.choose_sector()
        if is_blitz:
            await self.start_blitz(game_id=game_id, peer_id=peer_id)
            return
        await self.choose_question(game_id)
        game = await self.game.get_game_by_id(id=game_id)
        question = await self.game.get_question(game.current_question_id)
        text = f'Внимание, вопрос! "{question.text}".'
        await self.publish_message(text=text, peer_id=peer_id)
        await asyncio.sleep(2)
        text = "Время пошло!"
        await self.publish_message(text=text, peer_id=peer_id)
        params = {"wait_status": Status.thinking, "wait_time": int(time.time())}
        await self.game.update_game(id=game.id, **params)
        await self.activate_thinking_timer(game_id=game_id, peer_id=peer_id)

    async def activate_thinking_timer(self, game_id: int, peer_id: int):
        """
        Creates asyncio task when the top has chosen a sector and a question and so
        the players are thinking and discussing the question
        :param game_id:
        :param peer_id:
        :return:
        """
        task = asyncio.create_task(
            self.think_and_choose_speaker(game_id=game_id, peer_id=peer_id)
        )
        self.round_task[game_id] = task

    async def think_and_choose_speaker(self, game_id: int, peer_id: int):
        """
        The players are thinking and discussing the question
        :param game_id:
        :param peer_id:
        :return:
        """
        game = await self.game.get_game_by_id(game_id)
        captain_timer = self.rabbitmq.config.game.captain_timer
        thinking_timer = self.rabbitmq.config.game.thinking_timer
        if game.blitz_round > 0:
            thinking_timer //= BLITZ_THINKING_FACTOR
            captain_timer //= BLITZ_THINKING_FACTOR
        await asyncio.sleep(thinking_timer)
        self.round_task[game_id] = None
        params = {"wait_status": Status.captain.value, "wait_time": 0}
        await self.game.update_game(id=game_id, **params)
        text = (
            f"Время на обсуждение вышло. Капитан, выберите отвечающего. У вас есть "
            f"{self.get_word_time(captain_timer)}."
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
        """
        Creates a task for captain choosing a speaker
        :param game_id:
        :param peer_id:
        :param timer:
        :return:
        """
        task = asyncio.create_task(
            self.wait_and_continue(
                game_id=game_id, peer_id=peer_id, timer=timer
            )
        )
        self.captain_task[game_id] = task

    async def activate_answer_timer(
        self, game_id: int, peer_id: int, timer: int
    ):
        """
        Creates a task for answering a question
        :param game_id:
        :param peer_id:
        :param timer:
        :return:
        """
        task = asyncio.create_task(
            self.wait_and_continue(
                game_id=game_id, peer_id=peer_id, timer=timer
            )
        )
        self.answer_task[game_id] = task

    async def wait_and_continue(self, game_id: int, peer_id: int, timer: int):
        """
        Waits while a speaker is entering an answer
        and finish a round after it expires
        :param game_id:
        :param peer_id:
        :param timer:
        :return:
        """
        await asyncio.sleep(timer)
        game = await self.game.get_game_by_id(game_id)
        new_my_points = game.my_points + 1
        params = {
            "wait_status": Status.expired.value,
            "wait_time": 0,
            "my_points": new_my_points,
            "blitz_round": 0,
        }
        await self.game.update_game(id=game_id, **params)
        text = (
            f"К сожалению, время истекло. Очко за этот раунд переходит мне. "
            f"Счёт {new_my_points}:{game.players_points}"
        )
        await self.publish_message(text=text, peer_id=peer_id, keyboard={})
        if new_my_points == self.rabbitmq.config.game.max_points:
            await self.finish_game(
                game_id=game_id, peer_id=peer_id, winner="me"
            )
            return
        await asyncio.sleep(2)
        await self.next_round_message(peer_id=peer_id)
        await asyncio.sleep(1)
        await self.spin_top_message(peer_id=peer_id)

    def make_message(
        self,
        text: str,
        peer_id: int,
        user_id: int = None,
        keyboard: dict = None,
        event_data: dict = None,
        event_id: str = None,
        vk_user_request: int = None,
    ):
        """
        Makes an outgoing message to publish
        :param text:
        :param peer_id:
        :param user_id:
        :param keyboard:
        :param event_data:
        :param event_id:
        :param vk_user_request:
        :return:
        """
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
            vk_user_request=vk_user_request,
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

    async def register_game_message(self, text, user_id: int, peer_id: int):
        await self.publish_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={
                "buttons": [
                    {
                        "command": Command.register["command"],
                        "label": Command.register["label"],
                    }
                ]
            },
        )

    async def publish_start_message(self, text, user_id: int, peer_id: int):
        await self.publish_message(
            text=text,
            user_id=user_id,
            peer_id=peer_id,
            keyboard={
                "buttons": [
                    {
                        "command": Command.start["command"],
                        "label": Command.start["label"],
                    }
                ]
            },
        )

    async def publish_speaker_selection_message(
        self, game_id: int, peer_id: int, text: str
    ):
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
        await self.publish_message(text=text, peer_id=peer_id)

    async def spin_top_message(self, peer_id: int):
        text = "Капитан, крутите волчок, чтобы выбрать вопрос"
        await self.publish_message(
            text=text,
            peer_id=peer_id,
            keyboard={
                "buttons": [
                    {
                        "command": Command.top["command"],
                        "label": Command.top["label"],
                    }
                ]
            },
        )

    async def publish_message(
        self,
        text: str = None,
        peer_id: int = None,
        keyboard: dict = None,
        user_id: int = None,
        event_data: dict = None,
        event_id: str = None,
        vk_user_request: int = None,
    ):
        message = self.make_message(
            text=text,
            peer_id=peer_id,
            keyboard=keyboard,
            user_id=user_id,
            event_data=event_data,
            event_id=event_id,
            vk_user_request=vk_user_request,
        )
        await self.rabbitmq.publish(message.serialize())
        # await self.app.store.vk_api.publish_in_sender_queue(message)

    async def finish_game(self, game_id: int, peer_id: int, winner: str):
        game = await self.game.get_game_by_id(id=game_id)
        await self._finish_game_procedure(game_id)
        scores = await self.get_all_players_scores(game_id)
        scores_text = (
            f"Итоговый счёт {game.my_points}:{game.players_points}. "
            f" Счёт по игрокам: {scores}"
        )
        if winner == "me":
            text = (
                "Вы проиграли! Надеюсь, в следующий раз вам повезёт. "
                + scores_text  # type: ignore # noqa: E711
            )
            await self.publish_message(text=text, peer_id=peer_id)
        elif winner == "you":
            text = "Вы выиграли!!! Искренне поздравляю! " + scores_text
            await self.publish_message(text=text, peer_id=peer_id)
        else:
            text = "Победила дружба:) Игра закончилась вничью. " + scores_text
            await self.publish_message(text=text, peer_id=peer_id)
        await asyncio.sleep(2)
        text = "Хотите ли сыграть ещё?"
        await self.publish_message(
            text=text,
            peer_id=peer_id,
            keyboard={
                "buttons": [
                    {
                        "command": Command.again["command"],
                        "label": Command.again["label"],
                    }
                ]
            },
        )

    async def _finish_game_procedure(
        self,
        game_id: int,
    ):
        params = {"status": Status.finished}
        await self.game.update_game(id=game_id, **params)
        await self.game.unmark_questions_as_used(game_id=game_id)

    async def get_all_players_scores(self, game_id: int) -> str:
        game = await self.game.get_game_by_id(id=game_id)
        scores = ""
        for player in game.players:
            points = await self.game.get_total_score(player_id=player.id)
            scores += f"{player.name} {player.last_name} - {points}; "
        return scores

    async def request_user_info(self, event: Event):
        await self.publish_message(
            vk_user_request=event.user_id,
            peer_id=event.peer_id,
            event_id=event.event_id,
        )

    @staticmethod
    async def choose_sector():
        seq = [True]
        seq.extend([False] * 2)
        is_blitz = random.choice(seq)
        return is_blitz

    async def choose_question(self, game_id, blitz: bool = False):
        questions_ids = await self.game.get_question_ids(game_id=game_id, blitz=blitz)
        question_id = random.choice(questions_ids)
        params = {"current_question_id": question_id}
        await self.game.update_game(id=game_id, **params)
        await self.game.mark_question_as_used(
            game_id=game_id, question_id=question_id
        )

    async def start_blitz(self, game_id: int, peer_id: int):
        game = await self.game.get_game_by_id(id=game_id)
        text = (
            "Вам выпал блиц! Вам предстоит ответить на 3 вопроса, "
            f"{self.get_word_time(self.rabbitmq.config.game.thinking_timer // BLITZ_THINKING_FACTOR)}"
            " обсуждения каждый. Капитан выбирает отвечающего на каждый вопрос."
        )
        await self.publish_message(text=text, peer_id=peer_id)
        await asyncio.sleep(4)
        await self.proceed_blitz(game_id=game_id, peer_id=peer_id)

    async def proceed_blitz(self, game_id: int, peer_id: int):
        await self.choose_question(game_id, blitz=True)
        game = await self.game.get_game_by_id(game_id)
        params = {"blitz_round": game.blitz_round + 1}
        await self.game.update_game(id=game_id, **params)
        question = await self.game.get_question(game.current_question_id)
        text = f'Внимание, блиц-вопрос номер {game.blitz_round + 1}! "{question.text}".'
        await self.publish_message(text=text, peer_id=peer_id)
        await asyncio.sleep(2)
        text = "Время пошло!"
        await self.publish_message(text=text, peer_id=peer_id)
        params = {"wait_status": Status.thinking, "wait_time": int(time.time())}
        await self.game.update_game(id=game.id, **params)
        await self.activate_thinking_timer(game_id=game.id, peer_id=peer_id)

    async def update_score(self, game_id: int):
        game = await self.game.get_game_by_id(id=game_id)
        for player in game.players:
            await self.game.update_player_score(
                player_id=player.id, game_id=game_id
            )

    async def verify_questions(self, game_id: int = None):
        questions_ids = await self.game.get_question_ids(game_id=game_id)
        questions_blitz_ids = await self.game.get_question_ids(game_id=game_id, blitz=True)
        if len(questions_ids) == 0:
            text = (
                "В базе данных нет вопросов! Продолжение игры невозможно. "
                "Нужно добавить вопросы."
            )
            GameException(text)
        if len(questions_blitz_ids) < 3:
            text = (
                "В базе данных нет вопросов для блица! Продолжение игры невозможно. "
                "Нужно добавить вопросы."
            )
            GameException(text)

    @staticmethod
    def get_word_time(t: int) -> str:
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

    @staticmethod
    def get_word_players(num: int) -> str:
        if num == 1:
            return "одного участника"
        return f"{num} участников"

    @staticmethod
    def deserialize(message: dict) -> Update:
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
        if message["type"] == UpdateType.vk_request:
            return Update(
                type=message["type"],
                object=InfoUpdateObject(
                    vk_user_request=message[UpdateType.vk_request],
                    name=message["first_name"],
                    last_name=message["last_name"],
                    peer_id=message["peer_id"],
                    event_id=message["event_id"],
                ),
            )


class GameException(Exception):
    def __init__(self, text: str, event_answer=False):
        self.text = text
        self.event_answer = event_answer

    def __str__(self):
        return str(self.text)
