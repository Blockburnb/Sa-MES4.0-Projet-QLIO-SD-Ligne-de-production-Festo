import os
from datetime import datetime, timedelta, time
from html import escape

import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Configuration de la page (Mode Large + Dark Mode)
st.set_page_config(
    page_title="Maquette MES 4.0 - T'EleFan", 
    layout="wide",
    initial_sidebar_state="expanded"
)


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
    st.session_state.theme = "dark"  # dark ou light

# Appliquer le thème CSS
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
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            :root { --primary-color: #1f77b4; --background-color: #ffffff; --secondary-background-color: #f8f9fa; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
            [data-testid="stAppViewContainer"] h1,
            [data-testid="stAppViewContainer"] h2,
            [data-testid="stAppViewContainer"] h3,
            [data-testid="stAppViewContainer"] h4,
            [data-testid="stAppViewContainer"] h5,
            [data-testid="stAppViewContainer"] h6 {
                color: #1f2328;
            }
            [data-testid="stSidebar"] { background-color: #f6f8fa !important; border-right: 1px solid #d0d7de; }
            [data-testid="stSidebar"] > div:first-child { background-color: #f6f8fa !important; }
        </style>
    """, unsafe_allow_html=True)


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

    # Evite l'affichage de textes "undefined" sur certains graphiques sans titre explicite.
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
    # Priorite aux donnees de production (Start/End), fallback sur les logs machine.
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

# Vérifier si une navigation est demandée depuis Admin
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    st.session_state["current_page"] = target

# Initialiser la page courante
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Connexion"

page = st.sidebar.radio("Navigation", ["Connexion", "Temps Réel (Opérateur)", "Stockage", "Robot", "Qualité", "Admin"], 
                        index=["Connexion", "Temps Réel (Opérateur)", "Stockage", "Robot", "Qualité", "Admin"].index(st.session_state["current_page"]))

# Mettre à jour la page courante si l'utilisateur a changé la sélection
st.session_state["current_page"] = page
st.sidebar.markdown("---")

# Filtres Globaux
st.sidebar.subheader("🔍 Filtres")
date_range = st.sidebar.date_input("Période d'analyse", [datetime.now() - timedelta(days=7), datetime.now()])
site = st.sidebar.selectbox("Site", ["Tous", "Site A - Festo", "Site B"])

with st.sidebar.expander("Connexion SQL", expanded=False):
    db_host = st.text_input("Hôte", value=os.getenv("DB_HOST", "localhost"))
    db_port = st.text_input("Port", value=os.getenv("DB_PORT", "3306"))
    db_user = st.text_input("Utilisateur", value=os.getenv("DB_USER", "example_user"))
    db_password = st.text_input("Mot de passe", value=os.getenv("DB_PASSWORD", "example_password"), type="password")
    db_name = st.text_input("Base", value=os.getenv("DB_NAME", "MES4"))

db_config = get_db_config(db_host, db_port, db_user, db_password, db_name)
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
    if st.button(f"Thème {'🌙' if st.session_state.theme == 'dark' else '☀️'}", key="theme_toggle", width='stretch'):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.button("Déconnexion", key="sidebar_logout", width='stretch')
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Header commun pour toutes les pages (sauf connexion)
def display_header():
    col1, col2 = st.columns([8, 2])
    with col2:
        st.markdown("<div style='text-align: right;'><strong>Groupe 6</strong><br><em>Admin</em></div>", unsafe_allow_html=True)


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
    # Date/Heure en haut à gauche
    now = datetime.now()
    jour_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    st.markdown(f"**{jour_fr[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')}**")
    
    # Centrer le formulaire
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("## 🔒 Authentification")
        st.text_input("Identifiant", placeholder="ex: benoit.riou")
        st.text_input("Mot de passe", type="password")
        st.button("SE CONNECTER", type="primary", width='stretch')
        
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
    render_progress_kpi(
        st,
        "🔋 Autonomie Robot",
        f"{autonomie_restante}% Restant",
        f"{autonomie_utilisee}% Utilisé",
        autonomie_restante,
    )
    
    # KPI 2 : OF Réalisés
    pct_of_fait = (of_realises / of_total) * 100
    of_restants = max(of_total - of_realises, 0)
    render_progress_kpi(
        st,
        "✅ OF Réalisés (Jour)",
        f"{of_realises} Réalisés",
        f"{of_restants} Restants" if of_restants > 0 else "",
        pct_of_fait,
    )
    
    # KPI 3 : Production
    pct_prod_fait = (production_realisee / production_objectif) * 100
    render_progress_kpi(
        st,
        "📱 Production (Unités)",
        f"{production_realisee} unités",
        f"Objectif: {production_objectif}" if pct_prod_fait < 100 else "",
        min(pct_prod_fait, 100),
    )
    
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
    
    # Section Stockage
    st.markdown("### 📦 Stockage")
    with st.container():
        col_stock1, col_stock2 = st.columns(2)
        
        with col_stock1:
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
            st.plotly_chart(gauge_fig, width='stretch')
        
        with col_stock2:
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
            st.plotly_chart(fig_movements, width='stretch')

# PAGE 4: ROBOT
elif page == "Robot":
    display_header()
    
    st.title("🤖 Robotino")
    
    # Section Robot
    st.markdown("### 🤖 Robotino")
    with st.container():
        col_robot1, col_robot2 = st.columns(2)
        
        with col_robot1:
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
            st.plotly_chart(fig_mixed, width='stretch')
        
        with col_robot2:
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
            st.plotly_chart(fig_distance, width='stretch')

# PAGE 5: ADMIN
elif page == "Admin":
    display_header()

    if st.session_state.theme == "dark":
        st.markdown("""
            <style>
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
    
    st.title("📊 Gestion de Production (Admin)")

    st.subheader("📋 Récapitulatif des 15 KPIs")
    def set_nav_target(dest_page: str) -> None:
        st.session_state["nav_target"] = dest_page

    kpi_rows = [
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

    # Initialiser les droits d'accès si nécessaire
    if "kpi_permissions" not in st.session_state:
        st.session_state["kpi_permissions"] = {
            label: ["Admin", "Opérateur"] for label, _ in kpi_rows
        }

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
                st.button(label, key=f"kpi_nav_{label}", on_click=set_nav_target, args=(dest,), width='stretch')
            with col_perms:
                current_perms = st.session_state["kpi_permissions"][label]
                selected_perms = st.multiselect(
                    "Rôles",
                    ["Admin", "Opérateur", "Superviseur", "Chef de production"],
                    default=current_perms,
                    key=f"kpi_perms_{label}",
                    label_visibility="collapsed"
                )
                st.session_state["kpi_permissions"][label] = selected_perms
            with col_data:
                st.write("SQL")
    
    # Rerun après avoir défini la cible
    if "nav_target" in st.session_state:
        st.rerun()

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
        
        with p2:
            st.markdown("**Production détaillée de la semaine**")
            prod_detail = pd.DataFrame({
                "OBJ/PDP": [150, 120, 100, 170, 180],
                "Réel": [120, 120, 90, 160, 180],
                "Écart": [30, 0, 10, 10, 0]
            }, index=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"])
            render_table_card(p2, prod_detail)
        
        st.divider()
        
        # Ligne 2: KPI 10 + KPI 11
        p3, p4 = st.columns([1, 1])
        
        with p3:
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
            st.plotly_chart(fig_occupation, width='stretch')
        
        with p4:
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
            st.plotly_chart(fig_cycle, width='stretch')
    
    # ===== COLONNE DROITE: QUALITÉ =====
    with col_qual:
        st.markdown("### Qualité")
        
        # KPI 12: Nombre de NC
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
        st.plotly_chart(fig_nc, width='stretch')
        
        st.divider()
        
        # KPI 13 + KPI 14 (côte à côte)
        q1, q2 = st.columns([2.5, 1])
        
        with q1:
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
            st.plotly_chart(fig_causes, width='stretch')
        
        with q2:
            st.markdown("**Taux de conforme**")
            taux_conforme = get_taux_conforme(db_config, start_dt, end_dt)
            render_kpi_card(q2, "Conforme", f"{taux_conforme:.0f}%", value_color="#00cc00", value_size=48)
        
        st.divider()
        
        # KPI 15
        st.markdown("**Moyenne de la consommation d'énergie**")
        conso_energie = get_conso_energie(db_config, start_dt, end_dt)
        render_kpi_card(st, "Consommation moyenne", f"{conso_energie:.0f} kW/h", value_color="#1f77b4", value_size=32)
