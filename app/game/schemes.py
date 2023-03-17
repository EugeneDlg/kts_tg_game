from marshmallow import Schema, fields
from app.web.schemes import OkResponseSchema


class PlayerSchema(Schema):
    id = fields.Int(required=False)
    name = fields.Str(required=False)
    last_name = fields.Str(required=False)


class GameSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    players = fields.Nested(PlayerSchema, many=True, required=True)


class GameResponseSchema(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=True)