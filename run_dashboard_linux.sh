#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

REPO_URL="https://github.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo.git"
REPO_BRANCH="main"
PROJECT_DIR="$ROOT_DIR"

VENV_DIR=""
APP_FILE=""
COMPOSE_FILE=""
SQL_DUMP_FILE=""

DB_HOST_DEFAULT="localhost"
DB_PORT_DEFAULT="3306"
DB_USER_DEFAULT="example_user"
DB_PASSWORD_DEFAULT="example_password"
DB_NAME_DEFAULT="MES4"
DB_ROOT_PASSWORD="example_root_password"
DB_NAME_RUNTIME="$DB_NAME_DEFAULT"
DASHBOARD_PORT="8501"
PHPMYADMIN_PORT="8080"
MARIADB_PORT="3306"

update_project_paths() {
  VENV_DIR="$PROJECT_DIR/.venv"
  APP_FILE="$PROJECT_DIR/dashboard/dashboard_final.py"
  COMPOSE_FILE="$PROJECT_DIR/TELEFAN/docker-compose.yml"
  SQL_DUMP_FILE="$PROJECT_DIR/TELEFAN/FestoMES-2025-03-27.sql"
}

update_project_paths

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

ensure_git_sync() {
  local bootstrap_dir="$ROOT_DIR/project_main"
  local current_branch

  if ! command -v git >/dev/null 2>&1; then
    fail "Git introuvable. Installe Git puis relance."
  fi

  if [[ ! -d "$PROJECT_DIR/.git" ]]; then
    if [[ -d "$bootstrap_dir/.git" ]]; then
      PROJECT_DIR="$bootstrap_dir"
      update_project_paths
    else
      if [[ -d "$bootstrap_dir" ]] && [[ -n "$(ls -A "$bootstrap_dir" 2>/dev/null)" ]]; then
        fail "Le dossier de bootstrap Git existe deja et n'est pas vide: $bootstrap_dir"
      fi
      log "Depot Git non detecte. Clonage de la branche ${REPO_BRANCH}..."
      git clone --branch "$REPO_BRANCH" --single-branch "$REPO_URL" "$bootstrap_dir" >/dev/null 2>&1 || fail "Echec du clone Git depuis $REPO_URL"
      PROJECT_DIR="$bootstrap_dir"
      update_project_paths
    fi
  fi

  cd "$PROJECT_DIR"

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    fail "Le dossier projet n'est pas un depot Git valide: $PROJECT_DIR"
  fi

  if ! git diff --quiet || ! git diff --cached --quiet; then
    fail "Synchronisation Git impossible: modifications locales detectees dans $PROJECT_DIR (commit/stash requis)."
  fi

  current_branch="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "$current_branch" != "$REPO_BRANCH" ]]; then
    git checkout "$REPO_BRANCH" >/dev/null 2>&1 || fail "Impossible de basculer sur la branche ${REPO_BRANCH}."
  fi

  log "Synchronisation Git de la branche ${REPO_BRANCH}..."
  if git fetch origin "$REPO_BRANCH" >/dev/null 2>&1; then
    git pull --ff-only origin "$REPO_BRANCH" >/dev/null 2>&1 || fail "Echec du git pull --ff-only sur ${REPO_BRANCH}."
  else
    warn "Impossible de joindre GitHub. Synchronisation Git ignoree, demarrage avec la version locale."
  fi
}

port_in_use() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1
    return
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk 'NR > 1 {print $4}' | grep -Eq "[:.]${port}$"
    return
  fi

  return 1
}

check_required_ports() {
  if port_in_use "$DASHBOARD_PORT"; then
    fail "Le port ${DASHBOARD_PORT} est deja utilise. Ferme le service occupe puis relance."
  fi

  if port_in_use "$PHPMYADMIN_PORT"; then
    warn "Le port ${PHPMYADMIN_PORT} est deja utilise. phpMyAdmin peut ne pas demarrer correctement."
  fi

  if port_in_use "$MARIADB_PORT"; then
    warn "Le port ${MARIADB_PORT} est deja utilise. MariaDB Docker peut ne pas demarrer correctement."
  fi
}

