# Documentation Technique — Tableau de Bord MES 4.0 (T'EleFan)

> **Projet :** Tableau de bord de pilotage de production — ligne Festo  
> **Contexte :** BTS QLIO — Projet MES 4.0  
> **Application :** [http://localhost:8501](http://localhost:8501)

---

## Table des matières

1. [Vue d'ensemble de l'architecture](#1-vue-densemble-de-larchitecture)
2. [Technologies utilisées](#2-technologies-utilisées)
3. [Structure des fichiers](#3-structure-des-fichiers)
4. [Authentification et gestion des sessions](#4-authentification-et-gestion-des-sessions)
5. [Contrôle d'accès basé sur les rôles (RBAC)](#5-contrôle-daccès-basé-sur-les-rôles-rbac)
6. [Pages et fonctionnalités](#6-pages-et-fonctionnalités)
   - [6.1 Page de connexion](#61-page-de-connexion)
   - [6.2 Temps Réel (Opérateur)](#62-temps-réel-opérateur)
   - [6.3 Stockage](#63-stockage)
   - [6.4 Robot](#64-robot)
   - [6.5 Qualité](#65-qualité)
   - [6.6 Administration](#66-administration)
7. [Barre latérale et filtres globaux](#7-barre-latérale-et-filtres-globaux)
8. [Thème et personnalisation de l'interface](#8-thème-et-personnalisation-de-linterface)
9. [Architecture des bases de données](#9-architecture-des-bases-de-données)
10. [Stratégie de cache et performance](#10-stratégie-de-cache-et-performance)
11. [Sécurité](#11-sécurité)
12. [Déploiement et lancement](#12-déploiement-et-lancement)

---

## 1. Vue d'ensemble de l'architecture

Le tableau de bord est une application web **monopage multi-sections** développée entièrement en Python avec le framework **Streamlit**. Elle se connecte à deux sources de données :

- Une base **MariaDB** (conteneurisée via Docker) stockant les données de production réelles issues de la ligne Festo.
- Une base **SQLite** locale gérant l'authentification des utilisateurs et les permissions des indicateurs.

```
Navigateur (localhost:8501)
       │
       ▼
  Streamlit (app.py)
  ┌────────────────────────────────────────────┐
  │  Authentification  │  Navigation (pages)   │
  │  Session state     │  Filtres globaux       │
  │  RBAC / permissions│  Visualisations Plotly │
  └────────────────────────────────────────────┘
       │                          │
       ▼                          ▼
  SQLite (auth_users.sqlite3)   MariaDB (MES4 — Docker)
  - users                        - tblfinorder
  - kpi_permissions              - tblfinorderpos
  - app_config                   - tblmachinereport
                                 - tblbufferpos
                                 - tblfinstep
```

---

## 2. Technologies utilisées

| Couche | Technologie | Rôle |
|---|---|---|
| **Interface** | Streamlit | Framework web Python — rendu UI, navigation, état de session |
| **Visualisation** | Plotly | Graphiques interactifs (jauges, courbes, barres, histogrammes) |
| **Style** | HTML / CSS inline | Thèmes clair/sombre, cartes KPI personnalisées |
| **Backend** | Python 3 | Logique métier, requêtes SQL, gestion des permissions |
| **BDD Métriques** | MariaDB (Docker) | Données de production en temps réel |
| **BDD Auth** | SQLite | Comptes utilisateurs, permissions KPI, configuration |
| **Manipulation données** | Pandas | Agrégation, formatage et traitement des données SQL |
| **Containerisation** | Docker / Docker Compose | Isolation et portabilité de MariaDB + phpMyAdmin |
| **Lancement** | Bash / PowerShell | Scripts automatisés multi-plateforme |

---

## 3. Structure des fichiers

```
projet/
├── dashboard/
│   └── windows/
│       └── app.py                  # Application Streamlit principale (≈1 600 lignes)
├── TELEFAN/
│   ├── docker-compose.yml          # Définition des services Docker (MariaDB, phpMyAdmin)
│   ├── FestoMES-2025-03-27.sql     # Dump de la base de production (version initiale)
│   ├── FestoMES-2026-03-31.sql     # Dump de la base de production (version mise à jour)
│   └── data/                       # Volume persistant MariaDB
├── run_dashboard_linux.sh           # Script de lancement Linux
├── run_dashboard_macos.sh           # Script de lancement macOS
├── run_dashboard_windows.ps1        # Script de lancement Windows (PowerShell)
├── GUIDE_INSTALLATION_DASHBOARD.md # Guide d'installation utilisateur
└── GUIDE_TECHNIQUE_DASHBOARD.md    # Guide technique d'architecture
```

Le fichier `dashboard/windows/app.py` contient l'intégralité de la logique applicative :
- Gestion de la session et de l'authentification
- Définition de toutes les pages et KPIs
- Requêtes SQL paramétrées
- Rendu des graphiques Plotly
- Panneau d'administration

---

## 4. Authentification et gestion des sessions

### 4.1 Formulaire de connexion

La page d'accueil présente un formulaire avec deux champs : **nom d'utilisateur** et **mot de passe**. À la soumission :

1. Le nom d'utilisateur est recherché dans la table `users` de la base SQLite.
2. Le mot de passe saisi est haché avec **PBKDF2-HMAC-SHA256** (200 000 itérations) en utilisant le sel stocké propre à chaque utilisateur.
3. Le haché obtenu est comparé au haché stocké en base.
4. Si la vérification réussit et que le compte est actif, les informations de session sont chargées dans `st.session_state`.

### 4.2 État de session

Les variables clés maintenues en session Streamlit :

| Variable | Contenu |
|---|---|
| `logged_in` | Booléen — utilisateur authentifié |
| `username` | Identifiant de l'utilisateur connecté |
| `role` | Rôle associé (`admin`, `operateur`, `superviseur`, `chef_production`) |
| `kpi_permissions` | Dictionnaire des KPIs autorisés pour le rôle |
| `theme` | Thème d'affichage courant (`dark` ou `light`) |
| `current_page` | Page active affichée |

### 4.3 Déconnexion

Un bouton **Déconnexion** dans la barre latérale réinitialise l'état de session et redirige vers la page de connexion.

---

## 5. Contrôle d'accès basé sur les rôles (RBAC)

L'application implémente un système RBAC à deux niveaux :

### 5.1 Accès aux pages

| Page | Admin | Opérateur | Superviseur | Chef de production |
|---|:---:|:---:|:---:|:---:|
| Temps Réel | ✅ | ✅ | ✅ | ✅ |
| Stockage | ✅ | ✅ | ✅ | ✅ |
| Robot | ✅ | ✅ | ✅ | ✅ |
| Qualité | ✅ | ✅ | ✅ | ✅ |
| Administration | ✅ | ❌ | ❌ | ❌ |

### 5.2 Accès aux KPIs

Chacun des 15 indicateurs peut être activé ou désactivé individuellement pour chaque rôle. La configuration est persistée dans la table SQLite `kpi_permissions` et chargée à la connexion. Un KPI non autorisé n'est simplement pas rendu dans l'interface.

---

## 6. Pages et fonctionnalités

### 6.1 Page de connexion

**Accès :** Public (non authentifié)

La page de connexion affiche :
- Un logo ou titre de l'application
- Un formulaire `username` / `password`
- Un message d'erreur en cas d'identifiants invalides ou de compte inactif

Aucune donnée de production n'est accessible avant authentification.

---

### 6.2 Temps Réel (Opérateur)

**Accès :** Tous les rôles authentifiés

Cette page présente les **3 indicateurs de production en temps réel**, sous forme de barres de progression HTML :

#### KPI 1 — Autonomie Robot
- **Calcul :** Ratio entre le nombre d'enregistrements machine sans erreur et le total des enregistrements sur la période filtrée.  
  `Autonomie (%) = 100 × (1 − erreurs / total)`
- **Source SQL :** `tblmachinereport` (colonnes `ErrorL0`, `ErrorL1`, `ErrorL2`)
- **Affichage :** Barre de progression colorée (vert / orange / rouge) avec libellé "Restant / Utilisé"

#### KPI 2 — Ordres de Fabrication (OF) Réalisés
- **Calcul :** Nombre d'ordres clôturés (champ `End` renseigné) sur la période, comparé au nombre total d'ordres planifiés.
- **Source SQL :** `tblfinorder`
- **Affichage :** Barre de progression avec valeurs absolues (ex. : "12 / 15 OF réalisés")

#### KPI 3 — Production Réalisée
- **Calcul :** Nombre de positions d'ordres finalisées sur la période, comparé à un objectif configurable.
- **Source SQL :** `tblfinorderpos`
- **Affichage :** Barre de progression avec compteur d'unités produites vs. objectif

---

### 6.3 Stockage

**Accès :** Tous les rôles authentifiés

#### KPI 4 — Taux d'Occupation du Stockage
- **Calcul :** Proportion d'emplacements de buffer occupés (`Booked = 1`) par rapport à la capacité totale.  
  `Taux (%) = 100 × positions_occupées / total_positions`
- **Source SQL :** `tblbufferpos`
- **Affichage :** Jauge Plotly circulaire (0–100 %)  
  - Vert < 70 % | Orange 70–85 % | Rouge > 85 %

#### KPI 5 — Mouvements de Stocks
- **Calcul :** Nombre d'entrées et de sorties de stockage agrégées par jour sur la plage de dates sélectionnée.
- **Source SQL :** `tblbufferpos`
- **Affichage :** Graphique en courbes Plotly — deux séries (Entrées / Sorties) sur 7 jours glissants

---

### 6.4 Robot

**Accès :** Tous les rôles authentifiés

#### KPI 6 — Historique d'Autonomie
- **Calcul :** Pour chaque journée de la période, calcul du pourcentage d'autonomie (absence d'erreurs) et du nombre d'heures d'utilisation.
- **Source SQL :** `tblmachinereport`
- **Affichage :** Graphique combiné barres + courbe (heures d'utilisation / % autonomie)

#### KPI 7 — Distance Parcourue
- **Calcul :** Distance cumulée journalière du robot AGV (Robotino) sur la période.
- **Source :** Données issues des rapports machine ou fichier `robotino_data.csv`
- **Affichage :** Courbe Plotly avec cumul progressif

---

### 6.5 Qualité

**Accès :** Tous les rôles authentifiés

Cette page concentre **8 indicateurs** couvrant la performance qualité de la ligne de production.

#### KPI 8 — Production Hebdomadaire
- Deux métriques côte-à-côte : **production réelle** vs. **objectif** (720 unités/semaine).
- **Source SQL :** `tblfinorderpos`

#### KPI 9 — Production Détaillée (tableau)
- Tableau jour par jour (Lundi–Vendredi) : production réelle, objectif, écart et % d'atteinte.
- **Source SQL :** `tblfinorderpos` agrégé par date

#### KPI 10 — Taux d'Occupation Machine
- **Calcul :** Ratio temps productif / temps total disponible par journée.
- **Source SQL :** `tblmachinereport`
- **Affichage :** Barres verticales avec ligne de seuil cible

#### KPI 11 — Temps de Cycle & Temps Non à Valeur Ajoutée (NVA)
- **Calcul :** Pour chaque étape, décomposition du temps en VA (Valeur Ajoutée) et NVA (attentes, manutentions, pannes).
- **Source SQL :** `tblfinstep`
- **Affichage :** Barres empilées Plotly (Vert = VA, Orange = NVA)

#### KPI 12 — Taux de Défauts
- **Calcul :** `Taux (%) = 100 × unités_défectueuses / total_unités`
- **Source SQL :** `tblfinorderpos` (colonne `Error`)
- **Affichage :** Courbe temporelle avec zones colorées (Vert < 2,25 % / Rouge ≥ 2,25 %)

#### KPI 13 — Causes de Non-Conformité (Pareto)
- **Calcul :** Décompte et pourcentage cumulé de chaque catégorie de défaut.
- **Source SQL :** `tblfinorderpos`
- **Affichage :** Graphique de Pareto (barres + courbe cumulative)

#### KPI 14 — Taux de Conformité
- **Calcul :** `Conformité (%) = 100 − Taux_défauts`
- **Affichage :** Carte KPI HTML avec valeur en grand format et code couleur

#### KPI 15 — Consommation Énergétique
- **Calcul :** Moyenne de la consommation électrique réelle sur la période.
- **Source SQL :** `tblfinstep` (colonne `ElectricEnergyReal`)
- **Affichage :** Carte KPI HTML avec valeur en kWh

---

### 6.6 Administration

**Accès :** Rôle `admin` uniquement

Le panneau d'administration comporte deux sections :

#### A. Gestion des permissions KPI

Un tableau matriciel liste les 15 KPIs en lignes et les 4 rôles en colonnes. Chaque cellule est un widget `multiselect` permettant d'activer ou de désactiver l'accès. Les modifications sont immédiatement persistées dans la table SQLite `kpi_permissions`.

Des boutons de navigation rapide permettent d'accéder directement à chaque page pour vérifier le résultat des changements de permissions.

#### B. Gestion des comptes utilisateurs

Trois onglets sont disponibles :

| Onglet | Fonctionnalité |
|---|---|
| **Voir les comptes** | Tableau récapitulatif (username, rôle, statut actif, date de création) |
| **Créer un compte** | Formulaire avec validation (min. 3 caractères username, min. 4 caractères mot de passe) |
| **Modifier un compte** | Changement de rôle, activation/désactivation, réinitialisation du mot de passe |

**Garde-fous :**
- L'administrateur ne peut pas désactiver son propre compte actif.
- Les modifications sont refusées si les contraintes de validation ne sont pas respectées.

---

## 7. Barre latérale et filtres globaux

La barre latérale, accessible depuis toutes les pages authentifiées, contient :

### 7.1 Sélecteur de période
- Deux champs `date_input` (date de début / date de fin)
- Valeur par défaut : **7 jours glissants** (aujourd'hui − 7 jours → aujourd'hui)
- Toutes les requêtes SQL intègrent ce filtre via des paramètres de liaison `%s`

### 7.2 Sélecteur de site
- Liste déroulante : `Tous`, `Site A - Festo`, `Site B`
- Filtre additionnel appliqué aux requêtes pour les déploiements multi-sites

### 7.3 Panneau de connexion SQL (Admin uniquement)
- Champs configurables : `host`, `port`, `user`, `password`, `database`
- Permet de changer dynamiquement de source de données sans redémarrer l'application
- Le statut de connexion (✅ Connecté / ❌ Erreur) est affiché en temps réel

### 7.4 Informations utilisateur
- Affichage du nom d'utilisateur et du rôle courant
- Bouton de déconnexion

---

## 8. Thème et personnalisation de l'interface

### 8.1 Bascule clair/sombre

Un bouton dans la barre latérale alterne entre les thèmes **Clair** et **Sombre**. Le choix est maintenu en session (`st.session_state.theme`).

### 8.2 CSS injecté dynamiquement

À chaque rendu, un bloc CSS est injecté via `st.markdown(..., unsafe_allow_html=True)` pour surcharger les styles Streamlit par défaut :

- Couleurs de fond (`#0e1117` sombre / `#ffffff` clair)
- Couleurs des textes, bordures, boutons
- Cartes KPI HTML avec coins arrondis et ombres portées
- Styles des barres de progression personnalisées

### 8.3 Mise en page

- Layout **wide** activé (`st.set_page_config(layout="wide")`)
- Grille en **8 colonnes** pour les KPIs côte-à-côte
- Graphiques Plotly redimensionnables automatiquement

---

## 9. Architecture des bases de données

### 9.1 MariaDB — Base de production (`MES4`)

| Table | Description | Colonnes clés |
|---|---|---|
| `tblfinorder` | Ordres de fabrication | `Id`, `Start`, `End`, `PlannedStart` |
| `tblfinorderpos` | Positions d'ordre (unités) | `Id`, `OrderId`, `Start`, `End`, `Error` |
| `tblmachinereport` | Rapports machine / robot | `Id`, `TimeStamp`, `ErrorL0`, `ErrorL1`, `ErrorL2` |
| `tblbufferpos` | Emplacements de stockage | `PNo`, `Booked` |
| `tblfinstep` | Étapes de fabrication | `Id`, `OrderPosId`, `ElectricEnergyReal` |

Connexion par défaut : `exemple_user / exemple_password` sur `localhost:3306`.

### 9.2 SQLite — Base d'authentification (`auth_users.sqlite3`)

| Table | Description |
|---|---|
| `users` | Identifiants, hachés de mots de passe, sels, rôles, statut actif, dates |
| `kpi_permissions` | Matrice rôle × KPI (permission booléenne) |
| `app_config` | Paramètres globaux de l'application |

Le fichier SQLite est créé automatiquement au premier lancement. Un compte administrateur par défaut est inséré si la table `users` est vide.

---

## 10. Stratégie de cache et performance

Les fonctions de requête SQL utilisent le décorateur `@st.cache_data` de Streamlit pour éviter les appels répétés à la base de données :

| Durée de cache | Utilisation |
|---|---|
| **60 secondes** | Requêtes des KPIs opérationnels (production, stockage, robot) |
| **300 secondes** | Requêtes de plage de dates disponibles (données statiques de la période) |

Ce mécanisme réduit la charge sur MariaDB et améliore la réactivité de l'interface lors de la navigation entre les pages.

---

## 11. Sécurité

| Mécanisme | Implémentation |
|---|---|
| **Hachage des mots de passe** | PBKDF2-HMAC-SHA256 — 200 000 itérations — sel aléatoire par utilisateur |
| **Prévention de l'injection SQL** | Requêtes paramétrées avec placeholders `%s` (jamais de concaténation de chaînes) |
| **Contrôle d'accès** | Vérification du rôle et des permissions KPI à chaque rendu de page |
| **Isolation des données** | SQLite (auth) et MariaDB (métriques) sont des bases séparées |
| **Gestion de session** | État Streamlit en mémoire — aucune persistance côté client (pas de cookies exposés) |
| **Paramètres SQL** | La configuration de connexion SQL est accessible uniquement au rôle `admin` |

---

## 12. Déploiement et lancement

### 12.1 Prérequis

- Python 3.10+
- Docker Desktop (ou Docker Engine + Docker Compose)
- Git (optionnel, pour la synchronisation automatique)

### 12.2 Scripts de lancement automatisés

Les scripts de lancement réalisent automatiquement les étapes suivantes :

1. **Synchronisation Git** — `git pull origin main` (si Git est disponible)
2. **Vérification des ports** — 8501 (Streamlit), 3306 (MariaDB), 8080 (phpMyAdmin)
3. **Démarrage Docker** — `docker compose up -d` dans le dossier `TELEFAN/`
4. **Import SQL** — Import du dump SQL si la base `MES4` est vide
5. **Environnement virtuel Python** — Création et activation du venv, installation des dépendances
6. **Démarrage Streamlit** — `streamlit run dashboard/windows/app.py`
7. **Ouverture navigateur** — Lancement automatique de `http://localhost:8501`

| Système | Commande |
|---|---|
| Linux | `./run_dashboard_linux.sh` |
| macOS | `./run_dashboard_macos.sh` |
| Windows | `.\run_dashboard_windows.ps1` |

### 12.3 Services Docker

```yaml
# docker-compose.yml
services:
  mariadb:        # Port 3306 — base de production MES4
  phpmyadmin:     # Port 8080 — interface d'administration SQL
```

### 12.4 Accès phpMyAdmin

L'interface phpMyAdmin est disponible sur [http://localhost:8080](http://localhost:8080) pour inspecter ou modifier manuellement les données de la base MariaDB.
