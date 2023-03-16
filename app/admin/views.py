import time
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp_session import new_session, get_session
from app.web.app import View
from app.web.utils import authenticate, json_response, check_auth
from app.web.mixins import AuthRequiredMixin
from app.admin.schemes import (
    AdminRequestSchema,
    AdminResponseSchema,
    AdminIdResponseSchema
)


class AdminLoginView(View):
    @docs(tags=['admin'],
          summary='Authorization',
          description='Admin authorization')
    @request_schema(AdminRequestSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        data = self.request['data']
        email = data['email']
        password = data['password']
        app = self.request.app
        admin = await authenticate(email, password, app)
        session = await new_session(self.request)
        session["email"] = email
        session["visit_time"] = time.time()
        data_dump = AdminIdResponseSchema().dump(admin)
        json_data = json_response(data=data_dump)
        return json_data

    async def get(self):
        raise HTTPMethodNotAllowed("get", ["post"], text="not implemented")


class AdminCurrentView(View, AuthRequiredMixin):
    @response_schema(AdminResponseSchema, 200)
    @check_auth
    async def get(self):
        return json_response(data=AdminIdResponseSchema().dump(self.current_user))

    async def post(self):
        raise HTTPMethodNotAllowed()