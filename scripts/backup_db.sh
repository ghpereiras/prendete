#!/usr/bin/env bash
# Dumps the database, validates the dump and encrypts it with age.
# Prints the path of the encrypted file on stdout (everything else goes to stderr).
#
# Required env: BACKUP_DATABASE_URL (postgresql://..., direct connection, read-only role),
#               AGE_PUBLIC_KEY (age1...).
# Optional env: OUT_DIR (default: current dir), MIN_DUMP_BYTES (default: 5000),
#               PG_BIN_DIR (directory with the pg_dump/pg_restore to use; needed when several
#               PostgreSQL versions are installed and the default one is too old).
set -euo pipefail

: "${BACKUP_DATABASE_URL:?BACKUP_DATABASE_URL is required}"
: "${AGE_PUBLIC_KEY:?AGE_PUBLIC_KEY is required}"
OUT_DIR="${OUT_DIR:-.}"
MIN_DUMP_BYTES="${MIN_DUMP_BYTES:-5000}"
PG_DUMP="${PG_BIN_DIR:+$PG_BIN_DIR/}pg_dump"
PG_RESTORE="${PG_BIN_DIR:+$PG_BIN_DIR/}pg_restore"

name="prendete-$(date -u +%F).dump.age"
dump="$(mktemp)"
trap 'rm -f "$dump"' EXIT

echo "Dumping database..." >&2
"$PG_DUMP" --version >&2
"$PG_DUMP" -Fc --no-owner --no-privileges "$BACKUP_DATABASE_URL" > "$dump"

size="$(wc -c < "$dump")"
if [ "$size" -lt "$MIN_DUMP_BYTES" ]; then
  echo "Dump is suspiciously small ($size bytes), aborting." >&2
  exit 1
fi
# Fails if the archive can't be read back, so a corrupt dump never gets uploaded.
"$PG_RESTORE" --list < "$dump" > /dev/null

echo "Encrypting ($size bytes)..." >&2
age -r "$AGE_PUBLIC_KEY" < "$dump" > "$OUT_DIR/$name"
echo "$OUT_DIR/$name"
