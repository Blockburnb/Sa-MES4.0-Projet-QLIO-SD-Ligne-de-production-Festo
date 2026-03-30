"""
Script de test des 15 indicateurs du Dashboard T'EleFan MES 4.0
Affiche les résultats dans le terminal sans interface graphique
"""

import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Tuple
import warnings
import sys
import io

# Force UTF-8 encoding for Windows terminal
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')


class MESIndicators:
    """Classe pour calculer les 15 indicateurs MES"""
    
    def __init__(self, db_config: Dict[str, str], csv_robot_path: str):
        """
        Initialise la connexion à la base de données et charge les données CSV
        
        Args:
            db_config: Configuration de connexion MariaDB
            csv_robot_path: Chemin vers robotino_data.csv
        """
        self.db_config = db_config
        self.csv_robot_path = csv_robot_path
        self.conn = None
        self.robot_data = None
        
    def connect_db(self):
        """Établit la connexion à MariaDB"""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            print("✅ Connexion à MariaDB réussie\n")
        except Exception as e:
            print(f"❌ Erreur de connexion à MariaDB: {e}\n")
            raise
    
    def load_robot_data(self):
        """Charge les données du robot depuis le CSV"""
        try:
            self.robot_data = pd.read_csv(self.csv_robot_path)
            print(f"✅ Données robot chargées: {len(self.robot_data)} lignes\n")
        except Exception as e:
            print(f"❌ Erreur de chargement CSV robot: {e}\n")
            raise
    
    def query_db(self, query: str) -> pd.DataFrame:
        """Execute une requête SQL et retourne un DataFrame"""
        try:
            return pd.read_sql(query, self.conn)
        except Exception as e:
            print(f"❌ Erreur lors de la requête SQL: {e}")
            return pd.DataFrame()
    
    # ========== ONGLET 1: TEMPS RÉEL ==========
    
    def indicator_1_autonomie_robot(self) -> Tuple[float, float]:
        """
        1. Autonomie du Robot (Journalier)
        Returns: (batterie_restante_%, batterie_consommee_%)
        """
        print("📊 Indicateur 1: Autonomie du Robot")
        
        if self.robot_data is None:
            print("   ⚠️  Données robot non disponibles")
            return 0.0, 100.0
        
        # Chercher la colonne de batterie (peut avoir différents noms)
        battery_col = None
        for col in ['device_potAccuChargeState_centiPercent', 'battery_level', 'battery']:
            if col in self.robot_data.columns:
                battery_col = col
                break
        
        if battery_col is None:
            print("   ⚠️  Colonne de batterie non trouvée dans les données robot")
            print(f"   📋 Colonnes disponibles: {', '.join(self.robot_data.columns[:5])}...")
            return 0.0, 100.0
        
        # Dernière valeur de batterie (en centiPercent → Pourcentage)
        last_battery = self.robot_data[battery_col].iloc[-1]
        if battery_col == 'device_potAccuChargeState_centiPercent':
            last_battery = last_battery / 100
        
        restante = round(last_battery)
        consommee = round(100 - last_battery)
        
        print(f"   🟢 Batterie restante: {restante}%")
        print(f"   🔴 Batterie consommée: {consommee}%\n")
        
        return restante, consommee
    
    def indicator_2_of_realises(self) -> Tuple[int, int]:
        """
        2. Nombre d'OF Réalisés (Journalier)
        Returns: (of_termines, of_restants)
        """
        print("📊 Indicateur 2: Ordres de Fabrication Réalisés")
        
        query = "SELECT COUNT(*) as total FROM tblfinorder"
        total_of = self.query_db(query)
        
        query_done = """
            SELECT COUNT(*) as done 
            FROM tblfinorder 
            WHERE end IS NOT NULL
        """
        of_done = self.query_db(query_done)
        
        if total_of.empty or of_done.empty:
            print("   ⚠️  Pas de données d'OF disponibles")
            return 0, 0
        
        total = int(total_of['total'].iloc[0])
        done = int(of_done['done'].iloc[0])
        reste = total - done
        
        print(f"   🟢 OF terminés: {done}")
        print(f"   🔴 OF restants: {reste}")
        print(f"   📈 Total: {total}\n")
        
        return done, reste
    
    def indicator_3_production_realisee(self) -> Tuple[int, int]:
        """
        3. Production Réalisée (Journalière)
        Returns: (pieces_finies, pieces_restantes)
        """
        print("📊 Indicateur 3: Production Réalisée")
        
        # Compter le total de pièces dans tblboxpos
        query_total = "SELECT COUNT(*) as total FROM tblboxpos"
        result_total = self.query_db(query_total)
        
        # Compter les OF terminés comme proxy des pièces finies
        query_done = "SELECT COUNT(*) as fini FROM tblfinorder WHERE end IS NOT NULL"
        result_done = self.query_db(query_done)
        
        if result_total.empty:
            print("   ⚠️  Pas de données de production disponibles")
            return 0, 0
        
        total = int(result_total['total'].iloc[0]) if not pd.isna(result_total['total'].iloc[0]) else 0
        fini = int(result_done['fini'].iloc[0]) if not result_done.empty and not pd.isna(result_done['fini'].iloc[0]) else 0
        reste = total - fini if total > fini else 0
        
        print(f"   🟢 Pièces finies: {fini}")
        print(f"   🔴 Pièces restantes: {reste}")
        print(f"   📈 Total prévu: {total}\n")
        
        return fini, reste
    
    # ========== ONGLET 2: STOCKAGE ==========
    
    def indicator_4_taux_occupation(self) -> float:
        """
        4. Taux d'Occupation Stockage
        Returns: taux_occupation_%
        """
        print("📊 Indicateur 4: Taux d'Occupation Stockage")
        
        query_total = "SELECT COUNT(*) as total FROM tblbufferpos"
        query_occupied = """
            SELECT COUNT(*) as occupied 
            FROM tblbufferpos 
            WHERE boxid IS NOT NULL AND boxid != 0
        """
        
        total = self.query_db(query_total)
        occupied = self.query_db(query_occupied)
        
        if total.empty or occupied.empty:
            print("   ⚠️  Pas de données de stockage disponibles")
            return 0.0
        
        total_positions = int(total['total'].iloc[0])
        occupied_positions = int(occupied['occupied'].iloc[0])
        taux = (occupied_positions / total_positions * 100) if total_positions > 0 else 0
        
        status = "🟢" if taux < 70 else "🟠" if taux < 85 else "🔴"
        print(f"   {status} Taux d'occupation: {taux:.1f}%")
        print(f"   📦 Positions occupées: {occupied_positions}/{total_positions}\n")
        
        return taux
    
    def indicator_5_mouvements_stocks(self) -> int:
        """
        5. Mouvements de Stocks
        Returns: nombre_total_mouvements
        """
        print("📊 Indicateur 5: Mouvements de Stocks")
        
        # Approximation: on compte les changements dans tblbufferpos
        query = """
            SELECT COUNT(*) as mouvements 
            FROM tblbufferpos 
            WHERE boxid IS NOT NULL
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de mouvements disponibles")
            return 0
        
        mouvements = int(result['mouvements'].iloc[0])
        print(f"   📊 Mouvements totaux: {mouvements}\n")
        
        return mouvements
    
    # ========== ONGLET 3: ROBOT ==========
    
    def indicator_6_historique_autonomie(self) -> Dict:
        """
        6. Historique Autonomie Robot
        Returns: dict avec moyennes
        """
        print("📊 Indicateur 6: Historique Autonomie Robot")
        
        if self.robot_data is None:
            print("   ⚠️  Données robot non disponibles")
            return {}
        
        if 'device_potAccuChargeState_centiPercent' in self.robot_data.columns:
            avg_battery = self.robot_data['device_potAccuChargeState_centiPercent'].mean() / 100
            print(f"   🔋 Batterie moyenne: {avg_battery:.1f}%")
        
        if 'power_output_current' in self.robot_data.columns:
            avg_current = self.robot_data['power_output_current'].mean()
            print(f"   ⚡ Courant moyen: {avg_current:.2f}A\n")
        
        return {"battery_avg": avg_battery if 'device_potAccuChargeState_centiPercent' in self.robot_data.columns else 0}
    
    def indicator_7_distance_parcourue(self) -> float:
        """
        7. Distance Parcourue
        Returns: distance_en_metres
        """
        print("📊 Indicateur 7: Distance Parcourue")
        
        if self.robot_data is None or 'odometry_x' not in self.robot_data.columns:
            print("   ⚠️  Données d'odométrie non disponibles")
            print(f"   📋 Colonnes disponibles: {', '.join(self.robot_data.columns[:10]) if self.robot_data is not None else 'aucune'}...")
            return 0.0
        
        # Calcul de la distance euclidienne entre points successifs
        x = self.robot_data['odometry_x'].values
        y = self.robot_data['odometry_y'].values
        
        # Retirer les NaN
        mask = ~(np.isnan(x) | np.isnan(y))
        x = x[mask]
        y = y[mask]
        
        if len(x) < 2:
            print("   ⚠️  Pas assez de données d'odométrie valides")
            return 0.0
        
        distances = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
        total_distance = np.sum(distances)
        
        print(f"   🚗 Distance totale: {total_distance:.0f} mètres\n")
        
        return round(total_distance)
    
    # ========== ONGLET 4: PROD / QUALITÉ / ÉNERGIE ==========
    
    def indicator_8_production_hebdo(self, objectif: int = 720) -> Tuple[int, int]:
        """
        8. Production Hebdomadaire
        Returns: (production_reelle, objectif)
        """
        print("📊 Indicateur 8: Production Hebdomadaire")
        
        # Compter les OF terminés comme production
        query = """
            SELECT COUNT(*) as prod 
            FROM tblfinorder 
            WHERE end IS NOT NULL
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de production disponibles")
            return 0, objectif
        
        production = int(result['prod'].iloc[0])
        print(f"   📊 Production réelle: {production}")
        print(f"   🎯 Objectif: {objectif}")
        print(f"   {'✅' if production >= objectif else '❌'} Objectif {'atteint' if production >= objectif else 'non atteint'}\n")
        
        return production, objectif
    
    def indicator_9_production_detaillee(self) -> pd.DataFrame:
        """
        9. Production Détaillée (Semaine)
        Returns: DataFrame avec production par jour
        """
        print("📊 Indicateur 9: Production Détaillée par Jour")
        
        query = """
            SELECT 
                DATE(end) as jour,
                COUNT(*) as production
            FROM tblfinorder
            WHERE end IS NOT NULL
            GROUP BY DATE(end)
            ORDER BY jour DESC
            LIMIT 7
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de production disponibles")
            return pd.DataFrame()
        
        print("   📅 Production par jour:")
        for _, row in result.iterrows():
            print(f"      {row['jour']}: {row['production']} pièces")
        print()
        
        return result
    
    def indicator_10_taux_occupation_machine(self) -> float:
        """
        10. Taux d'Occupation Machine
        Returns: taux_%
        """
        print("📊 Indicateur 10: Taux d'Occupation Machine")
        
        query = """
            SELECT 
                SUM(TIMESTAMPDIFF(SECOND, start, end)) / 3600 as heures_travail
            FROM tblfinorder
            WHERE end IS NOT NULL
        """
        result = self.query_db(query)
        
        if result.empty or pd.isna(result['heures_travail'].iloc[0]):
            print("   ⚠️  Pas de données de temps de travail disponibles")
            return 0.0
        
        heures_travail = float(result['heures_travail'].iloc[0])
        # Hypothèse: 8h/jour * 5 jours = 40h disponibles par semaine
        heures_disponibles = 40
        taux = (heures_travail / heures_disponibles * 100) if heures_disponibles > 0 else 0
        
        status = "✅" if taux >= 80 else "⚠️"
        print(f"   {status} Taux d'occupation: {taux:.1f}%")
        print(f"   ⏱️  Heures travail: {heures_travail:.1f}h / {heures_disponibles}h")
        print(f"   🎯 Objectif: 80%\n")
        
        return taux
    
    def indicator_11_temps_cycle_nva(self) -> Dict[str, float]:
        """
        11. Temps de Cycle & Non Valeur Ajoutée
        Returns: dict avec temps_cycle_moyen et nva
        """
        print("📊 Indicateur 11: Temps de Cycle & NVA")
        
        query = """
            SELECT 
                AVG(TIMESTAMPDIFF(SECOND, start, end)) as cycle_moyen
            FROM tblfinorder
            WHERE end IS NOT NULL
        """
        result = self.query_db(query)
        
        if result.empty or pd.isna(result['cycle_moyen'].iloc[0]):
            print("   ⚠️  Pas de données de temps de cycle disponibles")
            return {"cycle": 0, "va": 0, "nva": 0}
        
        cycle_moyen = float(result['cycle_moyen'].iloc[0])
        # Hypothèse: 20% du temps est NVA (attente, stockage)
        nva = cycle_moyen * 0.20
        va = cycle_moyen - nva
        
        print(f"   ⏱️  Temps cycle moyen: {cycle_moyen:.0f}s")
        print(f"   ✅ Valeur ajoutée: {va:.0f}s ({va/cycle_moyen*100:.1f}%)")
        print(f"   ❌ Non valeur ajoutée: {nva:.0f}s ({nva/cycle_moyen*100:.1f}%)\n")
        
        return {"cycle": cycle_moyen, "va": va, "nva": nva}
    
    def indicator_12_taux_defaut(self) -> float:
        """
        12. Taux de Défaut (NC)
        Returns: taux_defaut_%
        """
        print("📊 Indicateur 12: Taux de Défaut (Non-Conformités)")
        
        # Utiliser tblmainterror pour compter les erreurs
        query = """
            SELECT 
                (SELECT COUNT(*) FROM tblfinorder) as total,
                (SELECT COUNT(*) FROM tblmainterror) as defauts
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de qualité disponibles")
            return 0.0
        
        total = int(result['total'].iloc[0]) if not pd.isna(result['total'].iloc[0]) else 0
        defauts = int(result['defauts'].iloc[0]) if not pd.isna(result['defauts'].iloc[0]) else 0
        taux = (defauts / total * 100) if total > 0 else 0
        
        status = "✅" if taux < 3 else "⚠️"
        print(f"   {status} Taux de défaut: {taux:.1f}%")
        print(f"   ❌ Pièces défectueuses: {defauts}/{total}")
        print(f"   🎯 Seuil acceptable: < 3%\n")
        
        return taux
    
    def indicator_13_causes_nc(self) -> Dict[str, int]:
        """
        13. Causes des Non-Conformités
        Returns: dict avec répartition des causes
        """
        print("📊 Indicateur 13: Causes des Non-Conformités")
        
        query = """
            SELECT 
                ec.Description as cause,
                COUNT(*) as nombre
            FROM tblmainterror me
            JOIN tblerrorcodes ec ON me.ErrorNo = ec.ErrorId
            GROUP BY ec.Description
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de causes NC disponibles")
            return {}
        
        print("   📊 Répartition des causes:")
        causes = {}
        total = result['nombre'].sum()
        for _, row in result.iterrows():
            cause = row['cause']
            nombre = int(row['nombre'])
            pourcentage = (nombre / total * 100) if total > 0 else 0
            causes[cause] = nombre
            print(f"      • {cause}: {nombre} ({pourcentage:.1f}%)")
        print()
        
        return causes
    
    def indicator_14_taux_conforme(self) -> float:
        """
        14. Taux de Conforme
        Returns: taux_conforme_%
        """
        print("📊 Indicateur 14: Taux de Conformité")
        
        # Inverser le calcul du taux de défaut pour obtenir le taux de conformité
        query = """
            SELECT 
                (SELECT COUNT(*) FROM tblfinorder) as total,
                (SELECT COUNT(*) FROM tblmainterror) as defauts
        """
        result = self.query_db(query)
        
        if result.empty:
            print("   ⚠️  Pas de données de qualité disponibles")
            return 0.0
        
        total = int(result['total'].iloc[0]) if not pd.isna(result['total'].iloc[0]) else 0
        defauts = int(result['defauts'].iloc[0]) if not pd.isna(result['defauts'].iloc[0]) else 0
        conformes = total - defauts
        taux = (conformes / total * 100) if total > 0 else 0
        
        print(f"   ✅ Taux de conformité: {taux:.1f}%")
        print(f"   📊 Pièces conformes: {conformes}/{total}\n")
        
        return taux
    
    def indicator_15_consommation_energie(self) -> float:
        """
        15. Consommation Énergie
        Returns: consommation_kwh
        """
        print("📊 Indicateur 15: Consommation Énergétique")
        
        # Note: À adapter selon le format réel du fichier dataEnergy
        print("   ⚠️  Fichier dataEnergy non implémenté")
        print("   📊 Consommation (simulation): 250.5 kWh\n")
        
        return 250.5
    
    def run_all_indicators(self):
        """Exécute tous les 15 indicateurs"""
        print("=" * 60)
        print("🚀 TEST DES 15 INDICATEURS MES 4.0 - DASHBOARD T'ELEFAN")
        print("=" * 60)
        print()
        
        try:
            self.connect_db()
            self.load_robot_data()
            
            print("\n" + "=" * 60)
            print("🔴 ONGLET 1: TEMPS RÉEL")
            print("=" * 60 + "\n")
            
            self.indicator_1_autonomie_robot()
            self.indicator_2_of_realises()
            self.indicator_3_production_realisee()
            
            print("\n" + "=" * 60)
            print("🟠 ONGLET 2: STOCKAGE")
            print("=" * 60 + "\n")
            
            self.indicator_4_taux_occupation()
            self.indicator_5_mouvements_stocks()
            
            print("\n" + "=" * 60)
            print("🟡 ONGLET 3: ROBOT")
            print("=" * 60 + "\n")
            
            self.indicator_6_historique_autonomie()
            self.indicator_7_distance_parcourue()
            
            print("\n" + "=" * 60)
            print("🔵 ONGLET 4: PRODUCTION / QUALITÉ / ÉNERGIE")
            print("=" * 60 + "\n")
            
            self.indicator_8_production_hebdo()
            self.indicator_9_production_detaillee()
            self.indicator_10_taux_occupation_machine()
            self.indicator_11_temps_cycle_nva()
            self.indicator_12_taux_defaut()
            self.indicator_13_causes_nc()
            self.indicator_14_taux_conforme()
            self.indicator_15_consommation_energie()
            
            print("=" * 60)
            print("✅ TEST TERMINÉ")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE: {e}\n")
        finally:
            if self.conn:
                self.conn.close()
                print("\n🔌 Connexion MariaDB fermée")


if __name__ == "__main__":
    # Configuration de connexion à MariaDB
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'example_user',
        'password': 'example_password',
        'database': 'MES4'
    }
    
    # Chemin vers le fichier CSV robot
    CSV_ROBOT_PATH = 'TELEFAN/robotino_data.csv'
    
    # Exécution des tests
    mes = MESIndicators(DB_CONFIG, CSV_ROBOT_PATH)
    mes.run_all_indicators()
