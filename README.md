# 📱 Tableau de Bord de Pilotage de Production - QLIO

**Projet :** Conception et développement d'une Web App décisionnelle pour le pilotage d'une chaîne de production de téléphones.
**Client :** QLIO (Qualité, Logistique Industrielle et Organisation)
**Fournisseur :** Groupe 6

---

## 📂 Documents et Ressources

Les fichiers et données nécessaires au projet sont accessibles via les liens suivants :

* **📂 Google Drive du Projet :** [Accéder au Drive](https://drive.google.com/drive/folders/1yjzKAwdKu8T9PpzbTniVk4mx_j-2bvwi)
* **📄 Fichiers Professeurs / Données Sources :** [Lien Univ Lyon 2](https://bul.univ-lyon2.fr/index.php/s/FnPb1Sx6WTaLKrm)
* **🌐 Site Stat & More :** [statandmore.com/univ/](https://statandmore.com/univ/)

---

## 📝 Cahier des Charges Technique et Fonctionnel

Conformément aux exigences du client (Stat & More), l'application doit respecter les contraintes suivantes :

### 🛠️ Contraintes Techniques

* **Langage & Framework :** Développement **100% Python** (avec HTML/CSS si besoin). Utilisation de frameworks type **Flask, Django ou Streamlit**.
* **Données :** Traitement de fichiers **CSV** (pas de base de données SQL obligatoire).
* **Environnement :** Création d'un environnement virtuel (`venv`) local contenant toutes les bibliothèques nécessaires. L'environnement doit être **entièrement reproductible** sur le PC de l'évaluateur.
* **Sécurité :**
* Page de **Login** obligatoire.
* Mot de passe stocké de manière sécurisée (**haché**).
* Gestion des erreurs (Page **404 Not Found** personnalisée).



### 💻 Interface et Ergonomie

L'application doit comporter **au minimum 5 pages Web** et respecter la structure suivante :

1. **Bandeau Gauche :** Informations utiles, filtres ou paramètres utilisateurs.
2. **Bandeau Haut :** Navigation entre les pages et bouton de **Déconnexion** (Logout) à droite.
3. **Zone Centrale :** Affichage du tableau de bord et des visualisations.
4. **Accès aux sources :** Un lien URL permettant de consulter/télécharger les données brutes.

### ⚙️ Fonctionnalités Clés

* **Filtrage Temporel Global :** Chaque page doit disposer d'un sélecteur de plage de temps qui **filtre dynamiquement tous les indicateurs** présents sur la page.
* **Indicateurs (KPIs) :** Les indicateurs sont définis selon les besoins spécifiques des clients QLIO (Production de téléphones). Vous êtes libres de leur représentation (pertinence, agencement et justesse seront évalués).

---

## 📅 Planning Prévisionnel et Livrables

Le projet est jalonné par 4 évaluations majeures. Les livrables doivent être envoyés impérativement via **SwissTransfer** à `benoit.riou@statandmore.com` aux dates indiquées.

### 🟢 Évaluation 1 : Recherche Bibliographique

* **Date limite :** 12 Décembre 2025 à 17h00.
* **Livrable :** Document Word ou PDF de 12 pages (hors annexes) avec sommaire, intro et conclusion.
* **Contenu attendu :**
1. Quantité de données nécessaire pour un portail web.
2. Nécessité d'échantillonnage des données.
3. Règles de contrôle qualité des données.
4. Fréquence de mise à jour des données.
5. Fonctionnalités attendues d'un portail décisionnel.
6. Impact des fonctionnalités sur le choix des logiciels.
7. Méthodes de travail collaboratif (Agile, Waterfall, Kanban, Scrum) et pertinence.



### 🟡 Évaluation 2 : Analyse et Conception

* **Date limite :** 23 Janvier 2026 à 17h00.
* **Livrables :**
1. **Référentiel de données (Excel) :** Nom variable, définition, métrique, source, nettoyages à prévoir.
2. **Modèle Conceptuel de Données (MCD) :** Format PDF.
3. **Note de Synthèse (PDF, max 10 pages) :** Description des fonctionnalités, environnement technique, sécurité, ergonomie, calcul des indicateurs.
4. **Maquette :** Format PDF, PowerPoint ou lien PenPot.



### 🔴 Évaluation 3 : Application Finale et Documentation

* **Date limite :** 02 Avril 2026 à 17h00.
* **Livrables :**
1. **Données travaillées** et **Scripts** complets.
2. **Documentation Technique (Installation) :** Procédure pour tester l'app en local (Windows 10 + venv), liste des paquets et versions.
3. **Documentation Fonctionnelle :** Description de chaque fonctionnalité de la WebApp.
4. **Documentation Analytique :** Justification des indicateurs choisis et pertinence métier pour QLIO.



### 🟣 Évaluation 4 : Soutenance Orale

* **Date :** 03 Avril 2026 (Créneau de 30 min entre 8h00 et 17h30).
* **Format :** 20 min de présentation + 10 min de Questions/Réponses.
* **Contenu de la présentation :**
1. Étapes du projet (de la prise de connaissance à la livraison).
2. **Démonstration fonctionnelle** de l'application.
3. Présentation d'un résultat ou d'une notion marquante découverte dans les données.
4. Conclusion (Retours d'expérience, apprentissages).



---

## 🗓️ Calendrier des Sessions de Travail (Autonomie)

Voici les créneaux identifiés pour les "Sprints" et le travail de groupe (Dates clés pages 90-91) :

* **Décembre 2025 :**
* 01/12 (8h-16h), 02/12 (8h-10h, 13h30-17h30), 03/12 (8h-12h), 05/12 (8h-10h), 08/12 (8h-12h), 09/12 (15h30-17h30), 12/12 (8h-12h), 21/12 (13h30-17h30).


* **Janvier 2026 :**
* 23/01 (8h-16h), 27/01 (15h30-17h30), 28/01 (10h-12h, 13h30-15h30), 29/01 (8h-16h), 30/01 (8h-16h).


* **Février 2026 :**
* 23/02 (8h-12h), 24/02 (8h-12h), 25/02 (8h-16h), 26/02 (8h-12h).


* **Avril 2026 :**
* 02/04 (8h-12h) - *Dernière ligne droite avant livraison*.



---

## 📥 Installation et Test (Procédure à documenter)

*(Cette section sera à compléter précisément pour l'Eval 3)*

1. **Cloner le dépôt :**
```bash
git clone https://github.com/votre-repo/qlio-dashboard.git
cd qlio-dashboard

```


2. **Créer l'environnement virtuel :**
```bash
python -m venv env
source env/bin/activate  # ou env\Scripts\activate sur Windows

```


3. **Installer les dépendances :**
```bash
pip install -r requirements.txt

```


4. **Lancer l'application :**
```bash
python main.py  # ou streamlit run app.py

```



---

## 📞 Communication

Pour toute question technique ou fonctionnelle :

* **Contact :** M. Benoit Riou (`benoit.riou@statandmore.com`)
* **Procédure :** Lister les questions par mail et solliciter une réponse (mail ou visio). Volume total d'accompagnement disponible : 96h (distanciel).

*Projet réalisé dans le cadre du module "Analyse et Conception d'un Outil Décisionnel" - IUT Lumière Lyon 2.*
