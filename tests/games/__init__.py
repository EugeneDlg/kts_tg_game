from apps.game.models import Player, Game, GameScore


def game2dict(game: Game):
    return {
        "id": int(game.id),
        "created_at": str(game.created_at),
        "chat_id": int(game.chat_id),
        "players": [player2dict(player) for player in game.players],
    }


def player2dict(player: Player):
    return {
        "id": int(player.id),
        "vk_id": player.vk_id,
        "name": player.name,
        "last_name": player.last_name,
        # "scores": [score2dict(score) for score in player.scores],
    }


def score2dict(score: GameScore):
    return {
        "points": int(score.points),
    }