wait_for_http() {
  local url="$1"
  local max_attempts="${2:-60}"
  local attempt

  if ! command -v curl >/dev/null 2>&1; then
    warn "curl introuvable: verification HTTP Streamlit ignoree."
    return 0
  fi

  for attempt in $(seq 1 "$max_attempts"); do
    if curl --silent --show-error --fail --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  return 1
}

open_dashboard_url() {
  local url="$1"

  if [[ -n "${BROWSER:-}" ]]; then
    "$BROWSER" "$url" >/dev/null 2>&1 &
    return 0
  fi

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
    return 0
  fi

  warn "Aucun navigateur detecte automatiquement. Ouvre manuellement: ${url}"
  return 1
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
    fail "Docker/Docker Compose introuvable. Installe Docker Desktop (ou docker + plugin compose) puis relance."
  fi

  if ! docker info >/dev/null 2>&1; then
    fail "Docker est installe mais le daemon ne repond pas. Lance le service Docker puis relance."
  fi

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    fail "Fichier Docker Compose introuvable: $COMPOSE_FILE"
  fi

  log "Demarrage des containers Docker..."
  if ! $compose_cmd -f "$COMPOSE_FILE" up -d; then
    fail "Echec du demarrage Docker Compose. Verifie la configuration dans $COMPOSE_FILE et l'etat de Docker."
  fi

  db_container_id="$($compose_cmd -f "$COMPOSE_FILE" ps -q mariadb 2>/dev/null || true)"
  if [[ -z "$db_container_id" ]]; then
    fail "Container mariadb non detecte apres demarrage. Verifie le service 'mariadb' dans $COMPOSE_FILE puis lance: $compose_cmd -f $COMPOSE_FILE logs mariadb"
  fi

  log "Attente de disponibilite de MariaDB..."
  if ! wait_for_mariadb "$db_container_id"; then
    fail "MariaDB n'a pas repondu a temps. Verifie les logs: $compose_cmd -f $COMPOSE_FILE logs mariadb"
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
  local streamlit_pid
  local health_url
  local dashboard_url

  if [[ ! -f "$APP_FILE" ]]; then
    fail "Fichier dashboard introuvable: $APP_FILE"
  fi

  export DB_HOST="${DB_HOST:-$DB_HOST_DEFAULT}"
  export DB_PORT="${DB_PORT:-$DB_PORT_DEFAULT}"
  export DB_USER="${DB_USER:-$DB_USER_DEFAULT}"
  export DB_PASSWORD="${DB_PASSWORD:-$DB_PASSWORD_DEFAULT}"
  export DB_NAME="${DB_NAME:-$DB_NAME_RUNTIME}"

  dashboard_url="http://localhost:${DASHBOARD_PORT}"
  health_url="${dashboard_url}/_stcore/health"

  log "Dashboard: ${dashboard_url}"
  log "phpMyAdmin: http://localhost:${PHPMYADMIN_PORT}"
  log "Arret: CTRL+C"
  echo

  python -m streamlit run "$APP_FILE" &
  streamlit_pid="$!"

  cleanup() {
    if kill -0 "$streamlit_pid" >/dev/null 2>&1; then
      kill "$streamlit_pid" >/dev/null 2>&1 || true
    fi
  }

  trap cleanup INT TERM

  if wait_for_http "$health_url" 90; then
    log "Streamlit est disponible (${health_url})."
    open_dashboard_url "$dashboard_url" || true
  else
    warn "Streamlit ne repond pas sur ${health_url} apres attente."
  fi

  wait "$streamlit_pid"
}

main() {
  local py_cmd

  ensure_git_sync

  py_cmd="$(find_python)"
  log "Python detecte: $py_cmd"

  check_required_ports
  setup_python_env "$py_cmd"
  start_docker_stack
  launch_dashboard
}

main "$@"
