from typing import Optional
from datetime import datetime
from sqlalchemy import select, text, and_, or_
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.base.utils import to_dataclass
from app.game.models import PlayerModel, GameModel, Player, Game, GameScoreModel


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id: int, created_at: datetime,
                          players: list[Player], new_players: list[dict]) -> Game:
        db_players = []
        for player in players:
            db_players.append(await self._get_player_by_vk_id_sql_model(player.vk_id))
        new_players_models = [
            PlayerModel(
                name=player["name"], last_name=player["last_name"], vk_id=player["vk_id"]
            ) for player in new_players
        ]
        db_players.extend(new_players_models)
        async with self.app.database.session.begin() as session:
            game = GameModel(chat_id=chat_id, players=db_players, created_at=created_at)
            session.add(game)
        return to_dataclass(game)

    async def _get_game_sql_model(self, chat_id: int, status: str = None) -> GameModel:
        async with self.app.database.session.begin() as session:
            # breakpoint()
            if status is None:
                game = (await session.execute(select(GameModel, PlayerModel, GameScoreModel)
                                              .where(GameModel.chat_id == chat_id)
                                              .options(joinedload(GameModel.players))
                                              .options(joinedload(PlayerModel.scores))
                                              .options(joinedload(GameScoreModel.games)))).scalar()
            else:
                game = (await session.execute(select(GameModel, PlayerModel, GameScoreModel)
                                              .where(and_(GameModel.chat_id == chat_id,
                                                          GameModel.status == status))
                                              .options(joinedload(GameModel.players))
                                              .options(joinedload(PlayerModel.scores))
                                              .options(joinedload(GameScoreModel.games)))).scalar()
        return game

    # async def get_game_sql_model(self, chat_id: int):
    #     async with self.app.database.session.begin() as session:
    #         game = (await session.execute(select(GameModel, GameScoreModel)
    #                                       .where(GameModel.chat_id == chat_id)
    #                                       .options(joinedload(GameModel.scores))
    #                                       .options(joinedload(GameScoreModel.players)))).scalar()
    #     return game

    async def get_game(self, chat_id: int, status: str = None) -> Optional[Game]:
        game = await self._get_game_sql_model(chat_id=chat_id, status=status)
        if game is not None:
            return to_dataclass(game)
        return None

    async def _get_game_by_id(self, id: int):
        async with self.app.database.session.begin() as session:
            game = (await session.execute(select(GameModel, PlayerModel, GameScoreModel)
                                          .where(GameModel.id == id)
                                          .options(joinedload(GameModel.players))
                                          .options(joinedload(PlayerModel.scores))
                                          .options(joinedload(GameScoreModel.games)))).scalar()
        return game

    async def update_game(self, id: int, **params):
        status = params.get("status")
        wait_status = params.get("wait_status")
        my_points = params.get("my_points")
        players_points = params.get("players_points")
        game = await self._get_game_by_id(id=id)
        game.status = status if status is not None else game.status
        game.wait_status = wait_status if wait_status is not None else game.wait_status
        game.my_points = my_points if my_points is not None else game.my_points
        game.players_points = players_points if players_points is not None else game.players_points
        async with self.app.database.session.begin() as session:
            session.add(game)
        return game

    async def list_games(self) -> list[Game]:
        async with self.app.database.session.begin() as session:
            games_ = (await session.execute(select(GameModel, PlayerModel)
                                            .options(joinedload(GameModel.players))
                                            .options(joinedload(PlayerModel.scores))))
        games = games_.scalars().unique().all()
        return [to_dataclass(game) for game in games if game is not None]

    async def create_player(
            self, vk_id: int, name: str,
            last_name: str, games: list[Game]) -> Player:
        db_games = []
        for game in games:
            db_games.append(await self._get_game_sql_model(chat_id=game.chat_id, status=game.status))
        async with self.app.database.session.begin() as session:
            player = PlayerModel(vk_id=vk_id, name=name, last_name=last_name, games=db_games)
            session.add(player)
        return to_dataclass(player)

    async def _get_player_by_vk_id_sql_model(self, vk_id: int) -> PlayerModel:
        async with self.app.database.session.begin() as session:
            player = (await session.execute(select(PlayerModel, GameScoreModel)
                                            .where(PlayerModel.vk_id == vk_id)
                                            .options(joinedload(PlayerModel.scores))
                                            .options(joinedload(GameScoreModel.games)))).scalar()
        return player

    async def get_player_by_vk_id(self, vk_id: int) -> Player:
        return to_dataclass(await self._get_player_by_vk_id_sql_model(vk_id=vk_id))

    async def _get_player_by_names_sql_model(self, name: str, last_name: str) -> PlayerModel:
        async with self.app.database.session.begin() as session:
            player = (await session.execute(select(PlayerModel, GameScoreModel)
                                            .where(PlayerModel.name == name
                                                   and PlayerModel.last_name == last_name)
                                            .options(joinedload(PlayerModel.scores))
                                            .options(joinedload(GameScoreModel.games)))).scalar()
        return player

    async def get_player_by_names(self, name: str, last_name: str) -> Player:
        return to_dataclass(await self._get_player_by_names_sql_model(name=name, last_name=last_name))

    async def get_player_list(self, chat_id: str) -> list[PlayerModel]:
        """
        Get all players in a certain game. This method is used in Bot Manager,
        not in OpenAPI
        :chat_id: chat_id
        :return: list of players
        """
        async with self.app.database.session.begin() as session:
            players_ = await session.execute(select(PlayerModel, GameModel)
                                             .where(GameModel.chat_id == chat_id)
                                             .options(joinedload(PlayerModel.games)))

        players = players_.scalars().unique().all()
        return players

    async def get_latest_game(self) -> Game:
        async with self.app.database.session.begin() as session:
            game = (await session.execute(select(GameModel, PlayerModel)
                                          .order_by(GameModel.created_at.desc())
                                          .limit(1)
                                          .options(joinedload(GameModel.players))
                                          .options(joinedload(PlayerModel.scores)))).scalar()
        return to_dataclass(game)

    async def link_player_to_game(self, player_id: int, game_id: int) -> GameScoreModel:
        """
        Link an already created game with an already created player. This method is used in Bot Manager,
        not in OpenAPI
        :param player_id:
        :param game_id:
        :return: game_score
        """
        async with self.app.database.session.begin() as session:
            game_score = GameScoreModel(player_id=player_id, game_id=game_id)
            session.add(game_score)
        return game_score

    # async def get_game_not_nested(self, chat_id: int) -> GameModel:
    #     async with self.app.database.session.begin() as session:
    #         game = (await session.execute(select(GameModel)
    #                                       .where(GameModel.chat_id == chat_id)
    #                                       )).scalar()
    #     return game

    # async def get_player_by_vk_id_not_nested(self, vk_id: int) -> PlayerModel:
    #     async with self.app.database.session.begin() as session:
    #         player = (await session.execute(select(PlayerModel)
    #                                         .where(PlayerModel.vk_id == vk_id)
    #                                         )).scalar()
    #     return player
