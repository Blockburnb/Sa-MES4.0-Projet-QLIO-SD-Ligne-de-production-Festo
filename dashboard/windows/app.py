import os
import sys  
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, time
from html import escape

import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Configuration de la page (Mode Large + Dark Mode)
st.set_page_config(
    page_title="Maquette MES 4.0 - T'EleFan", 
    page_icon="icone.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MICRO-MODIF 1 : GESTION DU CHEMIN POUR LE .EXE ---
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

AUTH_DB_PATH = os.path.join(get_base_path(), "auth_users.sqlite3")
# --------------------------------------------------------

ROLE_OPTIONS = ["Admin", "Opérateur", "Superviseur", "Chef de production"]
EMPTY_ROLE_SENTINEL = "__NONE__"
KPI_ROWS = [
    ("1. Autonomie Robot", "Temps Réel (Opérateur)"),
    ("2. OF Réalisés", "Temps Réel (Opérateur)"),
    ("3. Production Réalisée", "Temps Réel (Opérateur)"),
    ("4. Taux Occupation Stockage", "Stockage"),
    ("5. Mouvements Stocks", "Stockage"),
    ("6. Historique Autonomie", "Robot"),
    ("7. Distance Parcourue", "Robot"),
    ("8. Production Hebdo", "Qualité"),
    ("9. Production Détaillée", "Qualité"),
    ("10. Occupation Machine", "Qualité"),
    ("11. Temps Cycle & NVA", "Qualité"),
    ("12. Taux Défaut", "Qualité"),
    ("13. Causes NC", "Qualité"),
    ("14. Taux Conforme", "Qualité"),
    ("15. Conso Énergie", "Qualité"),
]

DEFAULT_AUTH_USERS = [
    (
        "user",
        "dbd4b5861d58a4579d2652b2687b8463ce6839bacc1f5cd6b726f2aedfa32b19",
        "mes4-user-salt-v1",
        "Opérateur",
    ),
    (
        "admin",
        "4668d1065a3b747ccfed1f5feb08853fe31d210ce7ba50d6c6ac6bc05f3e394c",
        "mes4-admin-salt-v1",
        "Admin",
    ),
]


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()


def init_auth_db():
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kpi_permissions (
                    kpi_label TEXT NOT NULL,
                    role_name TEXT NOT NULL,
                    PRIMARY KEY (kpi_label, role_name)
                )
                """
            )
            # NOUVEAU : Table Configuration SQL
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            
            conn.executemany(
                """
                INSERT OR IGNORE INTO users (username, password_hash, salt, role)
                VALUES (?, ?, ?, ?)
                """,
                DEFAULT_AUTH_USERS,
            )

            for label, _ in KPI_ROWS:
                has_rows = conn.execute(
                    "SELECT 1 FROM kpi_permissions WHERE kpi_label = ? LIMIT 1",
                    (label,),
                ).fetchone()
                if has_rows is None:
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO kpi_permissions (kpi_label, role_name)
                        VALUES (?, ?)
                        """,
                        [(label, role) for role in ROLE_OPTIONS],
                    )
            
            # Insérer paramètres SQL par défaut si vide
            sql_defaults = [("db_host", "localhost"), ("db_port", "3306"), ("db_user", "example_user"), ("db_password", "example_password"), ("db_database", "MES4")]
            for k, v in sql_defaults:
                conn.execute("INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)", (k, v))

            conn.commit()
        return True, ""
    except sqlite3.Error as exc:
        return False, str(exc)

# --- NOUVEAU : FONCTIONS PERSISTANCE SQL ---
def load_db_settings_from_sqlite():
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            rows = conn.execute("SELECT key, value FROM app_config").fetchall()
            if rows:
                return {row[0].replace("db_", ""): row[1] for row in rows}
    except: pass
    return None

def save_db_settings_to_sqlite(settings):
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            for k, v in settings.items():
                conn.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)", (f"db_{k}", v))
            conn.commit()
    except: pass
# ---------------------------------------------


def get_user_record(username):
    user_key = (username or "").strip().lower()
    if not user_key:
        return None
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT username, password_hash, salt, role, is_active
                FROM users
                WHERE username = ?
                """,
                (user_key,),
            ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    return dict(row)


def list_user_records():
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT username, role, is_active, created_at
                FROM users
                ORDER BY username ASC
                """
            ).fetchall()
    except sqlite3.Error:
        return []
    return [dict(row) for row in rows]


def create_user_account(username, password, role):
    user_key = (username or "").strip().lower()
    if not user_key:
        return False, "Identifiant requis."
    if len(user_key) < 3:
        return False, "Identifiant trop court (minimum 3 caractères)."
    if role not in ROLE_OPTIONS:
        return False, "Rôle invalide."
    if not password or len(password) < 4:
        return False, "Mot de passe trop court (minimum 4 caractères)."

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (user_key, password_hash, salt, role),
            )
            conn.commit()
        return True, f"Compte '{user_key}' créé."
    except sqlite3.IntegrityError:
        return False, "Ce compte existe déjà."
    except sqlite3.Error as exc:
        return False, f"Erreur SQL: {exc}"


def update_user_account(username, role, is_active, new_password=None):
    user_key = (username or "").strip().lower()
    if role not in ROLE_OPTIONS:
        return False, "Rôle invalide."

    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            cursor = conn.execute("SELECT username FROM users WHERE username = ?", (user_key,))
            if cursor.fetchone() is None:
                return False, "Compte introuvable."

            conn.execute(
                "UPDATE users SET role = ?, is_active = ? WHERE username = ?",
                (role, 1 if is_active else 0, user_key),
            )

            if new_password:
                if len(new_password) < 4:
                    return False, "Nouveau mot de passe trop court (minimum 4 caractères)."
                salt = secrets.token_hex(16)
                password_hash = hash_password(new_password, salt)
                conn.execute(
                    "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
                    (password_hash, salt, user_key),
                )

            conn.commit()
        return True, f"Compte '{user_key}' mis à jour."
    except sqlite3.Error as exc:
        return False, f"Erreur SQL: {exc}"


def authenticate_user(username, password):
    if not AUTH_DB_READY:
        return None
    user = get_user_record(username)
    if not user or int(user.get("is_active", 0)) != 1:
        return None
    computed = hash_password(password or "", user["salt"])
    if not hmac.compare_digest(computed, user["password_hash"]):
        return None
    return {"username": user["username"], "role": user["role"]}


def logout_user():
    st.session_state["is_authenticated"] = False
    st.session_state["auth_user"] = ""
    st.session_state["auth_role"] = ""
    st.session_state["current_page"] = "Connexion"


def ensure_kpi_permissions():
    if AUTH_DB_READY:
        st.session_state["kpi_permissions"] = load_kpi_permissions_from_db()
        return
    st.session_state["kpi_permissions"] = {
        label: ROLE_OPTIONS.copy() for label, _ in KPI_ROWS
    }


