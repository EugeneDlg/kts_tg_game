from copy import deepcopy
from marshmallow import Schema, fields
import dataclasses
from app.quiz.models import ThemeModel, QuestionModel, AnswerModel
from app.quiz.models import Theme, Question, Answer


class OkResponseSchema(Schema):
    status = fields.Str()
    data = fields.Dict()


class ErrorResponseSchema(Schema):
    status = fields.Str()
    message = fields.Str()
    data = fields.Dict()
