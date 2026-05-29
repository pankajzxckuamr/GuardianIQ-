from alembic.config import Config
import alembic.command

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
cfg = Config("alembic.ini")
cfg.set_main_option("sqlalchemy.url", URL)
alembic.command.upgrade(cfg, "head")
print("UPGRADE_OK")
