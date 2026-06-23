#!/usr/bin/env bash
#
# One-shot PostgreSQL bootstrap for GuardianIQ.
#
# Because the postgres superuser password is unknown, this script temporarily
# switches loopback authentication in pg_hba.conf to "trust", which lets it
# connect without a password. It then:
#   1. sets a known postgres superuser password (Guardian@123)
#   2. creates the application role (guardianiq_user) and database (guardianiq)
#   3. restores pg_hba.conf to its original (secure) state
#
# Must be run as root because pg_hba.conf is owned by the postgres OS user:
#     sudo bash setup_db.sh
#
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "[ERROR] This script must be run with sudo:  sudo bash $0"
  exit 1
fi

PGVER="${PGVER:-18}"
PGHOME="/Library/PostgreSQL/${PGVER}"
PGDATA="${PGHOME}/data"
PGBIN="${PGHOME}/bin"
HBA="${PGDATA}/pg_hba.conf"

SUPERPW="Guardian@123"
APPUSER="guardianiq_user"
APPPW="guardianiq123"
APPDB="guardianiq"

if [ ! -f "$HBA" ]; then
  echo "[ERROR] Could not find $HBA"
  echo "        Set the correct version with:  sudo PGVER=<version> bash $0"
  exit 1
fi

psql_super() {
  sudo -u postgres "${PGBIN}/psql" -h localhost -v ON_ERROR_STOP=1 "$@"
}

echo "[INFO] Backing up pg_hba.conf -> ${HBA}.bak"
cp "$HBA" "${HBA}.bak"

# Ensure we always restore the original file, even if something fails midway.
restore_hba() {
  echo "[INFO] Restoring original pg_hba.conf..."
  cp "${HBA}.bak" "$HBA"
  sudo -u postgres "${PGBIN}/pg_ctl" -D "$PGDATA" reload || true
}
trap restore_hba EXIT

echo "[INFO] Temporarily enabling 'trust' auth on loopback connections..."
sed -i '' -E 's#^(host[[:space:]]+all[[:space:]]+all[[:space:]]+(127\.0\.0\.1/32|::1/128)[[:space:]]+).*#\1trust#' "$HBA"

echo "[INFO] Reloading PostgreSQL configuration..."
sudo -u postgres "${PGBIN}/pg_ctl" -D "$PGDATA" reload
sleep 2

echo "[INFO] Setting postgres superuser password to '${SUPERPW}'..."
psql_super -d postgres -c "ALTER USER postgres PASSWORD '${SUPERPW}';"

echo "[INFO] Creating application role '${APPUSER}'..."
psql_super -d postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${APPUSER}') THEN
    CREATE ROLE ${APPUSER} LOGIN PASSWORD '${APPPW}';
  ELSE
    ALTER ROLE ${APPUSER} WITH LOGIN PASSWORD '${APPPW}';
  END IF;
END
\$\$;
SQL

echo "[INFO] Creating database '${APPDB}' (if missing)..."
if ! psql_super -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${APPDB}';" | grep -q 1; then
  psql_super -d postgres -c "CREATE DATABASE ${APPDB} OWNER ${APPUSER};"
fi

echo "[INFO] Ensuring ownership and schema privileges..."
psql_super -d postgres -c "ALTER DATABASE ${APPDB} OWNER TO ${APPUSER};"
psql_super -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${APPDB} TO ${APPUSER};"
psql_super -d "${APPDB}" -c "ALTER SCHEMA public OWNER TO ${APPUSER};"
psql_super -d "${APPDB}" -c "GRANT ALL ON SCHEMA public TO ${APPUSER};"

# restore_hba runs here via the EXIT trap.
echo
echo "[SUCCESS] postgres password is now '${SUPERPW}'."
echo "[SUCCESS] Database '${APPDB}' and user '${APPUSER}' are ready."
echo "          pg_hba.conf has been restored to its original secure settings."
