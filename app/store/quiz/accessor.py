from typing import Optional
from collections import defaultdict
from sqlalchemy import distinct, func, select, text
from sqlalchemy.orm import joinedload
from app.base.base_accessor import BaseAccessor
from app.quiz.models import Theme, Question, Answer
from app.quiz.models import ThemeModel, QuestionModel, AnswerModel
from app.quiz.models import to_dataclass


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        async with self.app.database.session.begin() as session:
            theme = ThemeModel(title=title)
            session.add(theme)
        return to_dataclass(theme)

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        async with self.app.database.session.begin() as session:
            theme = await session.execute(select(ThemeModel).filter(ThemeModel.title == title))
        return to_dataclass(theme.scalar())

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        async with self.app.database.session.begin() as session:
            theme = await session.execute(select(ThemeModel).filter(ThemeModel.id == id_))
        return to_dataclass(theme.scalar())

    async def list_themes(self) -> list[Theme]:
        async with self.app.database.session.begin() as session:
            themes = await session.execute(select(ThemeModel))
        themes_list = themes.scalars().all()
        return [to_dataclass(theme) for theme in themes_list if theme is not None]

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        async with self.app.database.session.begin() as session:
            question = (
                await session.execute(
                    select(QuestionModel)
                    .where(QuestionModel.title == title)
                    .options(joinedload(QuestionModel.answers)))
            ).scalar()
            if question is None:
                return None
        return to_dataclass(question)

    async def create_question(
            self, title: str, theme_id: int, answers: list[Answer]
    ) -> Question:
        async with self.app.database.session.begin() as session:
            answers_model = [
                AnswerModel(
                    title=answer["title"], is_correct=answer["is_correct"]
                ) for answer in answers
            ]
            question = QuestionModel(title=title, theme_id=theme_id, answers=answers_model)
            session.add(question)
        return to_dataclass(question)

    async def list_questions(self, theme_id: Optional[int] = None) -> list[Question]:
        select_ = select(QuestionModel).where(QuestionModel.theme_id == theme_id) \
            if theme_id is not None else select(QuestionModel)
        async with self.app.database.session.begin() as session:
            question = await session.execute(
                select_.options(joinedload(QuestionModel.answers))
            )
        # breakpoint()
        questions = question.scalars().unique().all()
        return [to_dataclass(question) for question in questions if question is not None]
