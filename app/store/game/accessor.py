from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.base.utils import to_dataclass
from app.game.models import (
    AnswerModel,
    Game,
    GameCaptainModel,
    GameModel,
    GameScoreModel,
    GameSpeakerModel,
    Player,
    PlayerModel,
    Question,
    QuestionModel,
    UsedQuestionsModel,
)


class GameAccessor:
    def __init__(self, db):
        self.database = db
        
    async def create_game(
        self,
        chat_id: int,
        created_at: datetime,
        players: list[Player],
        new_players: list[dict],
    ) -> Game:
        db_players = []
        for player in players:
            db_players.append(
                await self._get_player_by_vk_id_sql_model(player.vk_id)
            )
        new_players_models = [
            PlayerModel(
                name=player["name"],
                last_name=player["last_name"],
                vk_id=player["vk_id"],
            )
            for player in new_players
        ]
        db_players.extend(new_players_models)
        async with self.database.session.begin() as session:
            game = GameModel(
                chat_id=chat_id, players=db_players, created_at=created_at
            )
            session.add(game)
        return to_dataclass(game)

    async def _get_game_sql_model(
        self, chat_id: int, status: str = None
    ) -> GameModel:
        async with self.database.session.begin() as session:
            # breakpoint()
            if status is None:
                game = (
                    await session.execute(
                        select(GameModel, PlayerModel, GameScoreModel)
                        .where(GameModel.chat_id == chat_id)
                        .options(joinedload(GameModel.players))
                        .options(joinedload(PlayerModel.scores))
                        .options(joinedload(GameScoreModel.games))
                    )
                ).scalar()
            else:
                game = (
                    await session.execute(
                        select(GameModel, PlayerModel, GameScoreModel)
                        .where(
                            and_(
                                GameModel.chat_id == chat_id,
                                GameModel.status == status,
                            )
                        )
                        .options(joinedload(GameModel.players))
                        .options(joinedload(PlayerModel.scores))
                        .options(joinedload(GameScoreModel.games))
                    )
                ).scalar()
        return game

    # async def get_game_sql_model(self, chat_id: int):
    #     async with self.database.session.begin() as session:
    #         game = (await session.execute(select(GameModel, GameScoreModel)
    #                                       .where(GameModel.chat_id == chat_id)
    #                                       .options(joinedload(GameModel.scores))
    #                                       .options(joinedload(GameScoreModel.players)))).scalar()
    #     return game

    async def get_game(self, chat_id: int, status: str = None) -> Game | None:
        game = await self._get_game_sql_model(chat_id=chat_id, status=status)
        if game is not None:
            return to_dataclass(game)
        return None

    async def _get_game_by_id(self, id: int):
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel, GameScoreModel)
                    .where(GameModel.id == id)
                    .options(joinedload(GameModel.players))
                    .options(joinedload(PlayerModel.scores))
                    .options(joinedload(GameScoreModel.games))
                )
            ).scalar()
        return game

    async def get_game_by_id(self, id: int):
        game = await self._get_game_by_id(id=id)
        if game is not None:
            return to_dataclass(game)
        return None

    async def update_game(self, id: int, **params):
        status = params.get("status")
        wait_status = params.get("wait_status")
        my_points = params.get("my_points")
        players_points = params.get("players_points")
        round_ = params.get("round")
        wait_time = params.get("wait_time")
        current_question_id = params.get("current_question_id")
        game = await self._get_game_by_id(id=id)
        game.status = status if status is not None else game.status
        game.wait_status = (
            wait_status if wait_status is not None else game.wait_status
        )
        game.my_points = my_points if my_points is not None else game.my_points
        game.players_points = (
            players_points
            if players_points is not None
            else game.players_points
        )
        game.round = round_ if round_ is not None else game.round
        game.wait_time = wait_time if wait_time is not None else game.wait_time
        game.current_question_id = (
            current_question_id
            if current_question_id is not None
            else game.current_question_id
        )

        captain = params.get("captain")
        speaker = params.get("speaker")
        async with self.database.session.begin() as session:
            if captain is not None:
                # captain = await self._get_player_by_vk_id_sql_model(vk_id=params.get("captain").vk_id)
                game_captain_link = GameCaptainModel(
                    game_id=game.id, player_id=captain.id
                )
                session.add(game_captain_link)
            if speaker is not None:
                game_speaker_link = GameSpeakerModel(
                    game_id=game.id, player_id=speaker.id
                )
                session.add(game_speaker_link)
            session.add(game)
        return game

    async def list_games(self) -> list[Game]:
        async with self.database.session.begin() as session:
            games_ = await session.execute(
                select(GameModel, PlayerModel)
                .options(joinedload(GameModel.players))
                .options(joinedload(PlayerModel.scores))
            )
        games = games_.scalars().unique().all()
        return [to_dataclass(game) for game in games if game is not None]

    async def create_player(
        self, vk_id: int, name: str, last_name: str, games: list[Game]
    ) -> Player:
        db_games = []
        for game in games:
            db_games.append(
                await self._get_game_sql_model(
                    chat_id=game.chat_id, status=game.status
                )
            )
        async with self.database.session.begin() as session:
            player = PlayerModel(
                vk_id=vk_id, name=name, last_name=last_name, games=db_games
            )
            session.add(player)
        return to_dataclass(player)

    async def _get_player_by_vk_id_sql_model(self, vk_id: int) -> PlayerModel:
        async with self.database.session.begin() as session:
            player = (
                await session.execute(
                    select(PlayerModel, GameScoreModel)
                    .where(PlayerModel.vk_id == vk_id)
                    .options(joinedload(PlayerModel.scores))
                    .options(joinedload(GameScoreModel.games))
                )
            ).scalar()
        return player

    async def get_player_by_vk_id(self, vk_id: int) -> Player:
        return to_dataclass(
            await self._get_player_by_vk_id_sql_model(vk_id=vk_id)
        )

    async def _get_player_by_names_sql_model(
        self, name: str, last_name: str
    ) -> PlayerModel:
        async with self.database.session.begin() as session:
            player = (
                await session.execute(
                    select(PlayerModel, GameScoreModel)
                    .where(
                        and_(
                            PlayerModel.name == name,
                            PlayerModel.last_name == last_name,
                        )
                    )
                    .options(joinedload(PlayerModel.scores))
                    .options(joinedload(GameScoreModel.games))
                )
            ).scalar()
        return player

    async def get_player_by_names(self, name: str, last_name: str) -> Player:
        return to_dataclass(
            await self._get_player_by_names_sql_model(
                name=name, last_name=last_name
            )
        )

    async def list_players_by_game(
        self, game_id: int, status: str = None
    ) -> list[Player]:
        async with self.database.session.begin() as session:
            players = (
                (
                    await session.execute(
                        select(PlayerModel, GameScoreModel)
                        .where(GameScoreModel.game_id == game_id)
                        .options(joinedload(PlayerModel.scores))
                        .options(joinedload(GameScoreModel.games))
                    )
                )
                .scalars()
                .unique()
                .all()
            )
        return [
            to_dataclass(player) for player in players if player is not None
        ]

    async def _get_score(self, player_id: int, game_id: int):
        async with self.database.session.begin() as session:
            score = (
                await session.execute(
                    select(GameScoreModel).where(
                        and_(
                            GameScoreModel.game_id == game_id,
                            GameScoreModel.player_id == player_id,
                        )
                    )
                )
            ).scalar()
        return score

    async def update_player_score(
        self, player_id: int, game_id: int, points: int = None
    ):
        score = await self._get_score(player_id=player_id, game_id=game_id)
        points_ = score.points
        score.points = points_ + points if points is not None else points_ + 1
        async with self.database.session.begin() as session:
            session.add(score)
        return

    async def get_total_score(self, player_id: int) -> int:
        async with self.database.session.begin() as session:
            score = (
                await session.execute(
                    select(func.sum(GameScoreModel.points))
                    .having(GameScoreModel.player_id == player_id)
                    .group_by(GameScoreModel.player_id)
                )
            ).scalar()
        return score

    async def get_captain(self, id: int) -> Player:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel)
                    .where(GameModel.id == id)
                    .options(joinedload(GameModel.captain))
                )
            ).scalar()
        return to_dataclass(game.captain[0])

    async def get_speaker(self, id: int) -> Player:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel)
                    .where(GameModel.id == id)
                    .options(joinedload(GameModel.speaker))
                )
            ).scalar()
        return to_dataclass(game.speaker[0])

    async def delete_speaker(self, game_id: int) -> None:
        async with self.database.session.begin() as session:
            link = (
                await session.execute(
                    select(GameSpeakerModel).where(
                        GameSpeakerModel.game_id == game_id
                    )
                )
            ).scalar()
            if link is not None:
                await session.delete(link)
        return None

    # async def get_player_list(self, chat_id: str, status: str = None) -> list[Player]:
    #     """
    #     Get all players of a certain game in a certain status.
    #     chat_id: chat_id
    #     :return: list of players
    #     """
    #     async with self.database.session.begin() as session:
    #         players_ = await session.execute(select(PlayerModel, GameModel)
    #                                          .where(GameModel.chat_id == chat_id)
    #                                          .options(joinedload(PlayerModel.games)))
    #
    #     players = players_.scalars().unique().all()
    #     return players

    async def get_latest_game(self) -> Game:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel)
                    .order_by(GameModel.created_at.desc())
                    .limit(1)
                    .options(joinedload(GameModel.players))
                    .options(joinedload(PlayerModel.scores))
                )
            ).scalar()
        return to_dataclass(game)

    async def link_player_to_game(
        self, player_id: int, game_id: int
    ) -> GameScoreModel:
        """
        Link an already created game with an already created player. This method is used in Bot Manager,
        not in OpenAPI
        :param player_id:
        :param game_id:
        :return: game_score
        """
        async with self.database.session.begin() as session:
            game_score = GameScoreModel(player_id=player_id, game_id=game_id)
            session.add(game_score)
        return game_score

    async def create_question(self, text: str, answer: dict) -> Question:
        answer_model = AnswerModel(text=answer["text"].strip().lower())
        text = text.strip()
        async with self.database.session.begin() as session:
            question = QuestionModel(text=text, answer=[answer_model])
            session.add(question)
        return to_dataclass(question)

    async def get_all_questions_amount(self):
        async with self.database.session.begin() as session:
            amount = (
                await session.execute(select(func.count(QuestionModel.id)))
            ).scalar()
        return amount

    async def get_all_question_ids(self):
        async with self.database.session.begin() as session:
            ids = (await session.execute(select(QuestionModel.id))).scalars()
        return ids.unique().all()

    async def get_question_ids(self):
        async with self.database.session.begin() as session:
            ids = (
                await session.execute(
                    select(QuestionModel.id)
                    .join(
                        UsedQuestionsModel,
                        UsedQuestionsModel.question_id == QuestionModel.id,
                        isouter=True,
                    )
                    .filter(UsedQuestionsModel.question_id == None)  # type: ignore # noqa: E711
                )
            ).scalars()
        return ids.unique().all()

    async def _get_question(self, question_id: int) -> QuestionModel:
        async with self.database.session.begin() as session:
            question = (
                await session.execute(
                    select(QuestionModel, AnswerModel)
                    .where(QuestionModel.id == question_id)
                    .options(joinedload(QuestionModel.answer))
                )
            ).scalar()
        return question

    async def get_question(self, question_id: int) -> Question:
        question = await self._get_question(question_id)
        return to_dataclass(question)

    async def list_questions(self):
        async with self.database.session.begin() as session:
            questions = (
                (
                    await session.execute(
                        select(QuestionModel, AnswerModel).options(
                            joinedload(QuestionModel.answer)
                        )
                    )
                )
                .scalars()
                .unique()
                .all()
            )
        return [
            to_dataclass(question)
            for question in questions
            if question is not None
        ]

    async def list_answers(self):
        async with self.database.session.begin() as session:
            answers = (
                (await session.execute(select(AnswerModel)))
                .scalars()
                .unique()
                .all()
            )
        return [
            to_dataclass(answer) for answer in answers if answer is not None
        ]

    async def mark_question_as_used(self, question_id: int, game_id: int):
        async with self.database.session.begin() as session:
            link = UsedQuestionsModel(question_id=question_id, game_id=game_id)
            session.add(link)
        return link

    async def unmark_questions_as_used(self, game_id: int) -> None:
        async with self.database.session.begin() as session:
            await session.execute(
                delete(UsedQuestionsModel).where(
                    UsedQuestionsModel.game_id == game_id
                )
            )
        return None

    async def delete_question(self, question_id: int) -> None:
        async with self.database.session.begin() as session:
            question = await self._get_question(question_id)
            await session.delete(question)
        return None
