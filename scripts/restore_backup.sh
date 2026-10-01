#!/usr/bin/env bash
# Restores an encrypted backup into a database.
#
# Usage: scripts/restore_backup.sh <backup.dump.age> <target_database_url>
# Env:   AGE_IDENTITY_FILE  path to the age private key file (required)
#
# The target should be a NEW, empty database (a new Neon project or branch, or the local
# docker one) — verify it before pointing the app at it. See DEPLOY.md > "Backups".
set -euo pipefail

backup="${1:?Usage: $0 <backup.dump.age> <target_database_url>}"
target="${2:?Usage: $0 <backup.dump.age> <target_database_url>}"
: "${AGE_IDENTITY_FILE:?AGE_IDENTITY_FILE is required (path to your age private key)}"

# Show where it is going, without the credentials.
echo "About to restore $backup into: ${target#*@}" >&2
read -r -p "Type 'yes' to continue: " answer
[ "$answer" = "yes" ] || { echo "Aborted." >&2; exit 1; }

dump="$(mktemp)"
trap 'rm -f "$dump"' EXIT

age -d -i "$AGE_IDENTITY_FILE" < "$backup" > "$dump"
# pg_restore must be the same major as the pg_dump that made the backup, or newer.
pg_restore --no-owner --clean --if-exists -d "$target" "$dump"
echo "Restore finished. Check: alembic current, then log in and open an event." >&2
