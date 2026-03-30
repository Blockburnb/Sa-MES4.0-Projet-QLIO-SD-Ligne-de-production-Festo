# Guide installation et lancement du dashboard

## 1. Objectif
Ce guide explique la manipulation la plus simple pour:
1. installer et lancer le dashboard,
2. changer la base SQL utilisee pour les donnees de production,
3. verifier que la base des comptes stocke bien des mots de passe haches.

## 2. Prerequis minimaux
1. Git installe.
2. Docker installe et demarre (Docker Desktop sur Windows/macOS).
3. Python 3 installe.
4. Connexion Internet (le launcher synchronise le depot sur main).

## 3. Recuperer le projet
Si ce n'est pas deja fait:

```bash
git clone https://github.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo.git
cd Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo
```

## 4. Lancer le dashboard (manip la plus simple)
Utiliser le launcher natif de votre OS.

### Windows (PowerShell)
Depuis le dossier du projet:

```powershell
.\run_dashboard_windows.ps1
```

### Linux
Depuis le dossier du projet:

```bash
./run_dashboard_linux.sh
```

### macOS
Depuis le dossier du projet:

```bash
./run_dashboard_macos.sh
```

Le launcher fait automatiquement:
1. synchro Git vers la branche main,
2. verification des ports,
3. verification Docker + demarrage de MariaDB/phpMyAdmin,
4. import SQL initial si necessaire,
5. lancement Streamlit,
6. ouverture automatique du dashboard.

## 5. Changer la base SQL des donnees dans l'application
Important: seul un compte Admin peut modifier la connexion SQL.

### 5.1 Ou doit etre le fichier SQL
Pour l'import automatique par les launchers, le dump SQL doit etre place ici:

- TELEFAN/FestoMES-2025-03-27.sql

Si vous utilisez un autre dump, vous avez 2 options:
1. le renommer en FestoMES-2025-03-27.sql et remplacer le fichier dans TELEFAN,
2. ou l'importer manuellement dans MariaDB (voir 5.2), puis configurer la connexion dans le dashboard.

### 5.2 Comment mettre la base pour que le dashboard y accede
Le dashboard n'accede pas directement a un fichier .sql: il se connecte a une base MariaDB deja importee.

Option A (la plus simple):
1. placer le dump dans TELEFAN/FestoMES-2025-03-27.sql,
2. lancer le dashboard avec le launcher de votre OS,
3. le launcher demarre Docker et importe automatiquement le dump si la base est vide.

Option B (manuelle):
1. demarrer Docker (MariaDB/phpMyAdmin),
2. importer votre dump SQL dans MariaDB (via phpMyAdmin ou commande SQL),
3. noter les informations de connexion (host/port/user/password/nom de base),
4. les renseigner dans Connexion SQL dans le dashboard.

### 5.3 Reglage dans l'application

1. Connectez-vous avec un compte Admin (exemple: admin / admin).
2. Dans le panneau gauche, ouvrez la section Connexion SQL.
3. Modifiez:
   - Hote
   - Port
   - Utilisateur
   - Mot de passe
   - Base
4. Cliquez sur Appliquer configuration SQL.
5. Verifiez dans le panneau gauche:
   - Statut SQL = Connecte
   - Periode des donnees = valeurs attendues

Si Statut SQL reste Hors ligne, verifier les identifiants, le nom de base, et l'accessibilite du serveur SQL.

### 5.4 Ou trouver les informations de connexion SQL si elles ont change
Si les valeurs ne sont plus celles par defaut, vous pouvez les retrouver ici:

1. Dans le fichier compose du projet:
   - [TELEFAN/docker-compose.yml](TELEFAN/docker-compose.yml)
   - Variables utiles en general: MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_ROOT_PASSWORD.

2. Dans le dashboard (meme sans role Admin):
   - section Connexion SQL du panneau gauche,
   - les champs Hote, Port, Utilisateur et Base sont affiches (en lecture seule pour les non-admin).

3. Dans le launcher utilise:
   - [run_dashboard_linux.sh](run_dashboard_linux.sh)
   - [run_dashboard_macos.sh](run_dashboard_macos.sh)
   - [run_dashboard_windows.ps1](run_dashboard_windows.ps1)
   - Rechercher les variables DB_HOST_DEFAULT, DB_PORT_DEFAULT, DB_USER_DEFAULT, DB_PASSWORD_DEFAULT, DB_NAME_DEFAULT.

4. Si vous avez branche une base externe (hors Docker du projet):
   - demander les informations au responsable de la base (host, port, user, password, database),
   - puis les renseigner dans Connexion SQL depuis un compte Admin.

## 6. Verifier que les mots de passe comptes sont haches
La base des comptes est un fichier SQLite:

- dashboard/auth_users.sqlite3

### Methode simple (Linux/macOS avec sqlite3)
Depuis la racine du projet:

```bash
sqlite3 dashboard/auth_users.sqlite3 "SELECT username, password_hash, salt, role, is_active FROM users;"
```

### Methode simple (Windows sans sqlite3, via Python)
Depuis la racine du projet:

```powershell
python -c "import sqlite3; c=sqlite3.connect('dashboard/auth_users.sqlite3'); print(c.execute('SELECT username, password_hash, salt, role, is_active FROM users').fetchall()); c.close()"
```

Resultat attendu:
1. password_hash contient une chaine hexadecimale longue (pas un mot de passe lisible en clair).
2. salt est renseigne pour chaque compte.
3. Les valeurs de password_hash ne doivent pas etre des mots simples comme admin ou user.

## 7. Depannage rapide
1. Erreur Git: verifier Internet et installation Git.
2. Erreur Docker: demarrer Docker Desktop/service Docker puis relancer.
3. Port 8501 deja utilise: fermer le process qui l'occupe puis relancer.
4. Erreur SQL: verifier les champs de Connexion SQL dans le dashboard.
