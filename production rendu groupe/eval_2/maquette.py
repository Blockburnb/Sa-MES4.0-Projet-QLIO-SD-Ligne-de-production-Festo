import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration de la page (Mode Large + Dark Mode)
st.set_page_config(
    page_title="Maquette MES 4.0 - T'EleFan", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser session_state pour refresh des données et thème
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.random_seed = np.random.randint(0, 1000000)
    st.session_state.theme = "dark"  # dark ou light

# Force regeneration des nombres random à chaque page
st.session_state.random_seed = np.random.randint(0, 1000000)
np.random.seed(st.session_state.random_seed)

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
page = st.sidebar.radio("Navigation", ["Connexion", "Temps Réel (Opérateur)", "Stockage & Robot", "Admin / Qualité"])
st.sidebar.markdown("---")

# Filtres Globaux
st.sidebar.subheader("🔍 Filtres")
date_range = st.sidebar.date_input("Période d'analyse", [datetime.now() - timedelta(days=7), datetime.now()])
site = st.sidebar.selectbox("Site", ["Tous", "Site A - Festo", "Site B"])

st.sidebar.markdown("---")

# Gestion du thème et déconnexion (centrés)
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    if st.button(f"Thème {'🌙' if st.session_state.theme == 'dark' else '☀️'}", key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.button("Déconnexion", key="sidebar_logout", use_container_width=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Header commun pour toutes les pages (sauf connexion)
def display_header():
    col1, col2 = st.columns([8, 2])
    with col2:
        st.markdown("<div style='text-align: right;'><strong>Groupe 6</strong><br><em>Admin</em></div>", unsafe_allow_html=True)

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
        st.button("SE CONNECTER", type="primary", use_container_width=True)
        
        # Mot de passe oublié en bas à droite
        st.markdown("<div style='text-align: right;'><a href='#'>Mot de passe oublié ?</a></div>", unsafe_allow_html=True)

# PAGE 2: TEMPS RÉEL
elif page == "Temps Réel (Opérateur)":
    display_header()
    
    st.title("🏭 Suivi Production - Temps Réel")
    st.info(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Générer nombres random (nouvelles valeurs à chaque changement de page)
    autonomie_restante = np.random.randint(50, 95)
    autonomie_utilisee = 100 - autonomie_restante
    of_realises = np.random.randint(8, 16)
    of_total = 16
    production_realisee = np.random.randint(400, 650)
    production_objectif = 720
    
    # KPIs en haut
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("🔋 Autonomie Robot", f"{autonomie_restante}%", f"-{autonomie_utilisee}% utilisé")
    kpi2.metric("✅ OF Réalisés (Jour)", f"{of_realises} / {of_total}", f"{of_total - of_realises} restants")
    kpi3.metric("📱 Production (Unités)", f"{production_realisee}", f"Objectif: {production_objectif}")
    
    st.markdown("### ⚠️ Alertes en cours")
    if autonomie_restante < 30:
        st.error("🔴 ALERTE : Batterie robot critique (<30%)")
    elif autonomie_restante < 50:
        st.warning("🟠 ATTENTION : Batterie robot faible (30-50%)")
    elif production_realisee < (production_objectif * 0.5):
        st.warning("⚠️ Production en retard par rapport à l'objectif")
    else:
        st.success("✅ Aucune alerte critique. Ligne nominale.")

# PAGE 3: STOCKAGE & ROBOT
elif page == "Stockage & Robot":
    display_header()
    
    st.title("📦 Logistique & Robotique")
    
    col_gauche, col_droite = st.columns(2)
    
    with col_gauche:
        st.subheader("Taux d'Occupation Magasin")
        # Simulation Jauge avec zones colorées
        occupation = np.random.randint(45, 95)
        st.progress(occupation / 100)
        
        if occupation < 70:
            st.success(f"✅ {occupation}% Occupé (Zone Verte < 70%)")
        elif occupation < 85:
            st.warning(f"🟠 {occupation}% Occupé (Zone Orange 70-85%)")
        else:
            st.error(f"🔴 {occupation}% Occupé (Zone Rouge > 85%)")
        
        st.markdown("#### Mouvements Stocks (7j)")
        chart_data = pd.DataFrame(np.random.randint(10, 50, size=(7, 2)), columns=['Entrées', 'Sorties'])
        st.line_chart(chart_data)

    with col_droite:
        st.subheader("Monitoring Robotino")
        distance_parcourue = np.random.randint(900, 1500)
        st.metric("📏 Distance Parcourue", f"{distance_parcourue} m")
        
        st.markdown("#### Batterie vs Activité")
        heures_actives = [2, 4, 6, 8, 5]
        charge_batterie = [90, 80, 60, 40, 20]
        chart_robot = pd.DataFrame({
            "Heures Actives": heures_actives,
            "Charge (%)": charge_batterie
        })
        st.bar_chart(chart_robot.set_index("Charge (%)"))
        
        # KPI 6 : Historique Autonomie (graphique combiné)
        st.markdown("#### KPI 6: Historique Autonomie Robot")
        temps_data = pd.DataFrame({
            "Temps (h)": range(1, 11),
            "Batterie (%)": sorted([90, 85, 75, 60, 50, 40, 30, 25, 20, 15], reverse=True),
            "Puissance (W)": np.random.randint(500, 2000, 10)
        })
        st.line_chart(temps_data.set_index("Temps (h)"))

# PAGE 4: ADMIN
elif page == "Admin / Qualité":
    display_header()
    
    st.title("📊 Analyse de Performance (Admin)")
    
    # Ligne 1 : Production Hebdo + Causes NC
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("KPI 8&9: Production Hebdomadaire vs Objectif")
        objectif_hebdo = 720
        production_hebdo = np.random.randint(600, 800)
        
        prod_data = pd.DataFrame({
            "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven"],
            "Réel": np.random.randint(120, 160, 5),
            "Objectif": [144, 144, 144, 144, 144]  # 720/5
        })
        st.bar_chart(prod_data.set_index("Jour"))
        st.metric("📈 Total Hebdo", f"{production_hebdo} unités", f"Objectif: {objectif_hebdo}")
    
    with c2:
        st.subheader("KPI 13: Répartition Causes NC")
        defaut_hauteur = np.random.randint(20, 50)
        defaut_couleur = 100 - defaut_hauteur
        
        st.progress(defaut_hauteur / 100)
        st.caption(f"🔴 Défaut Hauteur : {defaut_hauteur}%")
        st.progress(defaut_couleur / 100)
        st.caption(f"🔵 Défaut Couleur : {defaut_couleur}%")
        st.info("Autres défauts négligeables")
    
    st.divider()
    
    # Ligne 2 : Temps de Cycle & KPIs Qualité
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("KPI 11: Temps de Cycle & NVA")
        cycle_time_data = pd.DataFrame({
            "Ordre": range(1, 6),
            "VA (mn)": [12, 14, 11, 13, 15],
            "NVA Attente (mn)": [3, 2, 4, 2, 1]
        })
        st.bar_chart(cycle_time_data.set_index("Ordre"), width='stretch')
    
    with c4:
        st.subheader("KPIs Qualité")
        taux_rebut = np.random.uniform(1.5, 3.5)
        occupation_machine = np.random.randint(75, 95)
        conso_energie = np.random.uniform(40, 50)
        taux_conforme = np.random.uniform(95, 99)
        
        m1, m2 = st.columns(2)
        m1.metric("Taux Rebuts (KPI 12)", f"{taux_rebut:.1f}%", "Acceptable < 3%")
        m2.metric("Taux Conforme (KPI 14)", f"{taux_conforme:.1f}%", "Objectif > 95%")
        m1.metric("Occupation Machine (KPI 10)", f"{occupation_machine}%", "Objectif > 80%")
        m2.metric("Conso Énergie J-1 (KPI 15)", f"{conso_energie:.1f} kWh", "-5% vs N-1")
    
    st.divider()
    
    # Ligne 3 : Récapitulatif des 15 KPIs
    st.subheader("📋 Récapitulatif des 15 KPIs")
    kpis_summary = pd.DataFrame({
        "KPI": [
            "1. Autonomie Robot",
            "2. OF Réalisés",
            "3. Production Réalisée",
            "4. Taux Occupation Stockage",
            "5. Mouvements Stocks",
            "6. Historique Autonomie",
            "7. Distance Parcourue",
            "8. Production Hebdo",
            "9. Production Détaillée",
            "10. Occupation Machine",
            "11. Temps Cycle & NVA",
            "12. Taux Défaut",
            "13. Causes NC",
            "14. Taux Conforme",
            "15. Conso Énergie"
        ],
        "Statut": ["✅"] * 15,
        "Données": ["Random"] * 15
    })
    st.dataframe(kpis_summary, width='stretch')