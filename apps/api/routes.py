from aiohttp.web_app import Application


def setup_routes(app: Application):
    from apps.admin.routes import setup_routes as admin_setup_routes
    from apps.game.routes import setup_routes as game_setup_routes

    admin_setup_routes(app)
    game_setup_routes(app)
