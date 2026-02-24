# Final deliverable copy of the maquette UI.
# This file is a fixed and hardened copy for the app rendering.
# Do not edit the original `frontend/maquette.py`.

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import httpx

# Configuration de la page (Mode Large + Dark Mode)
st.set_page_config(
    page_title="Maquette MES 4.0 - T'EleFan (Final)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Helper to try fetch data from backend, fallback to None
try:
    BACKEND_URL = st.secrets.get('BACKEND_URL', 'http://127.0.0.1:8000')
except Exception:
    BACKEND_URL = 'http://127.0.0.1:8000'


def fetch_json(path: str, params: dict | None = None):
    """Synchronous fetch helper. Returns parsed JSON or None on error. Supports query params."""
    url = BACKEND_URL.rstrip('/') + path
    try:
        if params:
            r = httpx.get(url, params=params, timeout=5.0)
        else:
            r = httpx.get(url, timeout=3.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# Initialiser session_state pour refresh des données et thème
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.theme = "dark"  # dark ou light

# Simulation Sidebar
st.sidebar.title("📱 T'EleFan MES - Final")

# Vérifier si une navigation est demandée depuis Admin
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    st.session_state["current_page"] = target

# Initialiser la page courante
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Connexion"

page = st.sidebar.radio(
    "Navigation",
    ["Connexion", "Temps Réel (Opérateur)", "Stockage", "Robot", "Qualité", "Admin"],
    index=["Connexion", "Temps Réel (Opérateur)", "Stockage", "Robot", "Qualité", "Admin"].index(
        st.session_state["current_page"]
    ),
)

# Mettre à jour la page courante si l'utilisateur a changé la sélection
st.session_state["current_page"] = page
st.sidebar.markdown("---")

# Filtres Globaux
st.sidebar.subheader("🔍 Filtres")
date_range = st.sidebar.date_input("Période d'analyse", [datetime.now() - timedelta(days=7), datetime.now()])
site = st.sidebar.selectbox("Site", ["Tous", "Site A - Festo", "Site B"]) 

# Compute filter parameters early so debug UI can access them
sd = None
ed = None
try:
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        sd = date_range[0].isoformat() + "T00:00:00"
        ed = date_range[1].isoformat() + "T23:59:59"
except Exception:
    sd = None
    ed = None
site_param = None if site == "Tous" else site
filter_params = {k: v for k, v in {"start_date": sd, "end_date": ed, "site": site_param, "limit": 500}.items() if v is not None}

# --- Show which days in the selected range have data ---
# Try to fetch a larger set of orders (no date filter) to compute availability by day.
try:
    all_orders_sample = fetch_json('/orders', params={'limit': 5000}) or []
    available_days = set()
    for o in all_orders_sample:
        try:
            # created_at expected in ISO format
            d = o.get('created_at')
            if d:
                available_days.add(d[:10])
        except Exception:
            continue
except Exception:
    all_orders_sample = []
    available_days = set()

# Render a compact day-strip showing which days of the selected range have data
try:
    sd_widget = date_range[0]
    ed_widget = date_range[1]
    days = (ed_widget - sd_widget).days + 1
    day_boxes = []
    for i in range(days):
        day = (sd_widget + timedelta(days=i)).date()
        day_str = day.isoformat()
        has = day_str in available_days
        color = '#2ca02c' if has else '#444'
        label = day.strftime('%d %b')
        day_boxes.append(f"<div style='padding:6px 8px; margin:2px; border-radius:4px; background:{color}; color:white; font-size:11px;' title={'has data' if has else 'no data'}>{label}</div>")
    day_strip_html = "<div style='display:flex; flex-wrap:wrap;'>" + "".join(day_boxes) + "</div>"
    st.sidebar.markdown("<div style='margin-top:10px; font-size:12px; color:#aaa;'>Périodes avec données (vert)</div>", unsafe_allow_html=True)
    st.sidebar.markdown(day_strip_html, unsafe_allow_html=True)
except Exception:
    # ignore visual errors
    pass

# Debug / info about filtered data (toggleable)
if st.sidebar.checkbox("Afficher détails filtre / debug", value=False):
    st.sidebar.markdown("**Paramètres de filtre envoyés au backend :**")
    st.sidebar.write(filter_params)
    try:
        cnt = len(orders_for_display) if isinstance(orders_for_display, list) else 0
        st.sidebar.markdown(f"**Ordres trouvés (filtré) :** {cnt}")
        # compute min/max dates from orders_for_display
        dates = []
        for o in orders_for_display:
            try:
                d = o.get('created_at')
                if d:
                    dates.append(d[:10])
            except Exception:
                continue
        if dates:
            st.sidebar.markdown(f"**Période des ordres :** {min(dates)} → {max(dates)}")
        else:
            st.sidebar.markdown("**Période des ordres :** aucune donnée")
    except Exception:
        st.sidebar.write("Impossible de calculer les détails")
    if st.sidebar.button("Rafraîchir les données"):
        # simple client-side refresh: re-run by setting a session_state value
        st.session_state.last_refresh = datetime.now()
        st.experimental_rerun()

st.sidebar.markdown("---")

# Gestion du thème et déconnexion (centrés)
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    # compute emoji label separately to avoid nested-quote f-string issues
    theme_emoji = '🌙' if st.session_state.theme == 'dark' else '☀️'
    if st.button(f"Thème {theme_emoji}", key="theme_toggle_final"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        # Removed st.experimental_rerun() for compatibility; changing session_state via a widget
        # will cause Streamlit to rerun automatically in supported versions.
    st.button("Déconnexion", key="sidebar_logout_final")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Header commun pour toutes les pages (sauf connexion)
def display_header():
    col1, col2 = st.columns([8, 2])
    with col2:
        st.markdown("<div style='text-align: right;'><strong>Groupe 6</strong><br><em>Admin</em></div>", unsafe_allow_html=True)

# Global connection probe (used by all pages)
# probe the backend once to detect connectivity
orders_global = fetch_json('/orders')
machines_global = fetch_json('/machines')
connected = orders_global is not None

# Build filter params from sidebar date_range and site so they apply to all pages
sd = None
ed = None
try:
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        sd = date_range[0].isoformat() + "T00:00:00"
        ed = date_range[1].isoformat() + "T23:59:59"
except Exception:
    sd = None
    ed = None

site_param = None if site == "Tous" else site
filter_params = {k: v for k, v in {"start_date": sd, "end_date": ed, "site": site_param, "limit": 500}.items() if v is not None}

# Fetch filtered data once (falls back to global probe if filtered fetch fails)
filtered_orders = fetch_json('/orders', params=filter_params)
if filtered_orders is None:
    orders_for_display = orders_global or []
else:
    orders_for_display = filtered_orders

filtered_machines = fetch_json('/machines')
machines_for_display = filtered_machines or machines_global or []

# Derive a deterministic numpy seed from the filtered data so visuals change with filters
try:
    sum_ids = sum([o.get('id', 0) for o in orders_for_display if isinstance(o, dict)])
    machines_count = len(machines_for_display) if isinstance(machines_for_display, list) else 0
    deterministic_seed = (sum_ids + machines_count) % 2_000_000
except Exception:
    deterministic_seed = 42

np.random.seed(int(deterministic_seed))

# Appliquer le thème CSS
if st.session_state.theme == "dark":
    st.markdown(
        """
        <style>
            :root { --primary-color: #1f77b4; --background-color: #0e1117; --secondary-background-color: #161b22; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
            :root { --primary-color: #1f77b4; --background-color: #ffffff; --secondary-background-color: #f8f9fa; }
            [data-testid="stAppViewContainer"] { background-color: var(--secondary-background-color); }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Fetch KPIs once using the current filter params so the UI is consistent
try:
    kpis = fetch_json('/kpis', params=filter_params) or {}
except Exception:
    kpis = {}

# PAGE 1: CONNEXION
if page == "Connexion":
    # Date/Heure en haut à gauche
    now = datetime.now()
    jour_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    st.markdown(f"**{jour_fr[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')}**")

    # Centrer le formulaire
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("## 🔒 Authentification")
        st.text_input("Identifiant", placeholder="ex: benoit.riou")
        st.text_input("Mot de passe", type="password")
        st.button("SE CONNECTER", type="primary")

        # Mot de passe oublié en bas à droite
        st.markdown("<div style='text-align: right;'><a href='#'>Mot de passe oublié ?</a></div>", unsafe_allow_html=True)

# PAGE 2: TEMPS RÉEL
elif page == "Temps Réel (Opérateur)":
    display_header()

    st.title("🏭 Suivi Production - Temps Réel")
    st.info(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Use the pre-fetched filtered data so the whole app is consistent
    orders = orders_for_display
    machines = machines_for_display

    # If not connected, show banner but continue rendering UI
    if not connected:
        show_no_connection_banner()

    # When connected, derive deterministic KPIs from backend data instead of random values
    if connected:
        # Prefer KPI feed when available
        try:
            prod_count_kpi = kpis.get('production_count') if isinstance(kpis, dict) else None
        except Exception:
            prod_count_kpi = None

        # OF réalisés = prefer production_count KPI if provided, else number of orders
        if prod_count_kpi is not None:
            of_realises = int(prod_count_kpi)
        else:
            of_realises = len(orders) if isinstance(orders, list) else 0

        # Production réalisée: prefer explicit KPI (production_count) in units, else estimate
        if prod_count_kpi is not None:
            production_realisee = int(prod_count_kpi)
        else:
            production_realisee = of_realises * 40  # units per order (domain assumption)

        # Autonomy: derive a deterministic value from machines busy flags if available
        autonomie_restante = None
        if isinstance(machines, list) and len(machines) > 0:
            try:
                busy_count = sum(1 for m in machines if bool(m.get('busy') or m.get('Busy') or m.get('busy', False)))
                total_machines = len(machines)
                busy_ratio = busy_count / total_machines
                # Map busy_ratio to autonomy: more busy -> lower remaining battery
                autonomie_restante = max(10, int((1 - busy_ratio) * 100))
            except Exception:
                autonomie_restante = 80
        else:
            # Fallback deterministic value when machines info not available
            autonomie_restante = 80

        # Additional KPIs for display (safe extraction)
        avg_cycle_min = kpis.get('average_cycle_time_min') if isinstance(kpis, dict) else None
        avg_lead_min = kpis.get('average_lead_time_min') if isinstance(kpis, dict) else None
        throughput = kpis.get('throughput_per_day') if isinstance(kpis, dict) else None
        buffer_occ = kpis.get('buffer_occupancy_avg') if isinstance(kpis, dict) else None
        buffer_mov = kpis.get('buffer_movements') if isinstance(kpis, dict) else None
        mach_util = kpis.get('machine_utilization_pct') if isinstance(kpis, dict) else None
        mach_avail = kpis.get('machine_availability_pct') if isinstance(kpis, dict) else None
        yield_pct = kpis.get('yield_pct') if isinstance(kpis, dict) else None
        defect_pct = kpis.get('defect_rate_pct') if isinstance(kpis, dict) else None
        energy_kwh = kpis.get('energy_consumption_kwh') if isinstance(kpis, dict) else None
    else:
        # No connection: use placeholders (None) but keep the page layout
        autonomie_restante = None
        of_realises = None
        production_realisee = None
        avg_cycle_min = avg_lead_min = throughput = buffer_occ = buffer_mov = None
        mach_util = mach_avail = yield_pct = defect_pct = energy_kwh = None

    autonomie_utilisee = None if autonomie_restante is None else 100 - autonomie_restante
    of_total = 16
    production_objectif = 720

    # KPI visuals (same style as maquette) - show placeholders when disconnected
    if not connected:
        # Simple placeholder cards showing the no-connection state
        st.markdown("""
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 10px;">
                <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px; color: #ff6666;">🔋 Autonomie Robot<br><strong>no connection to database</strong></div>
                <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px; color: #ff6666;">✅ OF Réalisés (Jour)<br><strong>no connection to database</strong></div>
                <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px; color: #ff6666;">📱 Production (Unités)<br><strong>no connection to database</strong></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        pct_vert = (autonomie_restante / 100) * 100
        pct_rouge = (autonomie_utilisee / 100) * 100
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

        pct_of_fait = (of_realises / of_total) * 100
        pct_of_reste = ((of_total - of_realises) / of_total) * 100
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

        pct_prod_fait = (production_realisee / production_objectif) * 100
        pct_prod_reste = 100 - pct_prod_fait if pct_prod_fait < 100 else 0
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### ⚠️ Alertes en cours")
    if autonomie_restante is None:
        st.info("Aucune donnée de batterie disponible (backend absent)")
    elif autonomie_restante < 30:
        st.error("🔴 ALERTE : Batterie robot critique (<30%)")
    elif autonomie_restante < 50:
        st.warning("🟠 ATTENTION : Batterie robot faible (30-50%)")
    elif production_realisee is not None and production_realisee < (production_objectif * 0.5):
        st.warning("⚠️ Production en retard par rapport à l'objectif")
    else:
        st.success("✅ Aucune alerte critique. Ligne nominale.")

# PAGE 3: STOCKAGE
elif page == "Stockage":
    display_header()

    # If not connected, show banner but continue rendering UI
    if not connected:
        show_no_connection_banner()

    st.title("📦 Logistique")

    # Section Stockage
    st.markdown("### 📦 Stockage")
    with st.container():
        col_stock1, col_stock2 = st.columns(2)

        with col_stock1:
            st.subheader("Taux d'occupation de l'espace de stockage")
            if connected and isinstance(orders_for_display, list):
                # If KPI available, prefer buffer occupancy KPI
                if buffer_occ is not None:
                    occupation = min(100, int(buffer_occ))
                else:
                    # deterministic occupancy derived from number of filtered orders
                    occupation = min(95, 30 + len(orders_for_display) * 3)
            else:
                # offline placeholder
                occupation = 60

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
            st.plotly_chart(gauge_fig)

        with col_stock2:
            st.subheader("Mouvements Stocks (7j)")
            # deterministic movement values: scale with orders count
            if connected and isinstance(orders_for_display, list):
                base = max(5, len(orders_for_display))
                entries = [base + i for i in range(7)]
                exits = [max(0, base - i // 2) for i in range(7)]
            else:
                entries = [10, 12, 9, 11, 13, 8, 7]
                exits = [5, 6, 7, 5, 8, 6, 4]
            chart_data = pd.DataFrame({"Entrées": entries, "Sorties": exits})
            st.line_chart(chart_data)

# PAGE 4: ROBOT
elif page == "Robot":
    display_header()

    # If not connected, show banner but continue rendering UI
    if not connected:
        show_no_connection_banner()

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
            st.plotly_chart(fig_mixed)

        with col_robot2:
            st.subheader("Distance parcourue")
            # If machine utilization KPI exists, annotate chart title
            title_extra = ""
            if mach_util is not None:
                title_extra = f" — Utilisation machines: {mach_util}%"

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
                title_text="Distance cumulée" + title_extra,
                xaxis_title="Jour de la semaine",
                yaxis_title="Distance (m)",
                height=350,
                margin=dict(l=40, r=40, t=40, b=40),
                hovermode="x"
            )
            st.plotly_chart(fig_distance)

# PAGE 5: ADMIN
elif page == "Admin":
    display_header()

    # If not connected, show banner but continue rendering UI
    if not connected:
        show_no_connection_banner()

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
        st.session_state["kpi_permissions"] = {label: ["Admin", "Opérateur"] for label, _ in kpi_rows}

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
        # mapping from displayed KPI label to backend kpi key
        mapping = {
            "1. Autonomie Robot": None,  # not provided by /kpis (derived from machines)
            "2. OF Réalisés": 'production_count',
            "3. Production Réalisée": 'production_count',
            "4. Taux Occupation Stockage": 'buffer_occupancy_avg',
            "5. Mouvements Stocks": 'buffer_movements',
            "6. Historique Autonomie": None,
            "7. Distance Parcourue": None,
            "8. Production Hebdo": 'throughput_per_day',
            "9. Production Détaillée": None,
            "10. Occupation Machine": 'machine_utilization_pct',
            "11. Temps Cycle & NVA": 'average_cycle_time_min',
            "12. Taux Défaut": 'defect_rate_pct',
            "13. Causes NC": None,
            "14. Taux Conforme": 'yield_pct',
            "15. Conso Énergie": 'energy_consumption_kwh',
        }

        for label, dest in kpi_rows:
            col_label, col_perms, col_data = st.columns([2, 2.5, 0.5])
            with col_label:
                st.button(label, key=f"kpi_nav_{label}", on_click=set_nav_target, args=(dest,))
            with col_perms:
                current_perms = st.session_state["kpi_permissions"][label]
                selected_perms = st.multiselect(
                    "Rôles",
                    ["Admin", "Opérateur", "Superviseur", "Chef de production"],
                    default=current_perms,
                    key=f"kpi_perms_{label}",
                    label_visibility="collapsed",
                )
                st.session_state["kpi_permissions"][label] = selected_perms
            with col_data:
                key = mapping.get(label)
                value = None
                if key is not None and isinstance(kpis, dict):
                    value = kpis.get(key)
                # show derived autonomy/machine values
                if label == "1. Autonomie Robot":
                    display_value = f"{autonomie_restante}%" if autonomie_restante is not None else "—"
                elif label == "6. Historique Autonomie":
                    display_value = "see Robot page"
                elif label == "7. Distance Parcourue":
                    display_value = "see Robot page"
                elif label == "9. Production Détaillée":
                    display_value = "see Qualité page"
                elif label == "13. Causes NC":
                    display_value = "see Qualité page"
                else:
                    if value is None:
                        display_value = "—"
                    else:
                        # format numbers nicely
                        if isinstance(value, float):
                            display_value = f"{value:.2f}"
                        else:
                            display_value = str(value)
                st.write(display_value)

    # Rerun after setting nav_target is unnecessary; button interaction already triggers rerun.
    if "nav_target" in st.session_state:
        # Previously: st.experimental_rerun()
        # Removed for compatibility with Streamlit versions that don't expose experimental_rerun.
        pass

# PAGE 6: QUALITÉ
elif page == "Qualité":
    display_header()

    # If not connected, show banner but continue rendering UI
    if not connected:
        show_no_connection_banner()

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
            # prefer throughput KPI to compute weekly production
            if throughput is not None:
                production_hebdo = int(round(throughput * 7))
            else:
                production_hebdo = np.random.randint(600, 800)
            objectif_hebdo = 720

            # Cadre 2x2
            st.markdown(
                """
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                    <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px;">
                        <div style="color: #888; font-size: 12px; margin-bottom: 8px;">Réel</div>
                        <div style="font-size: 32px; font-weight: bold; color: #00cc00;">""" + str(production_hebdo) + """</div>
                    </div>
                    <div style="border: 1px solid #444; padding: 15px; text-align: center; background-color: #0d1117; border-radius: 5px;">""",
                unsafe_allow_html=True,
            )

# Note: This file is the final corrected copy of the maquette UI. It attempts to fetch from the backend at BACKEND_URL for /orders and /machines but falls back to random/simulated data when the backend is not reachable.
# To run: pip install -r requirements.txt then run `streamlit run frontend/maquette_final.py`.
