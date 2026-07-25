import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from app import models  # noqa: F401
from app.config import settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name:
    fileConfig(config.config_file_name)

def configure(connection=None) -> None:
    context.configure(connection=connection, url=None if connection else settings.database_url, target_metadata=Base.metadata, compare_type=True, literal_binds=connection is None)
    with context.begin_transaction():
        context.run_migrations()

async def run_online() -> None:
    engine = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(configure)
    await engine.dispose()

if context.is_offline_mode():
    configure()
else:
    asyncio.run(run_online())
