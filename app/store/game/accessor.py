from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.base.utils import to_dataclass
from app.game.models import PlayerModel, GameModel, Player, Game, GameScoreModel


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id: int, created_at: datetime,
                          players: list[Player], new_players: list[Player]) -> Game:
        breakpoint()
        async with self.app.database.session.begin() as session:
            new_players_model = [
                PlayerModel(
                    name=player["name"], last_name=player["last_name"], vk_id=player["vk_id"]
                ) for player in new_players
            ]
            players.extend(new_players_model)

            game = GameModel(chat_id=chat_id, players=players, created_at=created_at)
            session.add(game)
        return to_dataclass(game)

    async def get_game_(self, chat_id: int):
        async with self.app.database.session.begin() as session:
            game = (await session.execute(select(GameModel, PlayerModel)
                                          .where(GameModel.chat_id == chat_id)
                                          .options(joinedload(GameModel.players))
                                          .options(joinedload(PlayerModel.scores)))).scalar()
        return game

    # async def get_game_(self, chat_id: int):
    #     async with self.app.database.session.begin() as session:
    #         game = (await session.execute(select(GameModel, GameScoreModel)
    #                                       .where(GameModel.chat_id == chat_id)
    #                                       .options(joinedload(GameModel.scores))
    #                                       .options(joinedload(GameScoreModel.players)))).scalar()
    #     return game

    async def get_game(self, chat_id: int):
        return to_dataclass(await self.get_game_(chat_id=chat_id))

    async def list_games(self):
        async with self.app.database.session.begin() as session:
            response = (await session.execute(select(GameModel, PlayerModel)
                                              .options(joinedload(GameModel.players))
                                              .options(joinedload(PlayerModel.scores))))
        games = response.scalars().unique().all()
        return [to_dataclass(game) for game in games if game is not None]

    async def create_player(
            self, vk_id: int, name: str,
            last_name: str) -> Player:
        async with self.app.database.session.begin() as session:
            player = PlayerModel(vk_id=vk_id, name=name, last_name=last_name)
            session.add(player)
        return to_dataclass(player)

    async def get_player_by_vk_id_(self, vk_id: int):
        async with self.app.database.session.begin() as session:
            player = (await session.execute(select(PlayerModel, GameScoreModel)
                                            .where(PlayerModel.vk_id == vk_id)
                                            .options(joinedload(PlayerModel.scores))
                                            .options(joinedload(GameScoreModel.games)))).scalar()
        return player

    async def get_player_by_vk_id(self, vk_id: int):
        return to_dataclass(await self.get_player_by_vk_id_(vk_id=vk_id))

    async def get_player_by_names_(self, name: str, last_name: str):
        async with self.app.database.session.begin() as session:
            player = (await session.execute(select(PlayerModel, GameScoreModel)
                                            .where(PlayerModel.name == name
                                                   and PlayerModel.last_name == last_name)
                                            .options(joinedload(PlayerModel.scores))
                                            .options(joinedload(GameScoreModel.games)))).scalar()
        return player

    async def get_player_by_names(self, name: str, last_name: str):
        return to_dataclass(await self.get_player_by_names_(name=name, last_name=last_name))

    async def get_latest_game(self):
        async with self.app.database.session.begin() as session:
            game = (await session.execute(select(GameModel, PlayerModel)
                                          .order_by(GameModel.created_at.desc())
                                          .limit(1)
                                          .options(joinedload(GameModel.players))
                                          .options(joinedload(PlayerModel.scores)))).scalar()
        return to_dataclass(game)
