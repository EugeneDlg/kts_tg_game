from marshmallow import Schema, fields
from app.web.schemes import OkResponseSchema


class ThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)


class ThemeIdSchemaTemp(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)


# response
class ThemeIdSchema(OkResponseSchema):
    data = fields.Nested(ThemeIdSchemaTemp)


class ThemeListSchemaTemp(Schema):
    themes = fields.Nested(ThemeIdSchemaTemp, many=True)


# response
class ThemeListSchema(OkResponseSchema):
    data = fields.Nested(ThemeListSchemaTemp)


class AnswerSchema(Schema):
    title = fields.Str(required=True)
    is_correct = fields.Bool(required=True)


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    theme_id = fields.Int(required=True)
    answers = fields.Nested(AnswerSchema, many=True, required=True)


class QuestionSchemaTemp(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    theme_id = fields.Int(required=True)
    answers = fields.Nested(AnswerSchema, many=True, required=True)


# response
class QuestionResponseScheme(OkResponseSchema):
    data = fields.Nested(QuestionSchemaTemp)


class QuestionListSchemaTemp(Schema):
    questions = fields.Nested(QuestionSchemaTemp, many=True)


# response
class QuestionListSchema(OkResponseSchema):
    data = fields.Nested(QuestionListSchemaTemp)