from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.db.session import Base

from app.db.base import *

# Safe Migration Monkeypatching
from alembic.operations import Operations
import sqlalchemy as sa

orig_drop_index = Operations.drop_index
def safe_drop_index(self, *args, **kwargs):
    try:
        index_name = args[0] if len(args) > 0 else kwargs.get('index_name')
        table_name = args[1] if len(args) > 1 else kwargs.get('table_name')
        conn = self.get_bind()
        exists = conn.execute(sa.text(
            "SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relname = :name AND c.relkind = 'i'"
        ), {"name": str(index_name)}).scalar()
        if exists:
            return orig_drop_index(self, *args, **kwargs)
        else:
            print(f"[Safe Migrations] Index {index_name} does not exist. Skipping drop.")
    except Exception as e:
        print(f"[Safe Migrations] Error dropping index (args={args}, kwargs={kwargs}): {e}")
Operations.drop_index = safe_drop_index

orig_drop_column = Operations.drop_column
def safe_drop_column(self, *args, **kwargs):
    try:
        table_name = args[0] if len(args) > 0 else kwargs.get('table_name')
        column_name = args[1] if len(args) > 1 else kwargs.get('column_name')
        conn = self.get_bind()
        exists = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ), {"table": str(table_name), "col": str(column_name)}).scalar()
        if exists:
            return orig_drop_column(self, *args, **kwargs)
        else:
            print(f"[Safe Migrations] Column {column_name} on table {table_name} does not exist. Skipping drop.")
    except Exception as e:
        print(f"[Safe Migrations] Error dropping column (args={args}, kwargs={kwargs}): {e}")
Operations.drop_column = safe_drop_column

orig_drop_constraint = Operations.drop_constraint
def safe_drop_constraint(self, *args, **kwargs):
    try:
        name = args[0] if len(args) > 0 else kwargs.get('name')
        table_name = args[1] if len(args) > 1 else kwargs.get('table_name')
        if name is None:
            print(f"[Safe Migrations] Skipping drop_constraint on {table_name} because name is None.")
            return
        conn = self.get_bind()
        exists = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE table_name = :table AND constraint_name = :name"
        ), {"table": str(table_name), "name": str(name)}).scalar()
        if exists:
            return orig_drop_constraint(self, *args, **kwargs)
        else:
            print(f"[Safe Migrations] Constraint {name} on table {table_name} does not exist. Skipping drop.")
    except Exception as e:
        print(f"[Safe Migrations] Error dropping constraint (args={args}, kwargs={kwargs}): {e}")
Operations.drop_constraint = safe_drop_constraint

orig_drop_table = Operations.drop_table
def safe_drop_table(self, *args, **kwargs):
    try:
        table_name = args[0] if len(args) > 0 else kwargs.get('table_name')
        conn = self.get_bind()
        exists = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :table"
        ), {"table": str(table_name)}).scalar()
        if exists:
            return orig_drop_table(self, *args, **kwargs)
        else:
            print(f"[Safe Migrations] Table {table_name} does not exist. Skipping drop.")
    except Exception as e:
        print(f"[Safe Migrations] Error dropping table (args={args}, kwargs={kwargs}): {e}")
Operations.drop_table = safe_drop_table


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
