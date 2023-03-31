import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DatabaseConfig:
    user: str
    password: str
    host: str
    port: str
    database: str


@dataclass
class RabbitMQConfig:
    user: str
    password: str
    host: str


@dataclass
class GameConfig:
    max_points: int
    players: int
    thinking_time: int
    captain_time: int
    answer_time: int


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    rabbitmq: RabbitMQConfig = None
    game: GameConfig = None


def setup_config(app: "Application", config_path: str):
    # TODO: добавить BotConfig и SessionConfig по данным из config.yml
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        session=SessionConfig(
            key=raw_config["session"]["key"]
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"]
        ),
        database=DatabaseConfig(
            user=raw_config["database"]["user"],
            password=raw_config["database"]["password"],
            host=raw_config["database"]["host"],
            port=raw_config["database"]["port"],
            database=raw_config["database"]["database"]
        ),
        rabbitmq=RabbitMQConfig(
            user=raw_config["rabbitmq"]["user"],
            password=raw_config["rabbitmq"]["password"],
            host=raw_config["rabbitmq"]["host"],
        ),
        game=GameConfig(
            max_points=raw_config["game"]["max_points"],
            players=raw_config["game"]["players"],
            thinking_time=raw_config["game"]["thinking_time"],
            captain_time=raw_config["game"]["captain_time"],
            answer_time=raw_config["game"]["answer_time"],
        ),
    )