def load_kpi_permissions_from_db():
    permissions = {label: [] for label, _ in KPI_ROWS}
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT kpi_label, role_name
                FROM kpi_permissions
                """
            ).fetchall()
    except sqlite3.Error:
        return {label: ROLE_OPTIONS.copy() for label, _ in KPI_ROWS}

    for row in rows:
        label = row["kpi_label"]
        role_name = row["role_name"]
        if label not in permissions:
            continue
        if role_name in ROLE_OPTIONS:
            permissions[label].append(role_name)

    return permissions


def save_kpi_permissions_for_label(kpi_label, roles):
    if not AUTH_DB_READY:
        return
    filtered_roles = [role for role in roles if role in ROLE_OPTIONS]
    try:
        with sqlite3.connect(AUTH_DB_PATH) as conn:
            conn.execute("DELETE FROM kpi_permissions WHERE kpi_label = ?", (kpi_label,))
            if filtered_roles:
                conn.executemany(
                    "INSERT INTO kpi_permissions (kpi_label, role_name) VALUES (?, ?)",
                    [(kpi_label, role) for role in filtered_roles],
                )
            else:
                conn.execute(
                    "INSERT INTO kpi_permissions (kpi_label, role_name) VALUES (?, ?)",
                    (kpi_label, EMPTY_ROLE_SENTINEL),
                )
            conn.commit()
    except sqlite3.Error:
        pass


def has_kpi_access(kpi_label):
    if not st.session_state.get("is_authenticated", False):
        return False
    role = st.session_state.get("auth_role", "")
    allowed_roles = st.session_state.get("kpi_permissions", {}).get(kpi_label, ROLE_OPTIONS)
    return role in allowed_roles


def render_kpi_access_denied(target, kpi_label):
    target.warning(f"Accès refusé à l'indicateur: {kpi_label}")


AUTH_DB_READY, AUTH_DB_ERROR = init_auth_db()


def normalize_date_range(date_range_value):
    if isinstance(date_range_value, (list, tuple)) and len(date_range_value) == 2:
        start_date, end_date = date_range_value
    else:
        start_date = date_range_value
        end_date = date_range_value
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    return start_dt, end_dt


def get_db_config(host, port, user, password, database):
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database,
    }


@st.cache_data(ttl=60)
def can_connect(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        conn.close()
        return True, ""
    except mysql.connector.Error as exc:
        return False, str(exc)


@st.cache_data(ttl=60)
def query_df(sql, params, db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        try:
            return pd.read_sql(sql, conn, params=params)
        finally:
            conn.close()
    except mysql.connector.Error:
        return pd.DataFrame()


def query_scalar(sql, params, db_config, default=0):
    df = query_df(sql, params, db_config)
    if df.empty:
        return default
    value = df.iloc[0, 0]
    return default if value is None else value

# Initialiser session_state pour refresh des données et thème
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.theme = "dark"  

if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = ""
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = ""
if "db_settings" not in st.session_state:
    saved_settings = load_db_settings_from_sqlite()
    if saved_settings:
        st.session_state["db_settings"] = saved_settings
    else:
        st.session_state["db_settings"] = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "3306"),
            "user": os.getenv("DB_USER", "example_user"),
            "password": os.getenv("DB_PASSWORD", "example_password"),
            "database": os.getenv("DB_NAME", "MES4"),
        }

ensure_kpi_permissions()

# --- CSS MODIFIÉ POUR CORRIGER LE THÈME CLAIR (INCLUANT PAGE ADMIN) ---
if st.session_state.theme == "dark":
    st.markdown("""
        <style>
            :root { --primary-color: #1f77b4; --background-color: #0e1117; --secondary-background-color: #161b22; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
            [data-testid="stHeader"] { background-color: #0d1117 !important; }
            [data-testid="stToolbar"] { background-color: #0d1117 !important; }
            [data-testid="stAppViewContainer"] h1,
            [data-testid="stAppViewContainer"] h2,
            [data-testid="stAppViewContainer"] h3,
            [data-testid="stAppViewContainer"] h4,
            [data-testid="stAppViewContainer"] h5,
            [data-testid="stAppViewContainer"] h6 {
                color: #e6edf3;
            }
            [data-testid="stAppViewContainer"] p,
            [data-testid="stAppViewContainer"] li,
            [data-testid="stAppViewContainer"] label,
            [data-testid="stAppViewContainer"] span {
                color: #c9d1d9;
            }
            [data-testid="stAppViewContainer"] small,
            [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
                color: #9da7b3 !important;
            }
            [data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #2d333b; }
            [data-testid="stSidebar"] > div:first-child { background-color: #0d1117 !important; }
            [data-testid="stSidebar"] * { color: #c9d1d9; }
            [data-testid="stSidebar"] hr { border-color: #2d333b !important; }
            [data-testid="stSidebar"] [data-baseweb="input"] > div,
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] [data-baseweb="textarea"] > div {
                background-color: #11151c !important;
                border-color: #2d333b !important;
                color: #c9d1d9 !important;
            }
            [data-testid="stMain"] div[data-testid="stButton"] > button {
                background-color: #11151c;
                color: #c9d1d9;
                border: 1px solid #444;
            }
            [data-testid="stMain"] div[data-testid="stButton"] > button:hover {
                border-color: #1f77b4;
                color: #ffffff;
            }
            [data-testid="stMain"] div[data-baseweb="select"] > div {
                background-color: #11151c !important;
                border-color: #444 !important;
                color: #c9d1d9 !important;
            }
            [data-testid="stMain"] span[data-baseweb="tag"] {
                background-color: #1b2430 !important;
                color: #c9d1d9 !important;
                border: 1px solid #444;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            :root { --primary-color: #1f77b4; --background-color: #ffffff; --secondary-background-color: #f8f9fa; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
            [data-testid="stHeader"] { background-color: #f6f8fa !important; }
            [data-testid="stToolbar"] { background-color: #f6f8fa !important; }
            [data-testid="stAppViewContainer"] h1,
            [data-testid="stAppViewContainer"] h2,
            [data-testid="stAppViewContainer"] h3,
            [data-testid="stAppViewContainer"] h4,
            [data-testid="stAppViewContainer"] h5,
            [data-testid="stAppViewContainer"] h6 {
                color: #1f2328;
            }
            [data-testid="stAppViewContainer"] p,
            [data-testid="stAppViewContainer"] li,
            [data-testid="stAppViewContainer"] label,
            [data-testid="stAppViewContainer"] span {
                color: #1f2328;
            }
            [data-testid="stAppViewContainer"] small,
            [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
                color: #57606a !important;
            }
            [data-testid="stSidebar"] { background-color: #f6f8fa !important; border-right: 1px solid #d0d7de; }
            [data-testid="stSidebar"] > div:first-child { background-color: #f6f8fa !important; }
            [data-testid="stSidebar"] * { color: #1f2328; }
            [data-testid="stSidebar"] hr { border-color: #d0d7de !important; }
            [data-testid="stSidebar"] [data-baseweb="input"] > div,
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] [data-baseweb="textarea"] > div {
                background-color: #ffffff !important;
                border-color: #d0d7de !important;
                color: #1f2328 !important;
            }
            /* Corriger les boutons dans tout le corps principal (y compris Admin) */
            [data-testid="stMain"] div[data-testid="stButton"] > button {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
            }
            [data-testid="stMain"] div[data-testid="stButton"] > button:hover {
                border-color: #1f77b4;
                color: #1f77b4;
            }
            [data-testid="stMain"] div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                border-color: #d0d7de !important;
                color: #1f2328 !important;
            }
            [data-testid="stMain"] span[data-baseweb="tag"] {
                background-color: #eaeef2 !important;
                color: #1f2328 !important;
                border: 1px solid #d0d7de;
            }
            /* Boutons Sidebar */
            [data-testid="stSidebar"] div[data-testid="stButton"] > button {
                background-color: #ffffff;
                color: #1f2328;
                border: 1px solid #d0d7de;
            }
            /* Icônes en haut à droite ("Deploy", Menu) */
            [data-testid="stHeader"] * {
                color: #1f2328 !important;
                fill: #1f2328 !important;
            }
        </style>
    """, unsafe_allow_html=True)
# ---------------------------------------------------------------

def get_theme_tokens():
    if st.session_state.theme == "dark":
        return {
            "card_bg": "#0d1117",
            "card_border": "#444",
            "label": "#888",
            "text": "#c9d1d9",
            "progress_bg": "#2d333b",
        }
    return {
        "card_bg": "#ffffff",
        "card_border": "#d0d7de",
        "label": "#57606a",
        "text": "#1f2328",
        "progress_bg": "#eaeef2",
    }


THEME = get_theme_tokens()


def render_kpi_card(target, label, value, value_color="#1f77b4", value_size=32):
    target.markdown(
        f"""
        <div style="border: 1px solid {THEME['card_border']}; background-color: {THEME['card_bg']}; border-radius: 5px; padding: 16px; text-align: center;">
            <div style="color: {THEME['label']}; font-size: 12px; margin-bottom: 8px;">{label}</div>
            <div style="font-size: {value_size}px; color: {value_color}; font-weight: bold;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_kpi(target, title, left_text, right_text, left_pct, left_color="#00cc00", right_color="#cc0000"):
    left_width = max(0.0, min(100.0, float(left_pct)))
    right_width = max(0.0, 100.0 - left_width)
    title_safe = escape(str(title))
    left_text_safe = escape(str(left_text))
    right_text_safe = escape(str(right_text))
    right_block = ""
    if right_width > 0 or right_text_safe:
        right_block = (
            f"<div style=\"width: {right_width}%; background-color: {right_color}; display: flex; align-items: center; "
            f"justify-content: center; color: white; font-weight: bold;\">{right_text_safe}</div>"
        )
    html = (
        f"<div style=\"border: 1px solid {THEME['card_border']}; background-color: {THEME['card_bg']}; border-radius: 5px; padding: 12px; margin-bottom: 20px;\">"
        f"<div style=\"text-align: center; color: {THEME['text']}; font-weight: bold; font-size: 18px; margin-bottom: 10px;\">{title_safe}</div>"
        f"<div style=\"width: 100%; height: 48px; background-color: {THEME['progress_bg']}; border-radius: 5px; overflow: hidden; display: flex;\">"
        f"<div style=\"width: {left_width}%; background-color: {left_color}; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;\">{left_text_safe}</div>"
        f"{right_block}"
        "</div>"
        "</div>"
    )
    target.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_table_card(target, df):
    header_bg = "#11151c" if st.session_state.theme == "dark" else "#f6f8fa"
    table_html = df.to_html(index=True, border=0)
    target.markdown(
        f"""
        <div style="border: 1px solid {THEME['card_border']}; background-color: {THEME['card_bg']}; border-radius: 5px; padding: 10px;">
            <style>
                .kpi-table-wrap table {{ width: 100%; border-collapse: collapse; color: {THEME['text']}; }}
                .kpi-table-wrap th {{ background-color: {header_bg}; color: {THEME['text']}; border: 1px solid {THEME['card_border']}; padding: 8px; text-align: center; }}
                .kpi-table-wrap td {{ background-color: {THEME['card_bg']}; color: {THEME['text']}; border: 1px solid {THEME['card_border']}; padding: 8px; text-align: center; }}
            </style>
            <div class="kpi-table-wrap">{table_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_plot_theme(fig):
    legend_bg = "rgba(13, 17, 23, 0.92)" if st.session_state.theme == "dark" else "rgba(255, 255, 255, 0.96)"
    legend_border = "#2d333b" if st.session_state.theme == "dark" else "#d0d7de"
    fig.update_layout(
        paper_bgcolor=THEME["card_bg"],
        plot_bgcolor=THEME["card_bg"],
        font=dict(color=THEME["text"]),
        title_font_color=THEME["text"],
        legend_font_color=THEME["text"],
        legend_bgcolor=legend_bg,
        legend_bordercolor=legend_border,
        legend_borderwidth=1,
        xaxis=dict(
            title_font=dict(color=THEME["text"]),
            tickfont=dict(color=THEME["text"]),
        ),
        yaxis=dict(
            title_font=dict(color=THEME["text"]),
            tickfont=dict(color=THEME["text"]),
        ),
        yaxis2=dict(
            title_font=dict(color=THEME["text"]),
            tickfont=dict(color=THEME["text"]),
        ),
    )
    fig.update_xaxes(gridcolor="#2d333b" if st.session_state.theme == "dark" else "#e5e7eb")
    fig.update_yaxes(gridcolor="#2d333b" if st.session_state.theme == "dark" else "#e5e7eb")

    title_text = getattr(getattr(fig.layout, "title", None), "text", None)
    if title_text is None or str(title_text).strip().lower() == "undefined":
        fig.update_layout(title_text="")

    for axis_name in ("xaxis", "yaxis", "xaxis2", "yaxis2"):
        axis = getattr(fig.layout, axis_name, None)
        if axis is None:
            continue
        axis_title_text = getattr(getattr(axis, "title", None), "text", None)
        if axis_title_text is None or str(axis_title_text).strip().lower() == "undefined":
            fig.update_layout(**{f"{axis_name}_title_text": ""})

    return fig


@st.cache_data(ttl=300)
def get_available_data_period(db_config):
    prod_df = query_df(
        """
        SELECT MIN(dt) AS min_dt, MAX(dt) AS max_dt
        FROM (
            SELECT Start AS dt FROM tblfinorderpos WHERE Start IS NOT NULL
            UNION ALL
            SELECT End AS dt FROM tblfinorderpos WHERE End IS NOT NULL
        ) t
        """,
        (),
        db_config,
    )
    if not prod_df.empty and pd.notna(prod_df.loc[0, "min_dt"]) and pd.notna(prod_df.loc[0, "max_dt"]):
        return pd.to_datetime(prod_df.loc[0, "min_dt"]), pd.to_datetime(prod_df.loc[0, "max_dt"])

    machine_df = query_df(
        "SELECT MIN(TimeStamp) AS min_dt, MAX(TimeStamp) AS max_dt FROM tblmachinereport",
        (),
        db_config,
    )
    if not machine_df.empty and pd.notna(machine_df.loc[0, "min_dt"]) and pd.notna(machine_df.loc[0, "max_dt"]):
        return pd.to_datetime(machine_df.loc[0, "min_dt"]), pd.to_datetime(machine_df.loc[0, "max_dt"])

    return None, None

# Simulation Sidebar
st.sidebar.title("📱 T'EleFan MES")

db_settings = st.session_state["db_settings"]
date_range = [datetime.now() - timedelta(days=7), datetime.now()]
site = "Tous"
start_dt, end_dt = normalize_date_range(date_range)
db_config = get_db_config(
    db_settings["host"],
    db_settings["port"],
    db_settings["user"],
    db_settings["password"],
    db_settings["database"],
)

# Vérifier si une navigation est demandée depuis Admin
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    st.session_state["current_page"] = target

# Initialiser la page courante
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Connexion"

if not st.session_state["is_authenticated"]:
    page = "Connexion"
    st.session_state["current_page"] = "Connexion"
    st.sidebar.markdown("---")
    if AUTH_DB_READY:
        st.sidebar.info("Connectez-vous pour accéder au dashboard.")
    else:
        st.sidebar.error(f"Base de comptes indisponible : {AUTH_DB_ERROR}")
    st.sidebar.markdown("---")
    if st.sidebar.button(f"Thème {'🌙' if st.session_state.theme == 'dark' else '☀️'}", key="theme_toggle_login", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
else:
    allowed_pages = ["Temps Réel (Opérateur)", "Stockage", "Robot", "Qualité"]
    if st.session_state["auth_role"] == "Admin":
        allowed_pages.append("Admin")

    if st.session_state["current_page"] not in allowed_pages:
        st.session_state["current_page"] = allowed_pages[0]

    page = st.sidebar.radio(
        "Navigation",
        allowed_pages,
        index=allowed_pages.index(st.session_state["current_page"]),
    )
    st.session_state["current_page"] = page
    st.sidebar.markdown("---")

    # Filtres Globaux
    st.sidebar.subheader("🔍 Filtres")
    date_range = st.sidebar.date_input("Période d'analyse", [datetime.now() - timedelta(days=7), datetime.now()])
    site = st.sidebar.selectbox("Site", ["Tous", "Site A - Festo", "Site B"])

    with st.sidebar.expander("Connexion SQL", expanded=False):
        if st.session_state["auth_role"] == "Admin":
            db_host = st.text_input("Hôte", value=db_settings["host"], key="db_host_input")
            db_port = st.text_input("Port", value=db_settings["port"], key="db_port_input")
            db_user = st.text_input("Utilisateur", value=db_settings["user"], key="db_user_input")
            db_password = st.text_input("Mot de passe", value=db_settings["password"], type="password", key="db_password_input")
            db_name = st.text_input("Base", value=db_settings["database"], key="db_name_input")
            if st.button("Appliquer configuration SQL", key="save_db_settings", use_container_width=True):
                # --- NOUVEAU : Sauvegarde Locale Automatique ---
                new_settings = {
                    "host": db_host,
                    "port": db_port,
                    "user": db_user,
                    "password": db_password,
                    "database": db_name,
                }
                st.session_state["db_settings"] = new_settings
                save_db_settings_to_sqlite(new_settings)
                st.success("Configuration SQL sauvegardée localement.")
                st.rerun()
        else:
            st.caption("Configuration SQL verrouillée (Admin uniquement).")
            st.write(f"Hôte: {db_settings['host']}")
            st.write(f"Port: {db_settings['port']}")
            st.write(f"Utilisateur: {db_settings['user']}")
            st.write(f"Base: {db_settings['database']}")

    db_settings = st.session_state["db_settings"]
    db_config = get_db_config(
        db_settings["host"],
        db_settings["port"],
        db_settings["user"],
        db_settings["password"],
        db_settings["database"],
    )

    db_ok, db_error = can_connect(db_config)
    if not db_ok:
        st.sidebar.warning(f"Connexion SQL impossible : {db_error}")
        sql_status = "Hors ligne"
        sql_color = "#cc0000"
        data_period_text = "Indisponible"
    else:
        sql_status = "Connecté"
        sql_color = "#00aa00"
        available_start, available_end = get_available_data_period(db_config)
        if available_start is not None and available_end is not None:
            data_period_text = f"{available_start.strftime('%d/%m/%Y')} - {available_end.strftime('%d/%m/%Y')}"
        else:
            data_period_text = "Aucune donnée"

    start_dt, end_dt = normalize_date_range(date_range)

    render_kpi_card(st.sidebar, "Statut SQL", sql_status, value_color=sql_color, value_size=20)
    render_kpi_card(st.sidebar, "Période des données", data_period_text, value_color="#1f77b4", value_size=16)

    st.sidebar.markdown("---")

    # Gestion du thème et déconnexion (centrés)
    st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        if st.button(f"Thème {'🌙' if st.session_state.theme == 'dark' else '☀️'}", key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
        if st.button("Déconnexion", key="sidebar_logout", use_container_width=True):
            logout_user()
            st.rerun()
        # --- MICRO-MODIF 2 : BOUTON QUITTER ---
        if st.button("❌ Quitter", key="sidebar_quit", use_container_width=True):
            os._exit(0)
        # ----------------------------------------
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Header commun pour toutes les pages (sauf connexion)
def display_header():
    col1, col2 = st.columns([8, 2])
    with col2:
        user = st.session_state.get("auth_user", "-")
        role = st.session_state.get("auth_role", "-")
        st.markdown(f"<div style='text-align: right;'><strong>{user}</strong><br><em>{role}</em></div>", unsafe_allow_html=True)


def get_autonomie_robot(db_config, start_dt, end_dt):
    sql = """
        SELECT
            SUM(CASE WHEN ErrorL0 = 1 OR ErrorL1 = 1 OR ErrorL2 = 1 THEN 1 ELSE 0 END) AS errors,
            COUNT(*) AS total
        FROM tblmachinereport
        WHERE TimeStamp BETWEEN %s AND %s
    """
    df = query_df(sql, (start_dt, end_dt), db_config)
    if df.empty:
        return 0
    errors = df.loc[0, "errors"] or 0
    total = df.loc[0, "total"] or 0
    if total == 0:
        return 0
    return round(100 * (1 - (errors / total)))


def get_of_counts(db_config, start_dt, end_dt):
    of_realises = query_scalar(
        "SELECT COUNT(*) FROM tblfinorder WHERE End IS NOT NULL AND End BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    of_total = query_scalar(
        "SELECT COUNT(*) FROM tblfinorder WHERE PlannedStart BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    return int(of_realises), max(int(of_total), int(of_realises), 1)


def get_production_counts(db_config, start_dt, end_dt):
    production_realisee = query_scalar(
        "SELECT COUNT(*) FROM tblfinorderpos WHERE End IS NOT NULL AND End BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    production_objectif = query_scalar(
        "SELECT COUNT(*) FROM tblfinorderpos WHERE PlannedStart BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    production_realisee = int(production_realisee)
    production_objectif = int(production_objectif)
    if production_objectif <= 0:
        production_objectif = max(production_realisee, 1)
    return production_realisee, production_objectif


def get_stock_occupation(db_config):
    sql = """
        SELECT
            SUM(CASE WHEN PNo > 0 OR Booked = 1 THEN 1 ELSE 0 END) AS used,
            COUNT(*) AS total
        FROM tblbufferpos
    """
    df = query_df(sql, (), db_config)
    if df.empty:
        return 0
    used = df.loc[0, "used"] or 0
    total = df.loc[0, "total"] or 0
    if total == 0:
        return 0
    return round(100 * used / total)


def get_stock_movements(db_config, start_dt, end_dt):
    entries = query_df(
        """
        SELECT DATE(Start) AS day, COUNT(*) AS entries
        FROM tblfinorderpos
        WHERE Start BETWEEN %s AND %s
        GROUP BY DATE(Start)
        """,
        (start_dt, end_dt),
        db_config,
    )
    exits = query_df(
        """
        SELECT DATE(End) AS day, COUNT(*) AS exits
        FROM tblfinorderpos
        WHERE End BETWEEN %s AND %s
        GROUP BY DATE(End)
        """,
        (start_dt, end_dt),
        db_config,
    )

    days = pd.date_range(start=start_dt.date(), end=end_dt.date(), freq="D")
    movements = pd.DataFrame({"Jour": days})
    movements["day"] = movements["Jour"].dt.date

    if not entries.empty:
        entries["day"] = pd.to_datetime(entries["day"]).dt.date
        movements = movements.merge(entries, on="day", how="left")
    else:
        movements["entries"] = 0

    if not exits.empty:
        exits["day"] = pd.to_datetime(exits["day"]).dt.date
        movements = movements.merge(exits, on="day", how="left")
    else:
        movements["exits"] = 0

    movements["entries"] = movements.get("entries", 0).fillna(0).astype(int)
    movements["exits"] = movements.get("exits", 0).fillna(0).astype(int)
    return movements[["entries", "exits"]].rename(columns={"entries": "Entrées", "exits": "Sorties"})


def get_production_hebdo(db_config, start_dt, end_dt):
    production_hebdo = query_scalar(
        "SELECT COUNT(*) FROM tblfinorderpos WHERE End IS NOT NULL AND End BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    return int(production_hebdo)


def get_taux_conforme(db_config, start_dt, end_dt):
    total = query_scalar(
        "SELECT COUNT(*) FROM tblfinorderpos WHERE End BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
    )
    conforme = query_scalar(
        "SELECT COUNT(*) FROM tblfinorderpos WHERE End BETWEEN %s AND %s AND Error = 0",
        (start_dt, end_dt),
        db_config,
    )
    total = int(total)
    conforme = int(conforme)
    if total == 0:
        return 0
    return round(100 * conforme / total)


def get_conso_energie(db_config, start_dt, end_dt):
    moyenne = query_scalar(
        "SELECT AVG(ElectricEnergyReal) FROM tblfinstep WHERE End BETWEEN %s AND %s",
        (start_dt, end_dt),
        db_config,
        default=0,
    )
    try:
        moyenne = float(moyenne)
    except (TypeError, ValueError):
        moyenne = 0
    return moyenne

# PAGE 1: CONNEXION
if page == "Connexion":
    if st.session_state["is_authenticated"]:
        st.success("Vous êtes déjà connecté.")
        st.stop()

    # Date/Heure en haut à gauche
    now = datetime.now()
    jour_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    st.markdown(f"**{jour_fr[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')}**")
    
    # Centrer le formulaire
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("## 🔒 Authentification")
        st.caption(f"Base des comptes: {AUTH_DB_PATH}")
        if not AUTH_DB_READY:
            st.error(f"Impossible d'accéder à la base des comptes: {AUTH_DB_ERROR}")
            st.stop()
        with st.form("login_form"):
            username = st.text_input("Identifiant", placeholder="user ou admin")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("SE CONNECTER", type="primary", use_container_width=True)

        if submitted:
            auth_result = authenticate_user(username, password)
            if auth_result is None:
                st.error("Identifiant ou mot de passe invalide.")
            else:
                st.session_state["is_authenticated"] = True
                st.session_state["auth_user"] = auth_result["username"]
                st.session_state["auth_role"] = auth_result["role"]
                st.session_state["current_page"] = "Temps Réel (Opérateur)"
                st.success(f"Connexion réussie ({auth_result['role']}).")
                st.rerun()
        
        # Mot de passe oublié en bas à droite
        st.markdown("<div style='text-align: right;'><a href='#'>Mot de passe oublié ?</a></div>", unsafe_allow_html=True)

# PAGE 2: TEMPS RÉEL
elif page == "Temps Réel (Opérateur)":
    display_header()
    
    st.title("🏭 Suivi Production - Temps Réel")
    st.info(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Données SQL (nouvelles valeurs à chaque changement de page)
    autonomie_restante = get_autonomie_robot(db_config, start_dt, end_dt)
    autonomie_utilisee = 100 - autonomie_restante
    of_realises, of_total = get_of_counts(db_config, start_dt, end_dt)
    production_realisee, production_objectif = get_production_counts(db_config, start_dt, end_dt)
    
    # KPIs verticaux avec barres personnalisées
    # KPI 1 : Autonomie Robot
    if has_kpi_access("1. Autonomie Robot"):
        render_progress_kpi(
            st,
            "🔋 Autonomie Robot",
            f"{autonomie_restante}% Restant",
            f"{autonomie_utilisee}% Utilisé",
            autonomie_restante,
        )
    else:
        render_kpi_access_denied(st, "1. Autonomie Robot")
    
    # KPI 2 : OF Réalisés
    pct_of_fait = (of_realises / of_total) * 100
    of_restants = max(of_total - of_realises, 0)
    if has_kpi_access("2. OF Réalisés"):
        render_progress_kpi(
            st,
            "✅ OF Réalisés (Jour)",
            f"{of_realises} Réalisés",
            f"{of_restants} Restants" if of_restants > 0 else "",
            pct_of_fait,
        )
    else:
        render_kpi_access_denied(st, "2. OF Réalisés")
    
    # KPI 3 : Production
    pct_prod_fait = (production_realisee / production_objectif) * 100
    if has_kpi_access("3. Production Réalisée"):
        render_progress_kpi(
            st,
            "📱 Production (Unités)",
            f"{production_realisee} unités",
            f"Objectif: {production_objectif}" if pct_prod_fait < 100 else "",
            min(pct_prod_fait, 100),
        )
    else:
        render_kpi_access_denied(st, "3. Production Réalisée")
    
    st.markdown("### ⚠️ Alertes en cours")
    if autonomie_restante < 30:
        st.error("🔴 ALERTE : Batterie robot critique (<30%)")
    elif autonomie_restante < 50:
        st.warning("🟠 ATTENTION : Batterie robot faible (30-50%)")
    elif production_realisee < (production_objectif * 0.5):
        st.warning("⚠️ Production en retard par rapport à l'objectif")
    else:
        st.success("✅ Aucune alerte critique. Ligne nominale.")

# PAGE 3: STOCKAGE
elif page == "Stockage":
    display_header()
    
    st.title("📦 Logistique")
    
    with st.container():
        col_stock1, col_stock2 = st.columns(2)
        
        with col_stock1:
            if has_kpi_access("4. Taux Occupation Stockage"):
                st.subheader("Taux d'occupation de l'espace de stockage")
                occupation = get_stock_occupation(db_config)

                # Jauge demi-cercle simple avec Plotly
                gauge_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=occupation,
                    number={"suffix": "%", "font": {"size": 20}},
                    gauge={
                        "shape": "angular",
                        "axis": {
                            "range": [0, 100],
                            "tickwidth": 1,
                            "tickcolor": "#888",
                            "nticks": 6
                        },
                        "bar": {"color": "#161b22", "thickness": 0.99},
                        "steps": [
                            {"range": [0, 70], "color": "#00aa00"},
                            {"range": [70, 85], "color": "#ff9900"},
                            {"range": [85, 100], "color": "#cc0000"}
                        ],
                    },
                    domain={"x": [0, 1], "y": [0, 1]},
                ))
                gauge_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
                apply_plot_theme(gauge_fig)
                st.plotly_chart(gauge_fig, use_container_width=True)
            else:
                render_kpi_access_denied(st, "4. Taux Occupation Stockage")
        
        with col_stock2:
            if has_kpi_access("5. Mouvements Stocks"):
                st.subheader("Mouvements Stocks (7j)")
                chart_data = get_stock_movements(db_config, start_dt, end_dt)
                fig_movements = go.Figure()
                fig_movements.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data["Entrées"],
                    name="Entrées",
                    line=dict(color="#1f77b4", width=3),
                    mode="lines+markers"
                ))
                fig_movements.add_trace(go.Scatter(
                    x=chart_data.index,
                    y=chart_data["Sorties"],
                    name="Sorties",
                    line=dict(color="#ff7f0e", width=3),
                    mode="lines+markers"
                ))
                fig_movements.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20), hovermode="x")
                apply_plot_theme(fig_movements)
                st.plotly_chart(fig_movements, use_container_width=True)
            else:
                render_kpi_access_denied(st, "5. Mouvements Stocks")

# PAGE 4: ROBOT
elif page == "Robot":
    display_header()
    
    st.title("🤖 Robotino")
    
    with st.container():
        col_robot1, col_robot2 = st.columns(2)
        
        with col_robot1:
            if has_kpi_access("6. Historique Autonomie"):
                st.subheader("Autonomie du Robot")
                temps_utilisation_data = pd.DataFrame({
                    "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
                    "Temps util. (h)": [0.75, 2.0, 1.58, 1.83, 1.42, 1.0, 0.5],
                    "Batterie (%)": [95, 85, 70, 60, 45, 30, 20]
                })

                # Graphique mixte avec Plotly
                fig_mixed = go.Figure()
                fig_mixed.add_trace(go.Bar(
                    x=temps_utilisation_data["Jour"],
                    y=temps_utilisation_data["Temps util. (h)"],
                    name="Temps utilisation (h)",
                    marker_color="#1f77b4",
                    yaxis="y1"
                ))
                fig_mixed.add_trace(go.Scatter(
                    x=temps_utilisation_data["Jour"],
                    y=temps_utilisation_data["Batterie (%)"],
                    name="Batterie restante (%)",
                    line=dict(color="#ff7f0e", width=3),
                    yaxis="y2"
                ))
                fig_mixed.update_layout(
                    title_text="Activité et Batterie",
                    xaxis=dict(title="Jour de la semaine"),
                    yaxis=dict(
                        title=dict(text="Temps utilisation (h)", font=dict(color="#1f77b4")),
                        tickfont=dict(color="#1f77b4")
                    ),
                    yaxis2=dict(
                        title=dict(text="Batterie (%)", font=dict(color="#ff7f0e")),
                        tickfont=dict(color="#ff7f0e"),
                        overlaying="y",
                        side="right"
                    ),
                    hovermode="x unified",
                    height=350,
                    margin=dict(l=40, r=60, t=40, b=85),
                    legend=dict(
                        orientation="h",
                        x=0.5,
                        y=-0.25,
                        xanchor="center",
                        yanchor="top",
                    ),
                )
                apply_plot_theme(fig_mixed)
                st.plotly_chart(fig_mixed, use_container_width=True)
            else:
                render_kpi_access_denied(st, "6. Historique Autonomie")
        
        with col_robot2:
            if has_kpi_access("7. Distance Parcourue"):
                st.subheader("Distance parcourue")
                distance_data = pd.DataFrame({
                    "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
                    "Distance (m)": [120, 350, 600, 850, 1100, 1320, 1450]
                })

                fig_distance = go.Figure()
                fig_distance.add_trace(go.Scatter(
                    x=distance_data["Jour"],
                    y=distance_data["Distance (m)"],
                    name="Distance totale (m)",
                    line=dict(color="#2ca02c", width=3)
                ))
                fig_distance.update_layout(
                    title_text="Distance cumulée",
                    xaxis_title="Jour de la semaine",
                    yaxis_title="Distance (m)",
                    height=350,
                    margin=dict(l=40, r=40, t=40, b=40),
                    hovermode="x"
                )
                apply_plot_theme(fig_distance)
                st.plotly_chart(fig_distance, use_container_width=True)
            else:
                render_kpi_access_denied(st, "7. Distance Parcourue")

# PAGE 5: ADMIN
elif page == "Admin":
    if st.session_state.get("auth_role") != "Admin":
        st.error("Accès refusé : la page Admin est réservée au rôle Admin.")
        st.stop()

    display_header()
    
    st.title("📊 Gestion de Production (Admin)")

    st.subheader("📋 Récapitulatif des 15 KPIs")
    def set_nav_target(dest_page: str) -> None:
        st.session_state["nav_target"] = dest_page

    kpi_rows = KPI_ROWS

    # En-têtes du tableau
    col_label, col_perms, col_data = st.columns([2, 2.5, 0.5])
    with col_label:
        st.markdown(f"<div style='text-align: center; font-size: 12px; font-weight: bold; color: {THEME['label']};'>KPI</div>", unsafe_allow_html=True)
    with col_perms:
        st.markdown(f"<div style='text-align: center; font-size: 12px; font-weight: bold; color: {THEME['label']};'>Droits d'accès</div>", unsafe_allow_html=True)
    with col_data:
        st.markdown(f"<div style='text-align: center; font-size: 12px; font-weight: bold; color: {THEME['label']};'>Données</div>", unsafe_allow_html=True)

    # Lignes du tableau
    table_container = st.container()
    with table_container:
        for label, dest in kpi_rows:
            col_label, col_perms, col_data = st.columns([2, 2.5, 0.5])
            with col_label:
                st.button(label, key=f"kpi_nav_{label}", on_click=set_nav_target, args=(dest,), use_container_width=True)
            with col_perms:
                current_perms = st.session_state["kpi_permissions"][label]
                selected_perms = st.multiselect(
                    "Rôles",
                    ROLE_OPTIONS,
                    default=current_perms,
                    key=f"kpi_perms_{label}",
                    label_visibility="collapsed"
                )
                st.session_state["kpi_permissions"][label] = selected_perms
                if set(selected_perms) != set(current_perms):
                    save_kpi_permissions_for_label(label, selected_perms)
            with col_data:
                st.write("SQL")
    
    # Rerun après avoir défini la cible
    if "nav_target" in st.session_state:
        st.rerun()

    st.divider()
    st.subheader("👤 Gestion des comptes")

    users_data = list_user_records()
    if not users_data:
        st.warning("Aucun compte trouvé dans la base secondaire d'authentification.")
    else:
        users_df = pd.DataFrame(users_data)
        users_df["actif"] = users_df["is_active"].apply(lambda v: "Oui" if int(v) == 1 else "Non")
        users_df = users_df[["username", "role", "actif", "created_at"]]
        users_df.columns = ["Identifiant", "Rôle", "Actif", "Créé le"]
        st.dataframe(users_df, use_container_width=True, hide_index=True)

    col_create, col_manage = st.columns(2)

    with col_create:
        st.markdown("#### Créer un compte")
        with st.form("admin_create_user_form"):
            new_username = st.text_input("Identifiant", placeholder="ex: chef.prod")
            new_password = st.text_input("Mot de passe", type="password")
            confirm_password = st.text_input("Confirmer le mot de passe", type="password")
            new_role = st.selectbox("Rôle", ROLE_OPTIONS, index=ROLE_OPTIONS.index("Opérateur"))
            create_submitted = st.form_submit_button("Créer le compte", type="primary", use_container_width=True)

        if create_submitted:
            if new_password != confirm_password:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                ok, message = create_user_account(new_username, new_password, new_role)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with col_manage:
        st.markdown("#### Modifier un compte")
        if not users_data:
            st.caption("Créez d'abord un compte pour le modifier.")
        else:
            usernames = [u["username"] for u in users_data]
            default_idx = 0
            current_user = st.session_state.get("auth_user", "")
            if current_user in usernames:
                default_idx = usernames.index(current_user)

            with st.form("admin_manage_user_form"):
                selected_username = st.selectbox("Compte", usernames, index=default_idx)
                selected_user = next((u for u in users_data if u["username"] == selected_username), None)
                selected_role = st.selectbox(
                    "Rôle",
                    ROLE_OPTIONS,
                    index=ROLE_OPTIONS.index(selected_user["role"]) if selected_user and selected_user["role"] in ROLE_OPTIONS else ROLE_OPTIONS.index("Opérateur"),
                )
                selected_active = st.checkbox(
                    "Compte actif",
                    value=bool(selected_user and int(selected_user["is_active"]) == 1),
                )
                reset_password = st.text_input("Nouveau mot de passe (optionnel)", type="password")
                update_submitted = st.form_submit_button("Enregistrer les modifications", use_container_width=True)

            if update_submitted:
                if selected_username == current_user and not selected_active:
                    st.error("Vous ne pouvez pas désactiver votre propre compte pendant la session en cours.")
                else:
                    ok, message = update_user_account(
                        selected_username,
                        selected_role,
                        selected_active,
                        new_password=reset_password,
                    )
                    if ok:
                        st.success(message)
                        # Si le rôle du compte courant change, on met à jour la session.
                        if selected_username == current_user:
                            st.session_state["auth_role"] = selected_role
                        st.rerun()
                    else:
                        st.error(message)

# PAGE 6: QUALITÉ
elif page == "Qualité":
    display_header()
    
    st.title("📊 Production Réel vs Prévisionnel | ✨ Qualité")

    quality_dark = st.session_state.theme == "dark"
    quality_card_bg = THEME["card_bg"]
    quality_card_border = THEME["card_border"]
    quality_label = THEME["label"]
    quality_text = THEME["text"]
    
    # Layout 2 colonnes principales
    col_prod, col_qual = st.columns(2, gap="large")
    
    # ===== COLONNE GAUCHE: PRODUCTION =====
    with col_prod:
        st.markdown("### Production réel vs prévisionnel")
        
        # Ligne 1: KPI 8 + KPI 9
        p1, p2 = st.columns([1, 1.5])
        
        with p1:
            if has_kpi_access("8. Production Hebdo"):
                st.markdown("**Production de la semaine**")
                production_hebdo = get_production_hebdo(db_config, start_dt, end_dt)
                objectif_hebdo = 720

                # Cadre 2x2
                st.markdown("""
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                    <div style="border: 1px solid """ + quality_card_border + """; padding: 15px; text-align: center; background-color: """ + quality_card_bg + """; border-radius: 5px;">
                        <div style="color: """ + quality_label + """; font-size: 12px; margin-bottom: 8px;">Réel</div>
                        <div style="font-size: 32px; font-weight: bold; color: #00cc00;">""" + str(production_hebdo) + """</div>
                    </div>
                    <div style="border: 1px solid """ + quality_card_border + """; padding: 15px; text-align: center; background-color: """ + quality_card_bg + """; border-radius: 5px;">
                        <div style="color: """ + quality_label + """; font-size: 12px; margin-bottom: 8px;">OBJ</div>
                        <div style="font-size: 32px; font-weight: bold; color: #1f77b4;">""" + str(objectif_hebdo) + """</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                render_kpi_access_denied(st, "8. Production Hebdo")
        
        with p2:
            if has_kpi_access("9. Production Détaillée"):
                st.markdown("**Production détaillée de la semaine**")
                prod_detail = pd.DataFrame({
                    "OBJ/PDP": [150, 120, 100, 170, 180],
                    "Réel": [120, 120, 90, 160, 180],
                    "Écart": [30, 0, 10, 10, 0]
                }, index=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"])
                render_table_card(p2, prod_detail)
            else:
                render_kpi_access_denied(p2, "9. Production Détaillée")
        
        st.divider()
        
        # Ligne 2: KPI 10 + KPI 11
        p3, p4 = st.columns([1, 1])
        
        with p3:
            if has_kpi_access("10. Occupation Machine"):
                st.markdown("**Taux d'occupation**")
                st.caption("taux d'occupation de la ligne de production")

                occupation_data = pd.DataFrame({
                    "Jour": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"],
                    "Taux": [85, 78, 72, 89, 65]
                })

                fig_occupation = go.Figure()
                fig_occupation.add_trace(go.Bar(
                    x=occupation_data["Jour"],
                    y=occupation_data["Taux"],
                    name="Taux occupation",
                    marker=dict(color="#1f77b4")
                ))
                fig_occupation.add_hline(y=80, line_dash="dash", line_color="red", 
                                         annotation_text="taux", annotation_position="right")
                fig_occupation.update_layout(
                    height=300, margin=dict(l=30, r=30, t=20, b=50),
                    xaxis_title="", yaxis_title="",
                    showlegend=True, hovermode="x", legend=dict(x=0.5, y=-0.3, xanchor="center", yanchor="top", orientation="h")
                )
                apply_plot_theme(fig_occupation)
                st.plotly_chart(fig_occupation, use_container_width=True)
            else:
                render_kpi_access_denied(st, "10. Occupation Machine")
        
        with p4:
            if has_kpi_access("11. Temps Cycle & NVA"):
                st.markdown("**Temps de cycle**")
                st.caption("Les temps de la journée entre NVA et VA")

                cycle_data = pd.DataFrame({
                    "Jour": ["lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
                    "VA": [6, 5, 6, 5, 4],
                    "NVA": [1, 2, 1, 2, 3]
                })

                fig_cycle = go.Figure()
                fig_cycle.add_trace(go.Bar(
                    x=cycle_data["Jour"],
                    y=cycle_data["VA"],
                    name="VA",
                    marker=dict(color="#1f77b4")
                ))
                fig_cycle.add_trace(go.Bar(
                    x=cycle_data["Jour"],
                    y=cycle_data["NVA"],
                    name="NVA",
                    marker=dict(color="#ff7f0e")
                ))
                fig_cycle.update_layout(
                    barmode="stack",
                    height=300, margin=dict(l=30, r=30, t=20, b=50),
                    xaxis_title="", yaxis_title="",
                    showlegend=True, hovermode="x", legend=dict(x=0.5, y=-0.3, xanchor="center", yanchor="top", orientation="h")
                )
                apply_plot_theme(fig_cycle)
                st.plotly_chart(fig_cycle, use_container_width=True)
            else:
                render_kpi_access_denied(st, "11. Temps Cycle & NVA")
    
    # ===== COLONNE DROITE: QUALITÉ =====
    with col_qual:
        st.markdown("### Qualité")
        
        # KPI 12: Nombre de NC
        if has_kpi_access("12. Taux Défaut"):
            st.markdown("**Nombre de NC**")
            nc_data = pd.DataFrame({
                "Jour": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"],
                "NC": [2.5, 1.5, 2.0, 2.5, 1.8]
            })

            fig_nc = go.Figure()

            # Zones de couleur (fond)
            # Zone verte (0 à 2.25)
            fig_nc.add_trace(go.Scatter(
                x=nc_data["Jour"],
                y=[2.25] * len(nc_data),
                fill="tozeroy",
                fillcolor="rgba(0, 204, 0, 0.2)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip"
            ))

            # Zone rouge (2.25 à 3)
            fig_nc.add_trace(go.Scatter(
                x=nc_data["Jour"],
                y=[3] * len(nc_data),
                fill="tonexty",
                fillcolor="rgba(204, 0, 0, 0.2)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip"
            ))

            # Courbe de données
            fig_nc.add_trace(go.Scatter(
                x=nc_data["Jour"],
                y=nc_data["NC"],
                name="NC",
                line=dict(color="#1f77b4", width=3),
                mode="lines+markers",
                marker=dict(size=8)
            ))

            fig_nc.update_layout(
                height=250, margin=dict(l=30, r=30, t=10, b=30),
                xaxis_title="", yaxis_title="",
                yaxis=dict(range=[0, 3]),
                showlegend=False, hovermode="x"
            )
            apply_plot_theme(fig_nc)
            st.plotly_chart(fig_nc, use_container_width=True)
        else:
            render_kpi_access_denied(st, "12. Taux Défaut")
        
        st.divider()
        
        # KPI 13 + KPI 14 (côte à côte)
        q1, q2 = st.columns([2.5, 1])
        
        with q1:
            if has_kpi_access("13. Causes NC"):
                st.markdown("**Causes des NC**")
                causes_data = pd.DataFrame({
                    "Cause": ["Mauvaise couleur", "Mauvaise hauteur", "Autres"],
                    "Pourcentage": [60, 30, 10]
                })

                fig_causes = go.Figure()
                fig_causes.add_trace(go.Bar(
                    x=causes_data["Cause"],
                    y=causes_data["Pourcentage"],
                    name="%",
                    marker=dict(color="#ff7f0e")
                ))
                fig_causes.add_trace(go.Scatter(
                    x=causes_data["Cause"],
                    y=causes_data["Pourcentage"].cumsum(),
                    name="% cumulé",
                    line=dict(color="#888888", width=2),
                    yaxis="y2"
                ))
                fig_causes.update_layout(
                    height=250, margin=dict(l=30, r=30, t=10, b=30),
                    xaxis_title="", yaxis_title="",
                    yaxis2=dict(overlaying="y", side="right"),
                    showlegend=False, hovermode="x"
                )
                apply_plot_theme(fig_causes)
                st.plotly_chart(fig_causes, use_container_width=True)
            else:
                render_kpi_access_denied(q1, "13. Causes NC")
        
        with q2:
            if has_kpi_access("14. Taux Conforme"):
                st.markdown("**Taux de conforme**")
                taux_conforme = get_taux_conforme(db_config, start_dt, end_dt)
                render_kpi_card(q2, "Conforme", f"{taux_conforme:.0f}%", value_color="#00cc00", value_size=48)
            else:
                render_kpi_access_denied(q2, "14. Taux Conforme")
        
        st.divider()
        
        # KPI 15
        if has_kpi_access("15. Conso Énergie"):
            st.markdown("**Moyenne de la consommation d'énergie**")
            conso_energie = get_conso_energie(db_config, start_dt, end_dt)
            render_kpi_card(st, "Consommation moyenne", f"{conso_energie:.0f} kW/h", value_color="#1f77b4", value_size=32)
        else:
            render_kpi_access_denied(st, "15. Conso Énergie")