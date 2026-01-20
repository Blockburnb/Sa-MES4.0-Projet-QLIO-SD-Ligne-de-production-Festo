# 🧠 CONTEXTE DU PROJET : DASHBOARD QLIO / FESTO MES 4.0

Ce document sert de référence technique et fonctionnelle pour l'assistant IA. Il décrit l'architecture du projet "Ligne de Production Festo".

## 1. OBJECTIF ET PÉRIMÈTRE

Développement d'une **Web App de pilotage (Dashboard)** pour une ligne d'assemblage didactique (Festo).

* **Clients :** Étudiants QLIO (Qualité Logistique).
* **Développeurs :** Groupe 6 (SD).
* **Cible :** Visualisation des ordres de fabrication (OF), suivi qualité, et données logistiques (Robotino).

## 2. ARCHITECTURE TECHNIQUE

### A. Stack Applicative

* **Langage :** Python 3.x (Strictement).
* **Framework Web :** Streamlit ou Flask/Dash.
* **Back-end Data :** `pandas` pour la manipulation des DataFrames.
* **Connexion Base de Données :** `mysql-connector-python` ou `sqlalchemy`.

### B. Infrastructure (Docker)

L'application tourne ou interagit avec un conteneur Docker défini dans `docker-compose.yml` :

* **Service DB :** `mariadb`
* **Port :** 3306
* **Database :** `MES4`
* **User :** `example_user` / **Password :** `example_password`
* **Root Password :** `example_root_password`


* **Service Admin :** `phpmyadmin` (Port 8080)

## 3. MODÈLE DE DONNÉES (SOURCES)

L'application doit croiser deux sources de données distinctes.

### SOURCE 1 : Base de Données SQL (MES4)

Données de production issues du dump `FestoMES-2025-03-27.sql`.
*L'IA doit utiliser ces noms de tables exacts pour générer les requêtes SQL :*

* **`tblOrder`** (Ordres de Fabrication - OF)
* `OrderNo` (PK) : Numéro de commande/OF.
* `OrderDate` : Date de création.
* `CustomerName` : Nom du client.


* **`tblOrderPos`** (Détails des commandes)
* `OrderNo` (FK), `PartNo` (FK).
* `Amount` : Quantité demandée.
* `Produced` : Quantité produite.


* **`tblPart`** (Articles / Produits)
* `PartNo` : Référence pièce.
* `Description` : Nom de la pièce.


* **`tblErrorLog`** (Qualité / Défauts)
* `ErrorTime` : Timestamp de l'erreur.
* `ErrorNo` : Code erreur.
* `PartNo` : Pièce concernée.


* **`tblWorkPlace`** (Postes de travail)
* Identifie les stations (Magasin, Perçage, Assemblage...).



### SOURCE 2 : Logs Robot (CSV)

Données logistiques issues du fichier `robotino_data.csv`.
*Structure du fichier (délimiteur `,`) :*

* **`timestamp`** : Date/Heure (clé de jointure temporelle).
* **`festool_charger_capacities_X`** : Niveau de batterie (0-100) pour différents slots.
* **`festool_charger_externalPower_X`** : Booléen (Branché/Non branché).
* **`festool_charger_batteryLow_X`** : Alerte batterie faible.

## 4. INDICATEURS CLÉS (KPIs) À CODIFIER

Les calculs doivent être réalisés en Python (`pandas`) après extraction des données brutes.

1. **Taux d'Avancement (Progress) :**
* Formule : `SUM(tblOrderPos.Produced) / SUM(tblOrderPos.Amount)`


2. **Taux de Qualité (Quality Rate) :**
* Formule : `(Production Totale - COUNT(tblErrorLog)) / Production Totale`


3. **Disponibilité Robotino :**
* Analyse de la colonne `festool_charger_batteryLow` et `capacities` dans le CSV.
* Seuil critique : < 20% de batterie.


4. **Répartition par Type de Produit :**
* Agrégation des volumes produits par `tblPart.Description`.



## 5. FONCTIONNALITÉS ATTENDUES (INTERFACE)

Selon les maquettes "CROQUIS logiciel" et le PDF "SAé_Telephan" :

1. **Sidebar (Filtres) :**
* Sélecteur de **Période** (Date Début / Date Fin).
* Ce filtre doit s'appliquer à la requête SQL (`WHERE OrderDate BETWEEN ...`) et au filtrage du CSV Robotino.


2. **Page Dashboard Production :**
* Graphique en barre : Quantité produite par jour.
* Camembert : Répartition des types d'erreurs (`tblErrorLog`).


3. **Page Robotino/Maintenance :**
* Graphique linéaire : Évolution de la batterie du Robotino dans le temps.
* Alertes : Liste des moments où le robot était en "Battery Low".


4. **Export :**
* Bouton pour télécharger les données consolidées en CSV.



## 6. INSTRUCTIONS SPÉCIFIQUES POUR LE CODE

* **Connexion DB :** Utiliser un bloc `try/except` pour la connexion MariaDB. Si la connexion échoue (local vs docker), prévoir un fallback ou un message d'erreur clair.
* **Nettoyage :** Le CSV Robotino contient beaucoup de colonnes vides ou à 0 (`festool_charger_accuConnected_X`). Filtrer les colonnes inutiles dès le chargement dans le DataFrame.
* **Jointures :** Il n'y a pas de clé directe entre le Robotino et le MES. La corrélation se fait uniquement par le **Timestamp**.