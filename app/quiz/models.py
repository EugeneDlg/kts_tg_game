import dataclasses
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Theme:
    id: Optional[int]
    title: str


@dataclass
class Answer:
    title: str
    is_correct: bool

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class Question:
    id: Optional[int]
    title: str
    theme_id: int
    answers: list[Answer]


class ThemeModel(db):
    __tablename__ = "themes"
    id = Column(Integer(), primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    questions = relationship("QuestionModel", back_populates="themes", cascade="all, delete")


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(Integer(), primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    theme_id = Column(Integer(), ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    themes = relationship("ThemeModel", back_populates="questions", cascade="all, delete",)
    answers = relationship("AnswerModel", back_populates="questions", cascade="all, delete")


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(Integer(), primary_key=True)
    title = Column(String(100), nullable=False)
    is_correct = Column(Boolean(), nullable=False)
    question_id = Column(Integer(), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    questions = relationship("QuestionModel", back_populates="answers")


models = {ThemeModel: Theme, QuestionModel: Question, AnswerModel: Answer}


def to_dataclass(model_instance):
    if model_instance is None:
        return None
    if isinstance(model_instance, list):
        lst = []
        for item in model_instance:
            obj = to_dataclass(item)
            lst.append(obj)
        return lst
    dataclass_model = models[type(model_instance)]
    fields = dataclasses.fields(dataclass_model)
    model_attributes = model_instance.__dict__
    dct = {}
    for field in fields:
        attr = model_attributes.get(field.name)
        if isinstance(attr, list):
            dct[field.name] = to_dataclass(attr)
        elif type(attr) in models:
            dct[field.name] = to_dataclass(attr)
        else:
            dct[field.name] = attr
    return dataclass_model(**dct)