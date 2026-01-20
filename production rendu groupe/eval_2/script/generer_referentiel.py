import pandas as pd

# 1. Définition des données pour l'onglet "Production (SQL)"
# Ces données proviennent de l'analyse du fichier FestoMES.sql et du contexte.
data_production = [
    {
        "Nom Variable": "OrderNo",
        "Définition": "Numéro unique de l'Ordre de Fabrication (Identifiant)",
        "Métrique (Unité)": "Texte (ID)",
        "Source (Table.Champ)": "tblfinorder.OrderNo",
        "Nettoyage / Règle": "Vérifier l'unicité. Clé Primaire."
    },
    {
        "Nom Variable": "Date_Lancement",
        "Définition": "Date et heure de début de production de l'OF",
        "Métrique (Unité)": "Datetime",
        "Source (Table.Champ)": "tblfinorder.StartTime",
        "Nettoyage / Règle": "Convertir le format SQL en objet datetime Python."
    },
    {
        "Nom Variable": "Date_Fin",
        "Définition": "Date et heure de fin de production de l'OF",
        "Métrique (Unité)": "Datetime",
        "Source (Table.Champ)": "tblfinorder.EndTime",
        "Nettoyage / Règle": "Si NULL, considérer l'état comme 'En cours'."
    },
    {
        "Nom Variable": "Produit_Ref",
        "Définition": "Référence unique du produit fabriqué",
        "Métrique (Unité)": "Entier (ID)",
        "Source (Table.Champ)": "tblboxpos.PartNo",
        "Nettoyage / Règle": "Jointure avec 'tblpart' pour récupérer le Nom et l'Image."
    },
    {
        "Nom Variable": "Statut_Piece",
        "Définition": "État de la pièce (Conforme ou Non Conforme)",
        "Métrique (Unité)": "Booléen / Texte",
        "Source (Table.Champ)": "tblboxpos.Error",
        "Nettoyage / Règle": "Si Error > 0 alors 'Non Conforme'. Sinon 'Conforme'."
    },
    {
        "Nom Variable": "Code_Erreur",
        "Définition": "Code identifiant le type de défaut spécifique",
        "Métrique (Unité)": "Entier",
        "Source (Table.Champ)": "tblboxpos.Error",
        "Nettoyage / Règle": "0 = OK. Faire jointure avec 'tblerrorcodes' pour description."
    },
    {
        "Nom Variable": "Temps_Cycle",
        "Définition": "Durée totale nécessaire pour fabriquer une unité",
        "Métrique (Unité)": "Secondes",
        "Source (Table.Champ)": "Calcul (EndTime - StartTime)",
        "Nettoyage / Règle": "Exclure valeurs négatives ou aberrantes (> seuil)."
    },
    {
        "Nom Variable": "Position_Stock",
        "Définition": "Emplacement physique du produit dans le magasin",
        "Métrique (Unité)": "Entier (1-9)",
        "Source (Table.Champ)": "tblbufferpos.PosNo",
        "Nettoyage / Règle": "Filtrer uniquement les positions valides du buffer."
    }
]

# 2. Définition des données pour l'onglet "Logistique & Energie"
# Ces données proviennent du CSV Robotino et du fichier Energie.
data_logistique = [
    {
        "Nom Variable": "Robot_Batterie",
        "Définition": "Niveau de charge actuel du Robotino",
        "Métrique (Unité)": "Pourcentage (0-100)",
        "Source (Table.Champ)": "robotino_data.csv (festool_charger_capacities_0)",
        "Nettoyage / Règle": "Moyenne par minute. Alerte Rouge si < 20%."
    },
    {
        "Nom Variable": "Robot_Charge",
        "Définition": "Indique si le robot est branché sur secteur",
        "Métrique (Unité)": "Booléen",
        "Source (Table.Champ)": "robotino_data.csv (festool_charger_externalPower_0)",
        "Nettoyage / Règle": "True = En charge, False = Sur batterie."
    },
    {
        "Nom Variable": "Robot_X",
        "Définition": "Coordonnée X de la position du robot",
        "Métrique (Unité)": "Mètres",
        "Source (Table.Champ)": "robotino_data.csv (odometry_x)",
        "Nettoyage / Règle": "Utilisé pour calcul distance euclidienne."
    },
    {
        "Nom Variable": "Robot_Y",
        "Définition": "Coordonnée Y de la position du robot",
        "Métrique (Unité)": "Mètres",
        "Source (Table.Champ)": "robotino_data.csv (odometry_y)",
        "Nettoyage / Règle": "Utilisé pour calcul distance euclidienne."
    },
    {
        "Nom Variable": "Conso_Elec",
        "Définition": "Consommation électrique totale journalière",
        "Métrique (Unité)": "kWh",
        "Source (Table.Champ)": "dataEnergy (Fichier externe)",
        "Nettoyage / Règle": "Arrondir à 1 décimale."
    }
]

# ... (Gardez les listes data_production et data_logistique définies au début)

# 3. Création des DataFrames
df_prod = pd.DataFrame(data_production)
df_log = pd.DataFrame(data_logistique)

# 4. Export en CSV (Solution de secours)
try:
    df_prod.to_csv("Referentiel_Production.csv", index=False, sep=';', encoding='utf-8-sig')
    df_log.to_csv("Referentiel_Logistique.csv", index=False, sep=';', encoding='utf-8-sig')
    
    print("✅ Fichiers CSV générés : 'Referentiel_Production.csv' et 'Referentiel_Logistique.csv'")
    print("👉 Vous pouvez maintenant les ouvrir dans Excel et les enregistrer en .xlsx pour le rendu.")
    
except Exception as e:
    print(f"❌ Erreur : {e}")