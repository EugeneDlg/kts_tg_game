from datetime import datetime
from typing import Optional
from collections import defaultdict
from sqlalchemy import distinct, func, select, text
from sqlalchemy.orm import joinedload

from app.base.base_accessor import BaseAccessor
from app.quiz.models import to_dataclass
from app.game.models import PlayerModel, GameModel, Player, Game


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id: int, created_at: datetime, players: Player) -> Game:
        breakpoint()
        async with self.app.database.session.begin() as session:
            players_model = [
                PlayerModel(
                    name=player.name, last_name=player.last_name
                ) for player in players
            ]
            game = GameModel(chat_id=chat_id, created_at=created_at, players=players_model)
            session.add(game)

        return game

