import streamlit.web.cli as stcli
import os
import re
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Chemins & paramètres Docker / base de données
# ---------------------------------------------------------------------------

def get_base_path():
    """Retourne le dossier racine du projet (deux niveaux au-dessus de ce script)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_project_root():
    """Remonte à la racine du dépôt (deux niveaux au-dessus de dashboard/windows)."""
    return os.path.dirname(os.path.dirname(get_base_path()))


PROJECT_ROOT     = get_project_root()
COMPOSE_FILE     = os.path.join(PROJECT_ROOT, "TELEFAN", "docker-compose.yml")
SQL_DUMP_FILE    = os.path.join(PROJECT_ROOT, "TELEFAN", "FestoMES-2026-03-31.sql")
DB_ROOT_PASSWORD = "example_root_password"
DB_NAME_DEFAULT  = "MES4"

# ---------------------------------------------------------------------------
# Helpers Docker
# ---------------------------------------------------------------------------

def _run(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)


def get_compose_cmd():
    """Retourne la commande docker compose disponible, ou None."""
    try:
        result = _run(["docker", "compose", "version"], capture_output=True)
        if result.returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass
    try:
        result = _run(["docker-compose", "version"], capture_output=True)
        if result.returncode == 0:
            return ["docker-compose"]
    except FileNotFoundError:
        pass
    return None


def docker_running():
    try:
        return _run(["docker", "info"], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def start_docker_stack(compose_cmd):
    print("[INFO] Démarrage des containers Docker...")
    _run(compose_cmd + ["-f", COMPOSE_FILE, "up", "-d"], check=True)


def get_db_container_id(compose_cmd):
    result = _run(
        compose_cmd + ["-f", COMPOSE_FILE, "ps", "-q", "mariadb"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def wait_for_mariadb(container_id, max_attempts=60):
    print("[INFO] Attente de disponibilité de MariaDB...")
    for _ in range(max_attempts):
        result = _run(
            ["docker", "exec", container_id,
             "mariadb-admin", "ping", "-h", "127.0.0.1",
             "-uroot", f"-p{DB_ROOT_PASSWORD}", "--silent"],
            capture_output=True
        )
        if result.returncode == 0:
            print("[INFO] MariaDB est disponible.")
            return True
        time.sleep(2)
    return False


def resolve_db_name(container_id):
    query = (
        "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
        "WHERE SCHEMA_NAME IN ('MES4','mes4') "
        "ORDER BY (SCHEMA_NAME='MES4') DESC LIMIT 1;"
    )
    result = _run(
        ["docker", "exec", container_id,
         "mariadb", "-uroot", f"-p{DB_ROOT_PASSWORD}", "-Nse", query],
        capture_output=True, text=True
    )
    name = result.stdout.strip()
    return name if name else DB_NAME_DEFAULT


def import_sql_if_needed(container_id, target_db):
    count_query = (
        f"SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_schema='{target_db}';"
    )
    result = _run(
        ["docker", "exec", container_id,
         "mariadb", "-uroot", f"-p{DB_ROOT_PASSWORD}", "-Nse", count_query],
        capture_output=True, text=True
    )
    table_count = result.stdout.strip()
    if table_count.isdigit() and int(table_count) > 0:
        print(f"[INFO] Base {target_db} déjà peuplée ({table_count} tables).")
        return

    if not os.path.isfile(SQL_DUMP_FILE):
        print(f"[WARN] Dump SQL introuvable : {SQL_DUMP_FILE}. Import ignoré.")
        return

    print(f"[INFO] Import du dump SQL initial dans {target_db}...")
    _run(
        ["docker", "exec", container_id,
         "mariadb", "-uroot", f"-p{DB_ROOT_PASSWORD}",
         "-e", f"CREATE DATABASE IF NOT EXISTS `{target_db}`;"],
        check=True, capture_output=True
    )

    # Lire le dump, filtrer les directives CREATE/USE/DROP DATABASE
    with open(SQL_DUMP_FILE, "r", encoding="utf-8", errors="replace") as fh:
        sql_content = fh.read()

    filtered = re.sub(
        r'^(?:/\*!40000 DROP DATABASE IF EXISTS[^\n]*\n?'
        r'|CREATE DATABASE[^\n]*\n?'
        r'|USE `[^`]+`;[^\n]*\n?)',
        "",
        sql_content,
        flags=re.MULTILINE
    )

    proc = subprocess.Popen(
        ["docker", "exec", "-i", container_id,
         "mariadb", "-uroot", f"-p{DB_ROOT_PASSWORD}", target_db],
        stdin=subprocess.PIPE
    )
    proc.communicate(input=filtered.encode("utf-8"))
    if proc.returncode != 0:
        print(f"[WARN] L'import SQL s'est terminé avec le code {proc.returncode}.")
    else:
        print("[INFO] Import SQL terminé.")


def setup_database():
    """Lance Docker Compose et importe la base si nécessaire."""
    if not os.path.isfile(COMPOSE_FILE):
        print(f"[WARN] Fichier Docker Compose introuvable : {COMPOSE_FILE}. Étape DB ignorée.")
        return

    if not docker_running():
        print("[WARN] Docker n'est pas disponible. Étape DB ignorée.")
        return

    compose_cmd = get_compose_cmd()
    if compose_cmd is None:
        print("[WARN] Docker Compose introuvable. Étape DB ignorée.")
        return

    try:
        start_docker_stack(compose_cmd)
        container_id = get_db_container_id(compose_cmd)
        if not container_id:
            print("[WARN] Container mariadb non détecté. Import SQL ignoré.")
            return
        if not wait_for_mariadb(container_id):
            print("[WARN] MariaDB n'a pas répondu à temps. Import SQL ignoré.")
            return
        target_db = resolve_db_name(container_id)
        import_sql_if_needed(container_id, target_db)
        print(f"[INFO] Base active : {target_db}")
        # Exporter pour que app.py puisse lire via os.getenv
        os.environ.setdefault("DB_NAME", target_db)
    except Exception as exc:
        print(f"[WARN] Erreur lors de la configuration de la base : {exc}")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_database()

    # Détermine où se trouve app.py (dans le .exe ou dans le dossier normal)
    if getattr(sys, 'frozen', False):
        script_path = os.path.join(sys._MEIPASS, "app.py")
    else:
        script_path = os.path.join(get_base_path(), "app.py")

    # Lance la commande Streamlit pour exécuter app.py
    sys.argv = ["streamlit", "run", script_path, "--global.developmentMode=false", "--browser.gatherUsageStats=false"]
    sys.exit(stcli.main())