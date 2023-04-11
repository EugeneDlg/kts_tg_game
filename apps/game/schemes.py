from marshmallow import Schema, fields

from apps.api.schemes import OkResponseSchema


class PlayerSchema(Schema):
    id = fields.Int(required=False)
    vk_id = fields.Int(required=True)
    name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    games = fields.Nested("GameSchemaNotNested", many=True, required=False)


class PlayerVkIdSchema(Schema):
    vk_id = fields.Int(required=True)


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


class PlayerResponseSchema(OkResponseSchema):
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


class PlayerScoreResponseSchema(OkResponseSchema):
    data = fields.Nested(PlayerScoreSchemaBeforeResponse, required=True)


class PlayerListSchemaBeforeResponse(Schema):
    players = fields.Nested(
        PlayerScoreSchema2BeforeResponse, many=True, required=True
    )


class PlayerListResponseSchema(Schema):
    data = fields.Nested(PlayerListSchemaBeforeResponse, required=True)


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
    status = fields.Str(required=True)
    players = fields.Nested(PlayerSchemaNotNested, many=True, required=True)


class GameSchemaNotNested(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=False)


class GameSchemaBeforeResponse(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    status = fields.Str(required=True)
    created_at = fields.DateTime(required=True)
    my_points = fields.Int(required=True)
    player_points = fields.Int(required=True)
    round = fields.Int(required=True)
    current_question_id = fields.Str(required=True)
    players = fields.Nested(
        PlayerScoreSchema2BeforeResponse, many=True, required=True
    )


class GameSchemaForCreateBeforeResponse(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    created_at = fields.DateTime(required=True)
    players = fields.Nested(
        PlayerSchemaForCreateBeforeResponse, many=True, required=True
    )


class GameResponseSchema(OkResponseSchema):
    data = fields.Nested(GameSchemaBeforeResponse, required=True)


class GameListSchemaBeforeResponse(Schema):
    games = fields.Nested(GameSchemaBeforeResponse, many=True, required=True)


class GameListResponseSchema(OkResponseSchema):
    data = fields.Nested(GameListSchemaBeforeResponse, required=True)


class AnswerSchema(Schema):
    id = fields.Str(required=False)
    text = fields.Str(required=True)


class QuestionSchema(Schema):
    id = fields.Str(required=False)
    text = fields.Str(required=True)
    blitz = fields.Boolean(required=True)
    answer = fields.Nested(AnswerSchema, required=True)


class QuestionIdSchema(Schema):
    id = fields.Str(required=True)


class QuestionSchemaBeforeResponse(Schema):
    id = fields.Str(required=False)
    text = fields.Str(required=True)
    blitz = fields.Boolean(required=True)
    answer = fields.Nested(AnswerSchema, required=True, many=True)


class QuestionDumpSchema(Schema):
    id = fields.Str(required=False)
    text = fields.Str(required=True)
    blitz = fields.Boolean(required=True)


# response
class QuestionResponseScheme(OkResponseSchema):
    data = fields.Nested(QuestionSchemaBeforeResponse, required=True)


class QuestionListSchemaBeforeResponse(Schema):
    questions = fields.Nested(
        QuestionSchemaBeforeResponse, many=True, required=True
    )


# response
class QuestionListResponseSchema(OkResponseSchema):
    data = fields.Nested(QuestionListSchemaBeforeResponse)


class QuestionListDumpSchemaBeforeResponse(Schema):
    questions = fields.Nested(QuestionDumpSchema, many=True, required=True)


class QuestionListDumpResponseSchema(OkResponseSchema):
    data = fields.Nested(QuestionListSchemaBeforeResponse, required=True)


class AnswerDumpSchema(AnswerSchema):
    question_id = fields.Str(required=True)


class AnswerListDumpSchemaBeforeResponse(Schema):
    answers = fields.Nested(AnswerDumpSchema, many=True, required=True)


class AnswerListDumpResponseSchema(Schema):
    data = fields.Nested(AnswerListDumpSchemaBeforeResponse, required=True)
