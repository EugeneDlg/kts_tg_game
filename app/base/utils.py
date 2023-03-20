import dataclasses
from app.game.models import Game, GameModel, Player, PlayerModel, GameScore, GameScoreModel

models = {GameModel: Game,
          PlayerModel: Player,
          GameScoreModel: GameScore}


def to_dataclass(model_instance, chain=[]):
    if model_instance is None:
        return
    if not isinstance(model_instance, list):
        if isinstance(model_instance, tuple(chain)):
            return
        else:
            chain.append(type(model_instance))
    if isinstance(model_instance, list):
        lst = []
        for item in model_instance:
            obj = to_dataclass(item, chain)
            if obj is None:
                return
            lst.append(obj)
        return lst
    dataclass_model = models[type(model_instance)]
    fields = dataclasses.fields(dataclass_model)
    model_attributes = model_instance.__dict__
    dct = {}
    for field in fields:
        attr = model_attributes.get(field.name)
        if isinstance(attr, (list, tuple(models))):
            dct[field.name] = to_dataclass(attr, chain)
        else:
            dct[field.name] = attr
    chain.pop()
    return dataclass_model(**dct)