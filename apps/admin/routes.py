import typing

from apps.admin.views import AdminCurrentView

if typing.TYPE_CHECKING:
    from apps.api.app import Application


def setup_routes(app: "Application"):
    from apps.admin.views import AdminLoginView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
