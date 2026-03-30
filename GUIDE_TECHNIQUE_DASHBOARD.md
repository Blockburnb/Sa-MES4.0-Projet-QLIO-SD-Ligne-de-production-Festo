# Guide technique dashboard

## 1. Objectif du document
Ce document explique les choix techniques faits pour developper l'application, ainsi que son fonctionnement general.

## 2. Vue d'ensemble de l'architecture
L'application est composee de 3 couches principales:
1. Interface et logique applicative Streamlit.
2. Base SQL metier (MariaDB) pour les indicateurs de production.
3. Base SQL locale (SQLite) pour l'authentification et la gestion des permissions KPI.

Composants principaux du projet:
1. dashboard/dashboard_final.py: application Streamlit principale.
2. TELEFAN/docker-compose.yml: services Docker (MariaDB + phpMyAdmin).
3. TELEFAN/FestoMES-2025-03-27.sql: dump de donnees metier.
4. dashboard/auth_users.sqlite3: base locale pour comptes et permissions.
5. run_dashboard_linux.sh, run_dashboard_macos.sh, run_dashboard_windows.ps1: launchers natifs.

## 3. Choix de framework et structure
### 3.1 Streamlit
Le choix Streamlit a ete retenu pour:
1. accelerer le developpement d'un dashboard multi-pages.
2. integrer rapidement les composants UI et graphiques (Plotly).
3. simplifier le deploiement local (un seul processus applicatif).

### 3.2 Application en fichier principal unique
Le coeur applicatif est centralise dans dashboard/dashboard_final.py.
Avantages:
1. lisibilite immediate pour une equipe etudiante/projet court.
2. modifications rapides pendant les iterations.
Limites:
1. taille du fichier qui augmente avec les fonctionnalites.
2. couplage plus fort entre UI, regles metier et acces donnees.

## 4. Gestion des donnees metier
### 4.1 Source de verite metier
Les KPIs sont calcules depuis MariaDB (tables MES).
Le dashboard lit dynamiquement la base configuree dans la section Connexion SQL.

### 4.2 Import initial
Le launcher demarre la stack Docker puis:
1. detecte la base cible (MES4/mes4),
2. importe le dump SQL si la base est vide,
3. laisse la base intacte si elle est deja peuplee.

Ce choix evite de reimporter a chaque lancement et preserve l'etat existant.

## 5. Securite et comptes
### 5.1 Authentification
Les comptes sont stockes dans SQLite (table users) et non en clair dans le code.
La verification mot de passe utilise PBKDF2-HMAC-SHA256 avec salt par compte.

### 5.2 Choix du hachage
PBKDF2 a ete choisi car:
1. standard Python natif (pas de dependance externe obligatoire),
2. resistant aux attaques par force brute mieux qu'un hash simple,
3. facilement configurable (nombre d'iterations).

### 5.3 Roles
Roles supportes:
1. Admin
2. Operateur
3. Superviseur
4. Chef de production

Le role controle:
1. la navigation (acces page Admin reserve Admin),
2. l'acces effectif aux indicateurs KPI.

## 6. Permissions KPI (RBAC applicatif)
### 6.1 Modele
Chaque KPI possede une liste de roles autorises.
Les permissions sont configurees depuis la page Admin.

### 6.2 Persistance
Les permissions KPI sont persistees en SQLite (table kpi_permissions).
Ce choix garantit que les droits restent stables apres redemarrage.

### 6.3 Enforcement
Le rendu de chaque indicateur est conditionne par une verification de role.
Si non autorise, le bloc KPI est remplace par un message d'acces refuse.

## 7. Gestion des comptes en administration
Depuis la page Admin, il est possible de:
1. creer un compte,
2. modifier role et activation,
3. reinitialiser un mot de passe.

Regles de protection appliquees:
1. validation des roles autorises,
2. prevention de desactivation du compte courant en session,
3. stockage uniquement hache + salt en base.

## 8. Choix des launchers natifs par OS
### 8.1 Pourquoi natif OS
Le projet utilise des scripts de lancement natifs pour:
1. ne pas dependre d'un launcher Python dedie,
2. simplifier l'usage final selon l'OS,
3. gerer les differences (open navigateur, commandes shell, etc.).

Scripts cibles:
1. run_dashboard_linux.sh
2. run_dashboard_macos.sh
3. run_dashboard_windows.ps1

### 8.2 Fonctions integrees des launchers
1. synchro Git active vers main (clone si besoin),
2. verification des ports,
3. verification Docker/Compose,
4. demarrage stack MariaDB/phpMyAdmin,
5. attente disponibilite DB,
6. lancement Streamlit,
7. check HTTP de sante,
8. ouverture automatique du dashboard.

### 8.3 Politique d'echec
Les launchers sont en mode fail-fast avec message guide si:
1. Git manquant,
2. Docker manquant/daemon indisponible,
3. service mariadb indisponible,
4. conflits ports critiques,
5. echec sync Git (reseau, arbre local sale, conflit fast-forward).

## 9. Fonctionnement global (sequence)
1. Lancement via script OS.
2. Synchronisation Git sur main.
3. Preparation Python venv + dependances.
4. Demarrage et verification Docker/MariaDB.
5. Import SQL initial si necessaire.
6. Lancement Streamlit.
7. Authentification utilisateur.
8. Chargement des permissions KPI.
9. Affichage conditionnel des pages et KPIs selon role.

## 10. Limites actuelles et pistes
Limites:
1. dashboard_final.py reste volumineux.
2. pas de tests automatises complets pour toute la couche RBAC.
3. validation PowerShell non executee dans l'environnement Linux de dev.

Pistes d'amelioration:
1. modulariser le code Python (auth, data, ui, permissions).
2. ajouter tests unitaires (auth + permissions + helpers SQL).
3. ajouter migration SQLite versionnee (schema evolutif).
4. ajouter observabilite (logs fonctionnels plus structures).
