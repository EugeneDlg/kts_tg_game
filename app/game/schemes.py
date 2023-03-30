from marshmallow import Schema, fields
from app.web.schemes import OkResponseSchema


class PlayerSchema(Schema):
    id = fields.Int(required=False)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    games = fields.Nested("GameSchemaNotNested", many=True, required=False)


class PlayerSchemaNotNested(Schema):
    id = fields.Int(required=False)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=False)


class PlayerSchemaBeforeResponse(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    games = fields.Nested("GameSchemaNotNested", many=True, required=True)


class PlayerSchemaForCreateBeforeResponse(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)


class PlayerResponseSchema(Schema):
    data = fields.Nested(PlayerSchemaBeforeResponse, required=True)


class PlayerScoreSchemaBeforeResponse(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    scores = fields.Nested("ScoreSchema", many=True, required=True)


class PlayerScoreSchema2BeforeResponse(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    scores = fields.Nested("ScoreSchemaNotNested", many=True, required=True)


class PlayerScoreResponseSchema(Schema):
    data = fields.Nested(PlayerScoreSchemaBeforeResponse, required=True)


class PlayerGameLinkSchema(Schema):
    vk_id = fields.Int(required=True)
    chat_id = fields.Int(required=True)


class PlayerGameLinkSchemaBeforeResponse(Schema):
    vk_id = fields.Int(required=True)
    chat_id = fields.Int(required=True)


class PlayerGameLinkResponseSchema(Schema):
    data = fields.Nested(PlayerGameLinkSchemaBeforeResponse, required=True)


class ScoreSchema(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    # game = fields.Int(required=True)
    points = fields.Int(required=True)
    games = fields.Nested("GameSchemaNotNested", required=True)


class ScoreSchemaNotNested(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    points = fields.Int(required=True)


class GameSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    players = fields.Nested(PlayerSchemaNotNested, many=True, required=True)


class GameSchemaNotNested(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=False)


class GameSchemaBeforeResponse(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=True)
    players = fields.Nested(PlayerScoreSchema2BeforeResponse, many=True, required=True)


class GameSchemaForCreateBeforeResponse(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=True)
    players = fields.Nested(PlayerSchemaForCreateBeforeResponse, many=True, required=True)


class GameResponseSchema(Schema):
    data = fields.Nested(GameSchemaBeforeResponse, required=True)


class GameListSchemaBeforeResponse(Schema):
    games = fields.Nested(GameSchemaBeforeResponse, many=True, required=True)


class GameListResponseSchema(Schema):
    data = fields.Nested(GameListSchemaBeforeResponse, required=True)

