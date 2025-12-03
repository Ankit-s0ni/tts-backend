import os
import sys
from logging.config import fileConfig

from alembic import context

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Import app modules
from app import models
from app.db import engine

target_metadata = models.Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
