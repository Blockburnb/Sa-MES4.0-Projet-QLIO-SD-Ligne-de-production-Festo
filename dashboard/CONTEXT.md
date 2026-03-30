# 🧠 CONTEXTE DU PROJET : DASHBOARD T'ELEFAN (MES 4.0)

Ce document est la **RÉFÉRENCE UNIQUE** pour l'assistant IA. Il compile les règles métier, le schéma technique et les 15 indicateurs obligatoires du client QLIO.

## 1. CONTEXTE NARRATIF & RÔLES

* **Entreprise :** T'EleFan (Fabricant de smartphones durables).
* **Projet :** Pilotage de la ligne d'assemblage semi-automatisée **Festo**.
* **Acteurs :**
* **Client (QLIO) :** Département Qualité/Logistique (Besoin métier, non technique).
* **Prestataire (SD - Groupe 6) :** Département Science des Données (Expertise technique Python).


* **Objectif :** Collecter les données (SQL + IoT), les nettoyer et les présenter dans un tableau de bord décisionnel ergonomique.

## 2. CRITÈRES DE RÉUSSITE (GRILLE D'ÉVALUATION)

L'IA doit prioriser ces aspects dans le code généré :

1. **Design & Ergonomie (Coef 20) :** Interface "Sexy", Dark Mode, Accessibilité (Daltonisme).
2. **Qualité du Code (Coef 15) :** Structure modulaire, PEP8, Docstrings.
3. **Analytique (Coef 10) :** Pertinence des 15 KPIs et mise en valeur des données.
4. **Fonctionnel (Coef 10) :** Robustesse (Try/Except), Gestion des erreurs de connexion.

## 3. RÈGLES VISUELLES & UX (Selon Recherche Bibliographique)

* **Thème :** Mode Sombre (Dark Mode) obligatoire + Palette accessible (Viridis/CVD).
* **Intégrité Graphique :**
* Axes Y démarrent toujours à 0.
* Pas de 3D pour la 2D.
* Contextualisation systématique (Valeur vs Objectif).


* **Structure de l'App :**
* **Sidebar :** Navigation + Filtres Globaux (Site, Période).
* **4 Onglets :** Temps Réel, Stockage, Robot, Production/Qualité/Énergie.



## 4. ARCHITECTURE TECHNIQUE

* **Langage :** 100% Python.
* **Framework :** Streamlit (recommandé) ou Dash.
* **Backend :** `pandas` pour tout le traitement de données.
* **Sources :**
* **MariaDB (SQL) :** Tables `tblfinorder`, `tblboxpos`, `tblbufferpos`, etc.
* **CSV :** `robotino_data.csv` (Robot), `dataEnergy` (Conso).



## 5. MODÈLE DE DONNÉES (TABLES CLÉS)

*Noms exacts à utiliser dans les requêtes SQL* :

* **`tblfinorder`** : Ordres terminés (Temps de cycle `start`/`end`, Opérations).
* **`tblboxpos`** : Suivi des produits (Quantités, Conformité, Défauts).
* **`tblbufferpos`** : Stockage (Positions occupées/vides, Entrées/Sorties).
* **`tblerrorcodes`** : Libellés des erreurs.
* **`tblcarrier`** : Suivi des palettes (pour temps des non-conformités).

## 6. DÉTAIL DES 15 INDICATEURS (PAR ONGLET)

### 🔴 ONGLET 1 : TEMPS RÉEL (Suivi Immédiat)

*Mise à jour continue.*

**1. Autonomie du Robot (Journalier)**

* **Donnée :** `device_potAccuChargeState_centiPercent` (CSV Robot).
* **Formule :** Vert = Batterie restante ; Rouge = (100 - Restante).
* **Visuel :** 2 Pourcentages (Arrondi unité).

**2. Nombre d'OF Réalisés (Journalier)**

* **Donnée :** `tblfinorder`.
* **Formule :** Total (Table) vs Réalisés (Statut Terminé).
* **Visuel :** 2 Chiffres (Vert=Fait, Rouge=Reste à faire). *Note: En cours = Reste à faire.*

