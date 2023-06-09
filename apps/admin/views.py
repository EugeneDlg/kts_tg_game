import time

from aiohttp.web_exceptions import HTTPMethodNotAllowed
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session

from apps.admin.schemes import (
    AdminIdResponseSchema,
    AdminRequestSchema,
    AdminResponseSchema,
)
from apps.api.app import View
from apps.api.utils import authenticate, check_auth, json_response


class AdminLoginView(View):
    @docs(
        tags=["admin"],
        summary="Authorization",
        description="Admin authorization",
    )
    @request_schema(AdminRequestSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        data = self.request["data"]
        email = data["email"]
        password = data["password"]
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


class AdminCurrentView(View):
    @response_schema(AdminResponseSchema, 200)
    @check_auth
    async def get(self):
        return json_response(
            data=AdminIdResponseSchema().dump(self.current_user)
        )

    async def post(self):
        raise HTTPMethodNotAllowed()
