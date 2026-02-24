import os
from datetime import datetime, timedelta, time

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
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            :root { --primary-color: #1f77b4; --background-color: #ffffff; --secondary-background-color: #f8f9fa; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
        </style>
    """, unsafe_allow_html=True)

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

start_dt, end_dt = normalize_date_range(date_range)

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
    pct_vert = (autonomie_restante / 100) * 100
    pct_rouge = (autonomie_utilisee / 100) * 100
    st.markdown(f"""
        <div style="width: 100%; margin-bottom: 30px;">
            <div style="text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 10px;">
                🔋 Autonomie Robot
            </div>
            <div style="width: 100%; height: 50px; background-color: #333; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: {pct_vert}%; background-color: #00cc00; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {autonomie_restante}% Restant
                </div>
                <div style="width: {pct_rouge}%; background-color: #cc0000; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {autonomie_utilisee}% Utilisé
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # KPI 2 : OF Réalisés
    pct_of_fait = (of_realises / of_total) * 100
    pct_of_reste = ((of_total - of_realises) / of_total) * 100
    st.markdown(f"""
        <div style="width: 100%; margin-bottom: 30px;">
            <div style="text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 10px;">
                ✅ OF Réalisés (Jour)
            </div>
            <div style="width: 100%; height: 50px; background-color: #333; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: {pct_of_fait}%; background-color: #00cc00; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {of_realises} Réalisés
                </div>
                <div style="width: {pct_of_reste}%; background-color: #cc0000; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {of_total - of_realises} Restants
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # KPI 3 : Production
    pct_prod_fait = (production_realisee / production_objectif) * 100
    pct_prod_reste = 100 - pct_prod_fait if pct_prod_fait < 100 else 0
    st.markdown(f"""
        <div style="width: 100%; margin-bottom: 30px;">
            <div style="text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 10px;">
                📱 Production (Unités)
            </div>
            <div style="width: 100%; height: 50px; background-color: #333; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: {min(pct_prod_fait, 100)}%; background-color: #00cc00; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {production_realisee} unités
                </div>
                <div style="width: {pct_prod_reste}%; background-color: #cc0000; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {'Objectif: ' + str(production_objectif) if pct_prod_reste > 0 else ''}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
            st.plotly_chart(gauge_fig, width='stretch')
        
        with col_stock2:
            st.subheader("Mouvements Stocks (7j)")
            chart_data = get_stock_movements(db_config, start_dt, end_dt)
            st.line_chart(chart_data)

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
                margin=dict(l=40, r=60, t=40, b=40)
            )
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
            st.plotly_chart(fig_distance, width='stretch')

# PAGE 5: ADMIN
elif page == "Admin":
    display_header()
    
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
        st.markdown("<div style='text-align: center; font-size: 12px; font-weight: bold; color: #888;'>KPI</div>", unsafe_allow_html=True)
    with col_perms:
        st.markdown("<div style='text-align: center; font-size: 12px; font-weight: bold; color: #888;'>Droits d'accès</div>", unsafe_allow_html=True)
    with col_data:
        st.markdown("<div style='text-align: center; font-size: 12px; font-weight: bold; color: #888;'>Données</div>", unsafe_allow_html=True)

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
                <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px;">
                    <div style="color: #888; font-size: 12px; margin-bottom: 8px;">Réel</div>
                    <div style="font-size: 32px; font-weight: bold; color: #00cc00;">""" + str(production_hebdo) + """</div>
                </div>
                <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px;">
                    <div style="color: #888; font-size: 12px; margin-bottom: 8px;">OBJ</div>
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
            st.dataframe(prod_detail, width='stretch')
        
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
            st.plotly_chart(fig_causes, width='stretch')
        
        with q2:
            st.markdown("**Taux de conforme**")
            taux_conforme = get_taux_conforme(db_config, start_dt, end_dt)
            st.markdown(f"<div style='text-align: center; font-size: 48px; color: #00cc00; font-weight: bold;'>{taux_conforme:.0f}%</div>", 
                       unsafe_allow_html=True)
        
        st.divider()
        
        # KPI 15
        st.markdown("**Moyenne de la consommation d'énergie**")
        conso_energie = get_conso_energie(db_config, start_dt, end_dt)
        st.markdown(f"<div style='text-align: center; font-size: 32px; color: #1f77b4; font-weight: bold;'>{conso_energie:.0f} kW/h</div>", 
                   unsafe_allow_html=True)
