from apps.game.models import Player, Game, GameScore, Question, Answer


def game2dict(game: Game):
    return {
        "id": int(game.id),
        "created_at": str(game.created_at),
        "chat_id": int(game.chat_id),
        "players": [player2dict(player) for player in game.players],
    }


def game_list2dict(game: Game):
    return {
        "id": int(game.id),
        "created_at": str(game.created_at),
        "chat_id": int(game.chat_id),
        "status": game.status,
        "round": game.round,
        "blitz_round": game.blitz_round,
        "my_points": game.my_points,
        "players_points": game.players_points,
        "current_question_id": game.current_question_id,
        "players": [player_with_scores2dict(player) for player in game.players],
    }


def player_with_scores2dict(player: Player):
    return {
        "id": int(player.id),
        "vk_id": player.vk_id,
        "name": player.name,
        "last_name": player.last_name,
        "scores": [score2dict(score) for score in player.scores],
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
        "points": int(score["points"]),
    }


def question2dict(question: Question):
    return {
        "id": question.id,
        "text": question.text,
        "blitz": question.blitz,
        "answer": [answer2dict(Answer(
            id=answer.id, text=answer.text, question_id=None
        )) for answer in question.answer]
    }


def answer2dict(answer: Answer):
    return {
        "id": answer.id,
        "text": answer.text,
    }