import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from config.config import setup_config
from db.sqlalchemy_base import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

section = config.config_ini_section
# config.set_section_option(section, "DB_USER", environ.get("DB_USER"))
# config.set_section_option(section, "DB_PASSWORD", environ.get("DB_PASSWORD"))
# config.set_section_option(section, "DB_NAME", environ.get("DB_NAME"))
# config.set_section_option(section, "DB_HOST", environ.get("DB_HOST"))
# config.set_section_option(section, "DB_PORT", environ.get("DB_PORT"))
# print("DB_USER", environ.get("DB_USER"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = db.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_db_conn_URL():
    class Config:
        pass

    config_path = os.path.join(
        Path(__file__).resolve().parent.parent, "config.yml"
    )
    config = Config()
    setup_config(config, config_path=config_path)
    user = config.config.database.user
    password = config.config.database.password
    host = config.config.database.host
    port = config.config.database.port
    db = config.config.database.database
    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    print("db_connection_url: ", db_connection_url)
    return db_connection_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url")
    url = get_db_conn_URL()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    config_ = config.get_section(config.config_ini_section)
    config_["sqlalchemy.url"] = get_db_conn_URL()
    connectable = engine_from_config(
        config_,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
