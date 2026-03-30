#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="$ROOT_DIR/.venv"
APP_FILE="$ROOT_DIR/eval_3/maquette_simple.py"
COMPOSE_FILE="$ROOT_DIR/TELEFAN/docker-compose.yml"
SQL_DUMP_FILE="$ROOT_DIR/TELEFAN/FestoMES-2025-03-27.sql"

DB_HOST_DEFAULT="localhost"
DB_PORT_DEFAULT="3306"
DB_USER_DEFAULT="example_user"
DB_PASSWORD_DEFAULT="example_password"
DB_NAME_DEFAULT="MES4"
DB_ROOT_PASSWORD="example_root_password"
DB_NAME_RUNTIME="$DB_NAME_DEFAULT"

log() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*"
}

fail() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  fail "Python introuvable. Installe python3 puis relance."
}

get_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return
  fi
  return 1
}

wait_for_mariadb() {
  local container_id="$1"
  local max_attempts=60
  local attempt

  for attempt in $(seq 1 "$max_attempts"); do
    if docker exec "$container_id" mariadb-admin ping -h 127.0.0.1 -uroot "-p${DB_ROOT_PASSWORD}" --silent >/dev/null 2>&1; then
      log "MariaDB est disponible."
      return 0
    fi
    sleep 2
  done

  return 1
}

import_sql_if_needed() {
  local container_id="$1"
  local target_db="$2"
  local table_count

  table_count="$(docker exec "$container_id" mariadb -uroot "-p${DB_ROOT_PASSWORD}" -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${target_db}';" 2>/dev/null || echo "0")"

  if [[ "$table_count" =~ ^[0-9]+$ ]] && (( table_count > 0 )); then
    log "Base ${target_db} deja peuplee (${table_count} tables)."
    return 0
  fi

  if [[ ! -f "$SQL_DUMP_FILE" ]]; then
    warn "Dump SQL introuvable: $SQL_DUMP_FILE. Le dashboard continuera, mais sans import automatique."
    return 0
  fi

  log "Import du dump SQL initial dans ${target_db}..."
  docker exec "$container_id" mariadb -uroot "-p${DB_ROOT_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS \`${target_db}\`;" >/dev/null
  sed -E '/^\/\*!40000 DROP DATABASE IF EXISTS /d; /^CREATE DATABASE /d; /^USE `[^`]+`;/d' "$SQL_DUMP_FILE" \
    | docker exec -i "$container_id" mariadb -uroot "-p${DB_ROOT_PASSWORD}" "${target_db}"
  log "Import SQL termine."
}

resolve_db_name() {
  local container_id="$1"
  local db_name

  db_name="$(docker exec "$container_id" mariadb -uroot "-p${DB_ROOT_PASSWORD}" -Nse "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ('MES4','mes4') ORDER BY (SCHEMA_NAME='MES4') DESC LIMIT 1;" 2>/dev/null || true)"
  if [[ -n "$db_name" ]]; then
    echo "$db_name"
  else
    echo "$DB_NAME_DEFAULT"
  fi
}

start_docker_stack() {
  local compose_cmd
  local db_container_id
  local target_db

  if ! compose_cmd="$(get_compose_cmd)"; then
    warn "Docker Compose introuvable. Lancement sans demarrage automatique de la base."
    return 0
  fi

  if ! docker info >/dev/null 2>&1; then
    warn "Docker est installe mais le daemon ne repond pas. Lancement sans base auto."
    return 0
  fi

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    warn "Fichier compose introuvable: $COMPOSE_FILE. Lancement sans base auto."
    return 0
  fi

  log "Demarrage des containers Docker..."
  $compose_cmd -f "$COMPOSE_FILE" up -d

  db_container_id="$($compose_cmd -f "$COMPOSE_FILE" ps -q mariadb 2>/dev/null || true)"
  if [[ -z "$db_container_id" ]]; then
    warn "Container mariadb introuvable apres demarrage."
    return 0
  fi

  log "Attente de disponibilite de MariaDB..."
  if ! wait_for_mariadb "$db_container_id"; then
    warn "MariaDB n'a pas repondu a temps."
    return 0
  fi

  target_db="$(resolve_db_name "$db_container_id")"
  import_sql_if_needed "$db_container_id" "$target_db"
  DB_NAME_RUNTIME="$(resolve_db_name "$db_container_id")"
  log "Base active detectee: ${DB_NAME_RUNTIME}"
}

setup_python_env() {
  local py_cmd="$1"

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creation de l'environnement virtuel..."
    "$py_cmd" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  log "Mise a jour de pip..."
  python -m pip install --upgrade pip

  log "Installation des dependances Python..."
  python -m pip install streamlit pandas plotly mysql-connector-python
}

launch_dashboard() {
  if [[ ! -f "$APP_FILE" ]]; then
    fail "Fichier dashboard introuvable: $APP_FILE"
  fi

  export DB_HOST="${DB_HOST:-$DB_HOST_DEFAULT}"
  export DB_PORT="${DB_PORT:-$DB_PORT_DEFAULT}"
  export DB_USER="${DB_USER:-$DB_USER_DEFAULT}"
  export DB_PASSWORD="${DB_PASSWORD:-$DB_PASSWORD_DEFAULT}"
  export DB_NAME="${DB_NAME:-$DB_NAME_RUNTIME}"

  log "Dashboard: http://localhost:8501"
  log "phpMyAdmin: http://localhost:8080"
  log "Arret: CTRL+C"
  echo

  python -m streamlit run "$APP_FILE"
}

main() {
  local py_cmd

  py_cmd="$(find_python)"
  log "Python detecte: $py_cmd"

  setup_python_env "$py_cmd"
  start_docker_stack
  launch_dashboard
}

main "$@"