**3. Production Réalisée (Journalière)**

* **Donnée :** `tblboxpos`.
* **Formule :** Total Prévu vs Total Fini.
* **Visuel :** 2 Chiffres (Vert=Réalisé, Rouge=Reste).

### 🟠 ONGLET 2 : STOCKAGE

*Mise à jour quotidienne.*

**4. Taux d'Occupation Stockage**

* **Donnée :** `tblbufferpos` (Total lignes) vs `tblboxpos` (Occupées).
* **Formule :** `(Nb Occupées / Nb Total) * 100`.
* **Visuel :** Jauge avec zones (Vert <70%, Orange 70-85%, Rouge >85%).

**5. Mouvements de Stocks**

* **Donnée :** `tblbufferpos`.
* **Formule :** `Somme(Entrées) + Somme(Sorties)`.
* **Visuel :** Courbe d'évolution journalière.

### 🟡 ONGLET 3 : ROBOT

*Performance et Maintenance.*

**6. Historique Autonomie Robot**

* **Donnée :** `device_potAccuChargeState_centiPercent` & `power_output_current`.
* **Visuel :** Graphique Combiné (Histo: Temps fonctionnement, Ligne: % Batterie).

**7. Distance Parcourue**

* **Donnée :** `odometry_x`, `odometry_y` (CSV).
* **Formule :** Somme des distances euclidiennes entre points successifs.
* **Visuel :** Chiffre en Mètres (Arrondi unité).

### 🔵 ONGLET 4 : PROD / QUALITÉ / ÉNERGIE

*Analyse Historique avec Filtres.*

**8. Production Hebdomadaire**

* **Donnée :** `tblboxpos`.
* **Calcul :** Somme Réelle (Lun-Ven) vs Objectif (ex: 720).
* **Visuel :** Comparaison (Arrondi unité).

**9. Production Détaillée (Semaine)**

* **Donnée :** `tblboxpos`.
* **Visuel :** Barres (Prod/Jour) vs Ligne (Objectif/Jour).

**10. Taux d'Occupation Machine**

* **Donnée :** `tblfinorder`.
* **Formule :** `(Temps Fonctionnement / Temps Total Disponible) * 100`.
* **Objectif :** 80%.
* **Visuel :** % (Arrondi 1 décimale).

**11. Temps de Cycle & NVA**

* **Donnée :** `tblfinorder` (Total), `tblbufferpos` (NVA/Attente).
* **Calcul :** Cycle Moyen = Total/Qté ; VA = Cycle - NVA.
* **Visuel :** Histo empilé (VA + NVA).

**12. Taux de Défaut (NC)**

* **Donnée :** `tblboxpos` (Total vs NC).
* **Formule :** `(Nb Défectueux / Total) * 100`.
* **Seuil :** Acceptable < 3%.
* **Visuel :** % (Arrondi 1 décimale).

**13. Causes des Non-Conformités**

* **Donnée :** `tblerrorcodes` + `tblcarrier`.
* **Catégories :** "Mauvaise couleur", "Problème hauteur", "Autre".
* **Visuel :** Répartition % (Pie/Bar).

**14. Taux de Conforme**

* **Donnée :** `tblboxpos`.
* **Formule :** `(Nb Conformes / Total) * 100`.
* **Visuel :** % (Arrondi 1 décimale).

**15. Consommation Énergie**

* **Donnée :** Fichier `dataEnergy` (kWh).
* **Indicateur :** Conso à J-1.
* **Visuel :** Chiffre (Arrondi 1 décimale).

## 7. SÉCURITÉ & ACCÈS

* **Fichier Utilisateurs :** `users.csv` (`id`, `username`, `password_hash`, `role`).
* **Rôles :**
* **Admin :** Accès total (Config, Utilisateurs).
* **Manager (QLIO) :** Vue Dashboard complète.
* **Visiteur/Opérateur :** Vue restreinte (Onglet Temps Réel).


* **Authentification :** Page de Login obligatoire au démarrage.