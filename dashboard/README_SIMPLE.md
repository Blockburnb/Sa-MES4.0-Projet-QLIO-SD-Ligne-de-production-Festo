# Tableau de bord simple (SQL)

## Ce qui a été fait
- Création de dashboard_final.py : copie de maquette.py avec remplacement des valeurs aléatoires par des données SQL (MariaDB MES4).
- Limitation des dépendances à : streamlit, pandas, plotly, mysql-connector-python.
- Mise en place de lanceurs natifs par OS : run_dashboard_linux.sh, run_dashboard_macos.sh, run_dashboard_windows.ps1.

## Source de données SQL
Le tableau de bord lit directement la base MariaDB exposée par Docker (compose dans TELEFAN/docker-compose.yml).
Les paramètres de connexion sont configurables dans la barre latérale (expander “Connexion SQL”) ou par variables d’environnement :
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

## Mettre à jour la base avec un extract plus récent
1) Remplacer l’extract SQL (ex: TELEFAN/FestoMES-2025-03-27.sql) par un dump plus récent.
2) Réimporter le dump dans MariaDB (via phpMyAdmin sur http://localhost:8080 ou via commande mysql dans le container).
3) Relancer le launcher de votre OS : le tableau de bord affichera les nouvelles données.

## Démarrage rapide
- Linux : exécuter ./run_dashboard_linux.sh à la racine du repo.
- macOS : exécuter ./run_dashboard_macos.sh à la racine du repo.
- Windows : exécuter .\run_dashboard_windows.ps1 à la racine du repo.
