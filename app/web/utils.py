from typing import Any, Optional
from hashlib import sha256
import json
import datetime as dt
from aiohttp_session import get_session
from aiohttp.web_exceptions import HTTPUnauthorized, HTTPForbidden

from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_response import Response
from app.admin.models import Admin


def json_response(data: Any = None, status: str = "ok") -> Response:
    if data is None:
        data = {}
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
        http_status: int,
        status: str = "error",
        message: Optional[str] = None,
        data: Optional[dict] = None,
):
    if data is None:
        data = {}
    return aiohttp_json_response(
        status=http_status,
        data={
            'status': status,
            'message': str(message),
            'data': data,
        })


def error_text(exception):
    if not hasattr(exception, "text") or len(exception.text) == 0:
        return str(exception)
    try:
        json_text = json.loads(exception.text)
    except Exception:
        return str(exception.text)
    return json_text


def error_reason(exception):
    if not hasattr(exception, "reason"):
        return str(exception)
    return exception.reason


async def authenticate(email: str, password: str, app: "Application") -> Optional[Admin]:
    user = await app.store.admins.get_by_email(email)
    if user is None:
        raise HTTPForbidden(text='No such user')
    password_ = sha256(password.encode()).hexdigest()
    if password_ != user.password:
        raise HTTPForbidden(text='Wrong password')
    return user


def check_auth(func):
    async def wrapper(self, *args, **kwargs):
        session = await get_session(self.request)
        if session.new:
            raise HTTPUnauthorized
        session_email = session.get("email")
        session_time = session.get("visit_time")
        if not all([session_time, session_email]):
            raise HTTPUnauthorized
        delta = dt.timedelta(days=1)
        if dt.datetime.now() - dt.datetime.fromtimestamp(session_time) > delta:
            raise HTTPUnauthorized
        user = await self.request.app.store.admins.get_by_email(session_email)
        if user is None:
            raise HTTPForbidden(text="User doesn't exist")
        self.current_user = user
        data = await func(self, *args, **kwargs)
        return data
    return wrapper