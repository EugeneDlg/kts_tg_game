from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp.web_exceptions import (
    HTTPMethodNotAllowed,
    HTTPConflict,
    HTTPBadRequest,
    HTTPNotFound
)
from app.quiz.schemes import (
    ThemeSchema,
    ThemeIdSchema,
    ThemeListSchema,
    ThemeListSchemaTemp,
    QuestionSchema,
    QuestionListSchema,
    QuestionListSchemaTemp
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response, check_auth


# TODO: добавить проверку авторизации для этого View
class ThemeAddView(View, AuthRequiredMixin):
    @docs(tags=['theme'],
          summary='Adding a theme',
          description='Adding a theme')
    @request_schema(ThemeSchema)
    @response_schema(ThemeIdSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        title = data["title"]
        theme = await self.store.quizzes.get_theme_by_title(title=title)
        if theme is not None:
            raise HTTPConflict
        theme = await self.store.quizzes.create_theme(title=title)
        return json_response(data=ThemeSchema().dump(theme))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class ThemeListView(View, AuthRequiredMixin):
    @docs(tags=['theme'],
          summary='List all themes',
          description='List all themes')
    @response_schema(ThemeListSchema, 200)
    @check_auth
    async def get(self):
        themes = await self.store.quizzes.list_themes()
        data = {"themes": themes}
        dd = ThemeListSchemaTemp().dump(data)
        return json_response(data=dd)

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")


class QuestionAddView(View, AuthRequiredMixin):
    @docs(tags=['question'],
          summary='Adding a question',
          description='Adding a question')
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema, 200)
    @check_auth
    async def post(self):
        data = self.request["data"]
        title = data["title"]
        theme_id = data["theme_id"]
        answers = data["answers"]
        question = await self.store.quizzes.get_question_by_title(title=title)
        if question is not None:
            raise HTTPConflict
        theme = await self.store.quizzes.get_theme_by_id(id_=theme_id)
        if theme is None:
            raise HTTPNotFound(text="Theme not found")
        correct_answer_count = 0
        for answer in answers:
            if answer["is_correct"]:
                correct_answer_count += 1
        if correct_answer_count == 0:
            raise HTTPBadRequest(text="no correct answer")

        if correct_answer_count > 1:
            raise HTTPBadRequest(text="Too many correct answers")

        if len(answers) == 0:
            raise HTTPBadRequest(text="No answers")

        if len(answers) == 1:
            raise HTTPBadRequest(text="Only one answer")
        question = await self.store.quizzes.create_question(title=title,
                                                            theme_id=theme_id,
                                                            answers=answers)
        return json_response(data=QuestionSchema().dump(question))

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class QuestionListView(View):
    @docs(tags=['question'],
          summary='List all questions',
          description='List all questions')
    @response_schema(QuestionListSchema, 200)
    @check_auth
    async def get(self):
        questions = await self.store.quizzes.list_questions()
        data = {"questions": questions}
        dd = QuestionListSchemaTemp().dump(data)
        return json_response(data=dd)

    async def post(self):
        raise HTTPMethodNotAllowed("post", ["get"], text="not implemented")
