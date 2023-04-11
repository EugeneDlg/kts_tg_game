import os
from pathlib import Path
import typing
from dataclasses import dataclass

import yaml
from dotenv import load_dotenv

if typing.TYPE_CHECKING:
    from apps.api.app import Application


@dataclass
class SessionConfig:
    key: str


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
    thinking_timer: int
    captain_timer: int
    answer_timer: int
    top_timer: int


@dataclass
class Config:
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    rabbitmq: RabbitMQConfig = None
    game: GameConfig = None


def setup_config(app: "Application", config_path: str):
    # TODO: добавить BotConfig и SessionConfig по данным из config.yml
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    load_dotenv(".env")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", 5432)
    db_name = os.getenv("DB_NAME")
    rabbitmq_host = os.getenv("RABBITMQ_HOST")
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS")

    app.config = Config(
        session=SessionConfig(key=raw_config["session"]["key"]),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
        ),
        database=DatabaseConfig(
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
        ),
        rabbitmq=RabbitMQConfig(
            user=rabbitmq_user,
            password=rabbitmq_pass,
            host=rabbitmq_host,
        ),
        game=GameConfig(
            max_points=raw_config["game"]["max_points"],
            players=raw_config["game"]["players"],
            thinking_timer=raw_config["game"]["thinking_timer"],
            captain_timer=raw_config["game"]["captain_timer"],
            answer_timer=raw_config["game"]["answer_timer"],
            top_timer=raw_config["game"]["top_timer"],
        ),
    )
