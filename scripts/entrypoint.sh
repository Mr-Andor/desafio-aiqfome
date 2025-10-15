
set -euo pipefail

wait_for_database() {
  if [[ -z "${DB_HOST:-}" ]]; then
    return 0
  fi

  local host="${DB_HOST}"
  local port="${DB_PORT:-5432}"

  echo "Waiting for PostgreSQL at ${host}:${port}..."
  until pg_isready -h "${host}" -p "${port}" >/dev/null 2>&1; do
    sleep 1
  done
}

wait_for_elasticsearch() {
  if [[ -z "${ES_HOST:-}" ]]; then
    return 0
  fi

  echo "Waiting for Elasticsearch at ${ES_HOST}..."
  until curl -s "${ES_HOST}" > /dev/null; do
    sleep 1
  done
}

wait_for_database
wait_for_elasticsearch

python manage.py migrate --noinput

exec "$@"
