import dataclasses

from app.game.models import (
    Answer,
    AnswerModel,
    Game,
    GameModel,
    GameScore,
    GameScoreModel,
    Player,
    PlayerModel,
    Question,
    QuestionModel,
)

models = {
    GameModel: Game,
    PlayerModel: Player,
    GameScoreModel: GameScore,
    QuestionModel: Question,
    AnswerModel: Answer,
}


def to_dataclass(model_instance, chain=[]):
    """
    Метод для прямого маппинга моделей SqlAlchemy в модели Dataclass непосредственно
    по именам атрибутов
    :param model_instance: Модель SqlAlchemy
    :param chain: стэк моделей при рекурсивных вызовах для избежания зацикленности
    :return: Модель Dataclass
    """
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
