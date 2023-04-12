import collections
from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import joinedload

from apps.base.utils import to_dataclass
from apps.game.models import (
    Answer,
    AnswerModel,
    Game,
    GameCaptainModel,
    GameModel,
    GameScore,
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

    @to_dataclass
    async def create_game(
        self,
        chat_id: int,
        created_at: datetime,
        players: list[Player],
        new_players: list[dict],
    ) -> Game:
        db_players = []
        for player in players:
            db_players.append(await self._get_player_as_orm_model(player.vk_id))
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
        return game

    async def get_game(self, chat_id: int, status: str) -> Game:
        game = await self._get_game_as_orm_tuple(chat_id=chat_id, status=status)
        return self.games_from_sql(game, many=False)

    async def _get_game_as_orm(self, chat_id: int, status: str) -> GameModel:
        game = await self._get_game_as_orm_tuple(chat_id=chat_id, status=status)
        if game is None or len(game) == 0:
            return None
        return game[0][0]

    async def _get_game_as_orm_tuple(
        self, chat_id: int, status: str
    ) -> tuple[GameModel]:
        async with self.database.session.begin() as session:
            game = await session.execute(
                select(GameModel, PlayerModel, GameScoreModel)
                .where(
                    and_(
                        GameModel.chat_id == chat_id,
                        GameModel.status == status,
                    )
                )
                .join(
                    GameModel,
                    GameModel.id == GameScoreModel.game_id,
                    isouter=True,
                )
                .join(
                    PlayerModel,
                    PlayerModel.id == GameScoreModel.player_id,
                    isouter=True,
                )
            )
        return game.all()

    @staticmethod
    def games_from_sql(game_all: list[GameModel], many: bool) -> list[Game]:
        if game_all is None or len(game_all) == 0:
            return [] if many else None
        games = collections.defaultdict(list)
        for row in game_all:
            game_instance = row[0]
            player_instance = row[1]
            player = Player(
                id=player_instance.id,
                vk_id=player_instance.vk_id,
                name=player_instance.name,
                last_name=player_instance.last_name,
                scores=[GameScore(points=row[2].points, games=None)],
            )
            games[game_instance].append(player)
        game_list = []
        for game_instance, players_instance in games.items():
            game = Game(
                id=game_instance.id,
                chat_id=game_instance.chat_id,
                created_at=game_instance.created_at,
                current_question_id=game_instance.current_question_id,
                wait_status=game_instance.wait_status,
                wait_time=game_instance.wait_time,
                status=game_instance.status,
                my_points=game_instance.my_points,
                players_points=game_instance.players_points,
                round=game_instance.round,
                blitz_round=game_instance.blitz_round,
                players=players_instance,
                speaker=None,
                captain=None,
            )
            game_list.append(game)
        return game_list if many else game_list[0]

    # async def get_game_sql_model(self, chat_id: int):
    #     async with self.database.session.begin() as session:
    #         game = (await session.execute(select(GameModel, GameScoreModel)
    #                                       .where(GameModel.chat_id == chat_id)
    #                                       .options(joinedload(GameModel.scores))
    #                                       .options(joinedload(GameScoreModel.players)))).scalar()
    #     return game

    async def get_game_by_id(self, id: int) -> Game:
        game = await self._get_game_by_id_as_orm_tuple(id)
        return self.games_from_sql(game, many=False)

    async def _get_game_by_id_as_orm(self, id: int) -> GameModel:
        game = await self._get_game_by_id_as_orm_tuple(id)
        if game is None or len(game) == 0:
            return None
        return game[0][0]

    async def _get_game_by_id_as_orm_tuple(self, id: int) -> list[GameModel]:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel, GameScoreModel)
                    .where(GameModel.id == id)
                    .join(
                        GameModel,
                        GameModel.id == GameScoreModel.game_id,
                        isouter=True,
                    )
                    .join(
                        PlayerModel,
                        PlayerModel.id == GameScoreModel.player_id,
                        isouter=True,
                    )
                )
            ).all()
        return game

    async def update_game(self, id: int, **params):
        status = params.get("status")
        wait_status = params.get("wait_status")
        my_points = params.get("my_points")
        players_points = params.get("players_points")
        round_ = params.get("round")
        blitz_round = params.get("blitz_round")
        wait_time = params.get("wait_time")
        current_question_id = params.get("current_question_id")
        game = await self._get_game_by_id_as_orm(id=id)
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
        game.blitz_round = (
            blitz_round if blitz_round is not None else game.blitz_round
        )
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
                # captain = await self._get_player_by_vk_id(vk_id=params.get("captain").vk_id)
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

    async def delete_game(self, id: int) -> None:
        async with self.database.session.begin() as session:
            game = await self._get_game_by_id_as_orm(id=id)
            await session.delete(game)
        return None

    async def list_games(self, status: str = None) -> list[Game]:
        async with self.database.session.begin() as session:
            if status is None:
                games_all = (
                    await session.execute(
                        select(GameModel, PlayerModel, GameScoreModel)
                        .join(
                            GameModel,
                            GameModel.id == GameScoreModel.game_id,
                            isouter=True,
                        )
                        .join(
                            PlayerModel,
                            PlayerModel.id == GameScoreModel.player_id,
                            isouter=True,
                        )
                    )
                ).all()
            else:
                games_all = (
                    await session.execute(
                        select(GameModel, PlayerModel, GameScoreModel)
                        .where(GameModel.status == status)
                        .join(
                            GameModel,
                            GameModel.id == GameScoreModel.game_id,
                            isouter=True,
                        )
                        .join(
                            PlayerModel,
                            PlayerModel.id == GameScoreModel.player_id,
                            isouter=True,
                        )
                    )
                ).all()
        return self.games_from_sql(games_all, many=True)

    @to_dataclass
    async def create_player(
        self, vk_id: int, name: str, last_name: str, games: list[Game]
    ) -> Player:
        db_games = []
        for game in games:
            db_games.append(await self._get_game_by_id_as_orm(game.id))
        async with self.database.session.begin() as session:
            player = PlayerModel(
                vk_id=vk_id, name=name, last_name=last_name, games=db_games
            )
            session.add(player)
        return player

    @to_dataclass
    async def get_player(self, vk_id: int) -> Player:
        player = await self._get_player_as_orm_model(vk_id)
        if player is None:
            return None
        return player

    async def _get_player_as_orm_model(self, vk_id: int) -> PlayerModel:
        async with self.database.session.begin() as session:
            player = (
                await session.execute(
                    select(PlayerModel).where(PlayerModel.vk_id == vk_id)
                )
            ).scalar()
        return player

    async def _get_player_with_scores_by_vk_id_as_orm(
        self, vk_id: int
    ) -> PlayerModel:
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

    @to_dataclass
    async def get_player_with_scores_by_vk_id(self, vk_id: int) -> Player:
        game = await self._get_player_with_scores_by_vk_id_as_orm(vk_id=vk_id)
        if game is None:
            return None
        return game

    async def _get_player_with_scores_by_names_as_orm(
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

    @to_dataclass
    async def get_player_with_scores_by_names_as_orm(
        self, name: str, last_name: str
    ) -> Player:
        player = await self._get_player_with_scores_by_names_as_orm(
            name=name, last_name=last_name
        )
        return player

    async def delete_player(self, vk_id: int) -> None:
        async with self.database.session.begin() as session:
            player = await self._get_player_as_orm_model(vk_id)
            await session.delete(player)
        return None

    @to_dataclass
    async def list_players_by_game(
        self,
        game_id: int = None,
    ) -> list[Player]:
        async with self.database.session.begin() as session:
            if game_id is None:
                players = (
                    (
                        await session.execute(
                            select(PlayerModel, GameScoreModel)
                            .options(joinedload(PlayerModel.scores))
                            .options(joinedload(GameScoreModel.games))
                        )
                    )
                    .scalars()
                    .unique()
                    .all()
                )
            else:
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
        return players

    async def _get_score_as_orm(self, player_id: int, game_id: int):
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
        score = await self._get_score_as_orm(
            player_id=player_id, game_id=game_id
        )
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

    @to_dataclass
    async def get_captain(self, id: int) -> Player:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel)
                    .where(GameModel.id == id)
                    .options(joinedload(GameModel.captain))
                )
            ).scalar()
        return game.captain[0]

    @to_dataclass
    async def get_speaker(self, id: int) -> Player:
        async with self.database.session.begin() as session:
            game = (
                await session.execute(
                    select(GameModel, PlayerModel)
                    .where(GameModel.id == id)
                    .options(joinedload(GameModel.speaker))
                )
            ).scalar()
        return game.speaker[0]

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

    @to_dataclass
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
        return game

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

    @to_dataclass
    async def create_question(
        self, text: str, blitz: bool, answer: dict
    ) -> Question:
        answer_model = AnswerModel(text=answer["text"].strip().lower())
        text = text.strip()
        async with self.database.session.begin() as session:
            question = QuestionModel(
                text=text, blitz=blitz, answer=[answer_model]
            )
            session.add(question)
        return question

    async def get_all_questions_amount(self) -> int:
        async with self.database.session.begin() as session:
            amount = (
                await session.execute(select(func.count(QuestionModel.id)))
            ).scalar()
        return amount

    async def get_question_ids(self, blitz: bool = False) -> list[int]:
        async with self.database.session.begin() as session:
            ids = (
                await session.execute(
                    select(QuestionModel.id)
                    .join(
                        UsedQuestionsModel,
                        UsedQuestionsModel.question_id == QuestionModel.id,
                        isouter=True,
                    )
                    .filter(
                        and_(
                            UsedQuestionsModel.question_id == None,
                            QuestionModel.blitz == blitz,
                        )
                    )  # type: ignore # noqa: E711
                )
            ).scalars()

        res = ids.unique().all()
        return res

    async def _get_question_as_orm(self, question_id: str) -> QuestionModel:
        async with self.database.session.begin() as session:
            question = (
                await session.execute(
                    select(QuestionModel, AnswerModel)
                    .where(QuestionModel.id == question_id)
                    .options(joinedload(QuestionModel.answer))
                )
            ).scalar()
        return question

    @to_dataclass
    async def get_question(self, question_id: str) -> Question:
        question = await self._get_question_as_orm(question_id)
        return question

    @to_dataclass
    async def list_questions(self) -> list[Question]:
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
        return questions

    @to_dataclass
    async def list_answers(self) -> list[Answer]:
        async with self.database.session.begin() as session:
            answers = (
                (await session.execute(select(AnswerModel)))
                .scalars()
                .unique()
                .all()
            )
        return answers

    async def mark_question_as_used(
        self, question_id: str, game_id: int
    ) -> UsedQuestionsModel:
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
            question = await self._get_question_as_orm(question_id)
            await session.delete(question)
        return None
