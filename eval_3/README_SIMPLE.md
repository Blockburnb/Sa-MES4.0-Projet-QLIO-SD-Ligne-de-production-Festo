# Tableau de bord simple (SQL)

## Ce qui a été fait
- Création de maquette_simple.py : copie de maquette.py avec remplacement des valeurs aléatoires par des données SQL (MariaDB MES4).
- Limitation des dépendances à : streamlit, pandas, plotly, mysql-connector-python.
- Ajout d’un lanceur start_dashboard_simple.bat qui télécharge la BDD et les fichiers nécessaires puis lance le tableau de bord.

## Source de données SQL
Le tableau de bord lit directement la base MariaDB exposée par Docker (compose dans TELEFAN/docker-compose.yml).
Les paramètres de connexion sont configurables dans la barre latérale (expander “Connexion SQL”) ou par variables d’environnement :
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

## Mettre à jour la base avec un extract plus récent
1) Remplacer l’extract SQL (ex: TELEFAN/FestoMES-2025-03-27.sql) par un dump plus récent.
2) Réimporter le dump dans MariaDB (via phpMyAdmin sur http://localhost:8080 ou via commande mysql dans le container).
3) Relancer start_dashboard_simple.bat : le tableau de bord affichera les nouvelles données.

## Démarrage rapide
- Exécuter start_dashboard_simple.bat à la racine du repo (ou seul, il télécharge le nécessaire).
