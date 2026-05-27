import os
import subprocess

import alembic.command
from alembic.config import Config

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
DUMP_PATH = "tmp_backup.dump"

cfg = Config("alembic.ini")
cfg.set_main_option("sqlalchemy.url", URL)

subprocess.run(["pg_dump", URL, "-Fc", "-f", DUMP_PATH], check=True)
try:
    alembic.command.downgrade(cfg, "base")
    alembic.command.upgrade(cfg, "head")
    subprocess.run(["pg_restore", "--clean", "--if-exists", "--no-owner", "--no-privileges", "-d", URL, DUMP_PATH], check=True)
    print("DOWNGRADE_UPGRADE_OK")
finally:
    if os.path.exists(DUMP_PATH):
        os.remove(DUMP_PATH)
