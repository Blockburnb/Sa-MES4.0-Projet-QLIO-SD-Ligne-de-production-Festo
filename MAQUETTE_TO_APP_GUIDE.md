# Transformer la maquette en application utilisant la base SQL

Objectif

- Décrire, étape par étape, ce qu'il faut faire pour convertir la maquette Python existante en une application fonctionnelle qui utilise la base de données (MariaDB/MySQL) présente dans le dossier `TELEFAN/data/mes4` comme source de données.

Prérequis

- OS: Windows (PowerShell disponible). 
- Python 3.10+ recommandé.
- Git configuré et accès au dépôt distant.
- Accès au serveur MariaDB local (ou conteneur Docker) contenant la base `mes4` (fichiers dans `TELEFAN/data/mes4`).
- Connaissance de base de Python, SQL, et d'un framework web (Flask, FastAPI, Django) et d'un framework frontend (React/Vue) si une UI web est prévue.

Ressources et choix techniques recommandés (exemples)

- Backend: Python + FastAPI (ou Flask). FastAPI est recommandé pour rapidité de développement et documentation automatique (OpenAPI).
- ORM: SQLAlchemy (avec Alembic pour migrations) ou PonyORM.
- Driver MariaDB/MySQL: `PyMySQL` ou `mysqlclient`.
- Frontend: React (create-react-app / Vite) ou une interface minimale en Jinja2 si on restaure une app serveur-rendered.
- Conteneurisation: `docker-compose` (il y a déjà un `TELEFAN/docker-compose.yml`).
- Tests: pytest.

Étapes détaillées

1) Analyse de la maquette existante

- Localiser `maquette.py` et `maquette_VF.py` (dans `production rendu groupe/eval_2/`).
- Lire le code : identifier les fonctions principales, flux de données, quelles données sont hardcodées ou simulées, quelles entités (ex: order, step, machine, error) apparaissent.
- Lister les modèles de données nécessaires (tables et champs utilisés).

2) Préparer l'environnement de développement

- Créer un nouvel environnement virtuel dans la racine du projet:
  - powershell: python -m venv .venv
  - powershell: .\.venv\Scripts\Activate.ps1
- Créer `requirements.txt` puis installer:
  - pip install fastapi uvicorn sqlalchemy alembic pymysql pydantic[dotenv] python-dotenv pytest
- Créer un dossier `backend/` pour le code serveur.

3) Connexion à la base de données

- Récupérer les paramètres de connexion MariaDB (hôte, port, user, password, database). Si la base est fournie via fichiers InnoDB, démarrer le service MariaDB via docker-compose ou restaurer la base sur une instance MariaDB.
- Utiliser `python-dotenv` pour stocker `DATABASE_URL` dans `.env`: exemple `mysql+pymysql://user:password@127.0.0.1:3306/mes4`.
- Dans le backend, créer le moteur SQLAlchemy central et une session scoped.

4) Modéliser les données

- Pour chaque entité utilisée par la maquette, créer une classe SQLAlchemy (ou déclarative) qui reflète la structure de la table (nom, colonnes importantes).
- Si vous préférez utiliser le schéma existant sans ORM, créer une couche DAO qui exécute requêtes SQL brutes.
- Si des tables existent déjà (fichiers .frm/.ibd), reverse-engineer le schéma si nécessaire (ou consulter `schema_BDD.pdf` dans `TELEFAN/`).

5) Intégrer la logique de la maquette dans des services

- Refactoriser les fonctions de `maquette.py` en modules réutilisables (ex: `services/processing.py`, `services/orders.py`).
- Séparer la logique pure (calculs, règles métiers) de la logique d'I/O (lecture DB, écriture DB, HTTP).
- Rendre les fonctions idempotentes et testables.

6) Créer une API REST (ou GraphQL)

- Définir les endpoints nécessaires (exemples):
  - GET /orders
  - GET /orders/{id}
  - POST /orders
  - PUT /orders/{id}/status
  - GET /machines
  - POST /simulate-step
- Pour chaque endpoint, appeler le service métier qui lit/écrit dans la base.
- Utiliser Pydantic pour les schémas de requête/réponse.

7) UI / intégration frontend

- Si la maquette est une application console/PyQt, décider si on migre vers une UI web ou qu'on garde un client desktop.
- Pour web: créer un projet React/Vite dans `frontend/`, implémenter pages qui consomment l'API.
- Pour rendu serveur: utiliser Jinja2 templates dans le backend.

8) Tests et validation

- Écrire tests unitaires pour la logique refactorisée (pytest).
- Écrire tests d'intégration pour les endpoints (testclient FastAPI ou requests) en utilisant une base de test (ex: conteneur MariaDB temporaire ou SQLite in-memory si compatible).

9) Migrations et gestion du schéma

- Mettre en place Alembic pour versionner les changements du schéma si vous modifiez la structure.
- Garder migrations sous `backend/migrations/`.

10) Dockerisation et déploiement

- Adapter `TELEFAN/docker-compose.yml` ou créer `docker-compose.app.yml` qui lance:
  - le service mariadb (ou pointer vers l'existant)
  - le backend (uvicorn) et le frontend (npm build / nginx)
- Exemples de commandes PowerShell:
  - docker-compose -f .\TELEFAN\docker-compose.yml up -d
  - docker-compose -f .\docker-compose.app.yml up --build -d

11) Sécurité et bonnes pratiques

- Ne pas committer `.env` contenant mots de passe.
- Utiliser des comptes DB avec privilèges limités.
- Valider les entrées côté serveur.
- Configurer CORS pour l'API si frontend séparé.

12) Checklist finale

- [ ] Maquette refactorée en modules testables
- [ ] Connexion DB fonctionnelle et tests d'accès
- [ ] Modèles/ORM créés pour entités principales
- [ ] API REST opérationnelle avec docs OpenAPI
- [ ] Frontend consommant l'API (ou interface serveur rendue)
- [ ] Tests unitaires et d'intégration en place
- [ ] Docker-compose pour dev et prod
- [ ] Pipeline CI (facultatif) pour tests et build

Mapping rapide (exemple) - maquette -> app

- Fonctions d'entrée/sortie de `maquette.py` -> endpoints FastAPI
- Fonctions de calcul -> services dans `backend/services/`
- Données simulées -> requêtes SQL vers tables `tblfinorder`, `tblfinstep`, `tblmachine...`

Commands utiles (PowerShell)

- Créer venv
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1
- Installer dépendances
  - pip install -r requirements.txt
- Lancer backend en dev
  - uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
- Lancer docker-compose
  - docker-compose -f .\TELEFAN\docker-compose.yml up -d

Annexes

- Consulter `TELEFAN/schema_BDD.pdf` pour le schéma réel des tables.
- Inspecter `production rendu groupe/eval_2/maquette.py` pour identifier la logique à porter.

Si tu veux, je peux :
- générer l'ossature d'un projet FastAPI + SQLAlchemy dans `backend/` et un README d'installation détaillé;
- analyser automatiquement `maquette.py` et proposer une liste de modèles (classes ORM) à créer.

