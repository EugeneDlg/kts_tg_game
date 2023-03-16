import datetime as dt
from aiohttp_session import get_session
from aiohttp.web_exceptions import HTTPUnauthorized,  HTTPForbidden


class AuthRequiredMixin:
    # TODO: можно использовать эту mixin-заготовку для реализации проверки авторизации во View
    async def check_authentication(self):
        session = await get_session(self.request)
        if session.new:
            raise HTTPUnauthorized
        session_email = session.get("email")
        session_time = session.get("visit_time")
        breakpoint()
        if not all([session_time, session_email]):
            raise HTTPUnauthorized
        delta = dt.timedelta(minutes=1)
        if dt.datetime.now() - dt.datetime.fromtimestamp(session_time) > delta:
            raise HTTPUnauthorized
        user = await self.request.app.store.admins.get_by_email(session_email)
        if user is None:
            raise HTTPForbidden(text="User doesn't exist")
        return user