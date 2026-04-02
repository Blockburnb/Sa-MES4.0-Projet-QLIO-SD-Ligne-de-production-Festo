# Documentation Analytique — Choix et Pertinence des Indicateurs

> **Projet :** Tableau de bord de pilotage de production — ligne Festo  
> **Contexte :** BTS QLIO — Projet MES 4.0

---

## Table des matières

1. [Introduction : La démarche de sélection des indicateurs](#1-introduction--la-démarche-de-sélection-des-indicateurs)
2. [Indicateurs de production en temps réel](#2-indicateurs-de-production-en-temps-réel)
   - [Autonomie Robot](#21-autonomie-robot)
   - [OF Réalisés](#22-of-réalisés)
   - [Production Réalisée](#23-production-réalisée)
3. [Indicateurs de stockage et logistique](#3-indicateurs-de-stockage-et-logistique)
   - [Taux d'Occupation du Stockage](#31-taux-doccupation-du-stockage)
   - [Mouvements de Stocks](#32-mouvements-de-stocks)
4. [Indicateurs robot (AGV)](#4-indicateurs-robot-agv)
   - [Historique d'Autonomie](#41-historique-dautonomie)
   - [Distance Parcourue](#42-distance-parcourue)
5. [Indicateurs qualité](#5-indicateurs-qualité)
   - [Production Hebdomadaire](#51-production-hebdomadaire)
   - [Production Détaillée](#52-production-détaillée)
   - [Taux d'Occupation Machine](#53-taux-doccupation-machine)
   - [Temps de Cycle & NVA](#54-temps-de-cycle--nva)
   - [Taux de Défauts](#55-taux-de-défauts)
   - [Causes de Non-Conformité (Pareto)](#56-causes-de-non-conformité-pareto)
   - [Taux de Conformité](#57-taux-de-conformité)
   - [Consommation Énergétique](#58-consommation-énergétique)
6. [Cohérence globale du tableau de bord](#6-cohérence-globale-du-tableau-de-bord)
7. [Ce que nous avons volontairement écarté](#7-ce-que-nous-avons-volontairement-écarté)
8. [Synthèse](#8-synthèse)

---

## 1. Introduction : La démarche de sélection des indicateurs

### Pourquoi des indicateurs dans un MES ?

Un **Système d'Exécution de la Production (MES — Manufacturing Execution System)** a pour mission de relier le niveau décisionnel (ERP, planification) au niveau opérationnel (machines, robots, opérateurs). Sans indicateurs mesurables, cette liaison est aveugle : les décisions sont prises sur des intuitions plutôt que sur des faits.

Dans le cadre de la ligne Festo, l'enjeu était de sélectionner des indicateurs qui répondent à trois critères :

1. **Actionnabilité** — L'indicateur doit conduire à une décision ou une action concrète. Un indicateur qu'on observe sans pouvoir agir dessus n'a pas sa place dans un tableau de bord opérationnel.
2. **Disponibilité des données** — L'indicateur doit être calculable à partir des données réellement présentes dans la base MariaDB de la ligne Festo (`MES4`).
3. **Pertinence métier** — L'indicateur doit répondre à une question que se posent effectivement les acteurs concernés (opérateur, superviseur, chef de production).

Nous avons structuré notre sélection autour de **quatre domaines** couvrant l'ensemble du périmètre de pilotage d'une ligne de production automatisée :

| Domaine | Problématique couverte |
|---|---|
| **Production en temps réel** | Est-ce qu'on produit selon le plan ce jour-là ? |
| **Logistique / Stockage** | Les flux physiques sont-ils fluides ? |
| **Robot / AGV** | Le robot est-il disponible et efficace ? |
| **Qualité** | Ce qu'on produit est-il conforme ? À quel coût ? |

---

## 2. Indicateurs de production en temps réel

### 2.1 Autonomie Robot

**Question à laquelle il répond :** *Le robot peut-il continuer à travailler sans intervention maintenance ?*

**Pourquoi cet indicateur ?**

La ligne Festo utilise un robot Robotino (AGV — Automated Guided Vehicle) comme vecteur de transport entre les postes. Ce robot est un **goulot d'étranglement potentiel** : s'il tombe en panne ou nécessite une recharge, toute la ligne est arrêtée ou ralentie. La disponibilité du robot conditionne directement la capacité de production.

L'autonomie est exprimée comme le pourcentage du temps sans erreur détectée (`ErrorL0`, `ErrorL1`, `ErrorL2` à 0). Ce choix est délibéré : les erreurs machines sont des signaux précoces de défaillance imminente, avant même un arrêt complet. Surveiller l'autonomie en continu permet d'anticiper une maintenance préventive plutôt que de subir une panne.

**Pertinence pour chaque rôle :**
- **Opérateur :** Savoir en temps réel si le robot est opérationnel pour adapter son rythme de travail.
- **Superviseur / Chef de production :** Déclencher une intervention maintenance si l'autonomie chute sous un seuil critique.

**Seuils retenus :** Vert ≥ 70 % | Orange 30–70 % | Rouge < 30 %

---

### 2.2 OF Réalisés

**Question à laquelle il répond :** *Combien d'ordres de fabrication avons-nous clôturés par rapport à ce qui était planifié ?*

**Pourquoi cet indicateur ?**

L'**Ordre de Fabrication (OF)** est l'unité de base du pilotage de production : chaque OF correspond à une série de pièces à produire selon une fiche technique. Mesurer le ratio OF clôturés / OF planifiés donne une vision immédiate du **taux d'avancement** du programme de production.

Cet indicateur est prioritairement destiné aux opérateurs et superviseurs pour détecter un retard en cours de journée, avant qu'il ne se cumule sur la semaine. Il répond à la logique du pilotage **court terme** (heure par heure ou quart par quart).

**Pertinence métier :** En production de série, un retard d'OF non détecté en temps réel est difficile à rattraper. Afficher cet indicateur en barre de progression (et non en simple chiffre) donne une lecture immédiate de l'écart sans calcul mental.

---

### 2.3 Production Réalisée

**Question à laquelle il répond :** *Combien d'unités avons-nous produites par rapport à notre objectif ?*

**Pourquoi cet indicateur ?**

Là où les OF mesurent l'avancement des ordres, la **Production Réalisée** mesure le volume physique de sortie. Ces deux indicateurs sont complémentaires : un OF peut être clôturé mais avec un nombre d'unités inférieur à l'objectif (rebuts, arrêts partiels).

Exprimer la production en unités absolues (et non en pourcentage seulement) permet à l'opérateur de savoir exactement combien de pièces ont été produites — information directement utilisable pour remplir un rapport de production ou communiquer avec la logistique aval.

**Pertinence :** Cet indicateur est le plus concret et le plus actionnable pour un opérateur. Il représente directement le résultat de son travail sur la période.

---

## 3. Indicateurs de stockage et logistique

### 3.1 Taux d'Occupation du Stockage

**Question à laquelle il répond :** *Y a-t-il suffisamment d'espace disponible dans les buffers pour absorber la production ?*

**Pourquoi cet indicateur ?**

Dans une ligne de production automatisée, les **buffers** (zones de stockage intermédiaires) jouent un rôle d'amortisseur entre les postes. Si un buffer se remplit à 100 %, la ligne en amont doit s'arrêter (blocage). Inversement, un buffer vide signifie que la ligne en aval est en attente (manque d'approvisionnement).

Le **taux d'occupation** est donc un indicateur de **tension logistique** : à 85 % ou plus, il faut anticiper un risque de blocage et agir (évacuation, réorganisation des flux, appel au responsable logistique).

**Choix de la jauge circulaire :** La jauge est visuellement plus intuitive qu'un chiffre pour une lecture rapide. Les codes couleur (vert / orange / rouge) permettent une détection d'anomalie sans lecture du chiffre exact.

**Seuils retenus :**
- **< 70 %** (vert) : Situation nominale, flux fluide
- **70–85 %** (orange) : Vigilance, risque de saturation à surveiller
- **> 85 %** (rouge) : Alerte, action corrective immédiate nécessaire

Ces seuils sont cohérents avec les pratiques lean manufacturing (buffer zone ≈ 15–30 % de capacité libre recommandée).

---

### 3.2 Mouvements de Stocks

**Question à laquelle il répond :** *Les entrées et sorties de stockage sont-elles équilibrées et régulières ?*

**Pourquoi cet indicateur ?**

Le taux d'occupation seul est un **état statique** : il indique le niveau actuel mais pas la tendance. Les **mouvements de stocks** (entrées vs. sorties quotidiennes) permettent de détecter :

- Un déséquilibre durable (les entrées dépassent les sorties = saturation progressive)
- Une irrégularité anormale (absence de mouvement un jour donné = arrêt non signalé ?)
- Un pic inhabituel (livraison ou expédition exceptionnelle à analyser)

L'affichage en **courbe sur 7 jours** transforme cet indicateur en outil d'**analyse de tendance**, utile pour le superviseur qui souhaite comprendre une dérive avant qu'elle devienne critique.

---

## 4. Indicateurs robot (AGV)

### 4.1 Historique d'Autonomie

**Question à laquelle il répond :** *L'autonomie du robot se dégrade-t-elle dans le temps ?*

**Pourquoi cet indicateur ?**

L'autonomie en temps réel (KPI 1) indique l'état actuel, mais ne permet pas de détecter une **dégradation progressive**. L'historique d'autonomie sur 7 jours révèle des tendances : si le robot perd de l'autonomie chaque jour un peu plus tôt, c'est un signal de vieillissement de la batterie ou d'un problème mécanique en cours d'apparition.

Combiné aux heures d'utilisation (barres), cet indicateur permet de **normaliser l'analyse** : une autonomie de 80 % sur 4 heures d'utilisation est très différente d'une autonomie de 80 % sur 8 heures. La lecture simultanée des deux séries enrichit le diagnostic.

**Usage préventif :** Cet indicateur est principalement utile pour la **maintenance préventive** — il permet de planifier une intervention avant la panne.

---

### 4.2 Distance Parcourue

**Question à laquelle il répond :** *Le robot parcourt-il les distances attendues selon le programme de production ?*

**Pourquoi cet indicateur ?**

La distance parcourue est un **proxy de l'activité réelle** du robot. Si la distance journalière chute brutalement, cela peut indiquer :
- Un arrêt du robot (panne, recharge prolongée)
- Un changement de programme (moins de rotations planifiées)
- Un problème de navigation (détours, recalculs d'itinéraire)

À l'inverse, une distance anormalement élevée peut signaler un problème de trajectoire (le robot tourne en boucle ou prend des chemins non optimaux).

La **distance cumulée** permet aussi de déclencher les maintenances périodiques (vidange, vérification des roues) à intervalle régulier, comme on le fait avec le kilométrage d'un véhicule.

---

## 5. Indicateurs qualité

### 5.1 Production Hebdomadaire

**Question à laquelle il répond :** *Atteint-on l'objectif de production de la semaine ?*

**Pourquoi cet indicateur ?**

La **semaine** est l'unité de planification la plus courante en production industrielle (programme hebdomadaire, réunions de production, reporting client). L'objectif de 720 unités/semaine n'est pas arbitraire : il correspond au rythme cible de la ligne Festo calculé à partir de la capacité théorique et du taux de disponibilité attendu.

Présenter la production réelle vs. l'objectif sous forme de deux cartes côte-à-côte permet une lecture instantanée de l'écart sans calcul. C'est l'information de synthèse qu'un chef de production lit en priorité lors de sa ronde ou de son point d'équipe.

---

### 5.2 Production Détaillée

**Question à laquelle il répond :** *Quel jour y a-t-il eu un décrochage par rapport au plan ?*

**Pourquoi cet indicateur ?**

La production hebdomadaire donne le résultat global, mais le tableau détaillé jour par jour permet d'**analyser les causes** : si le vendredi est systématiquement en dessous de l'objectif, c'est peut-être lié à des approvisionnements de fin de semaine ou à une réduction d'équipe. Cette granularité jour/jour est indispensable pour conduire une analyse des causes racines (méthode 5 pourquoi, diagramme d'Ishikawa).

**Pertinence :** Les colonnes "Écart" et "% Atteinte" transforment le tableau en outil d'analyse, pas seulement de constat.

---

### 5.3 Taux d'Occupation Machine

**Question à laquelle il répond :** *Les machines produisent-elles pendant la totalité du temps disponible ?*

**Pourquoi cet indicateur ?**

Le taux d'occupation machine est un **indicateur d'efficience** : il mesure la proportion du temps où la machine produit réellement, par rapport au temps total disponible (hors arrêts planifiés). Un taux faible révèle des **pertes de production** qui peuvent avoir plusieurs origines :
- Arrêts non planifiés (pannes, changement d'outil)
- Micro-arrêts répétés (bourrage, vide d'approvisionnement)
- Sous-cadence (machine qui produit mais lentement)

C'est l'un des composants de l'**OEE (Overall Equipment Effectiveness)**, indicateur de référence en lean manufacturing. Nous n'avons pas calculé l'OEE complet (qui intègrerait aussi la performance et la qualité) car les données disponibles ne permettaient pas un calcul fiable de tous ses composants. Le taux d'occupation machine est le composant **disponibilité** de l'OEE.

---

### 5.4 Temps de Cycle & NVA

**Question à laquelle il répond :** *Quelle part du temps de production est gaspillée en activités sans valeur ajoutée ?*

**Pourquoi cet indicateur ?**

Le **Temps Non à Valeur Ajoutée (NVA)** est un concept central du lean manufacturing : tout temps passé à attendre, transporter sans nécessité, ou corriger une erreur est un gaspillage (*muda*) qui augmente le coût de revient sans augmenter la valeur du produit.

Décomposer le temps de cycle en VA / NVA permet de **quantifier les gaspillages** et de prioriser les actions d'amélioration. Un graphique en barres empilées est le format le plus adapté pour cette visualisation : il montre à la fois le temps total et la proportion relative de chaque partie.

**Pertinence :** Dans le cadre d'un projet QLIO (Qualité, Logistique, Organisation), cet indicateur est particulièrement adapté car il est directement lié aux méthodes d'amélioration continue enseignées en formation.

---

### 5.5 Taux de Défauts

**Question à laquelle il répond :** *Quelle est la proportion de pièces produites hors conformité ?*

**Pourquoi cet indicateur ?**

Le taux de défauts est l'indicateur qualité le plus fondamental. Il mesure directement la **capabilité qualitative** du processus. Le seuil de 2,25 % retenu n'est pas arbitraire : il correspond à un **niveau 3 sigma** (environ 97,75 % de conformité), seuil couramment utilisé comme limite acceptable avant déclenchement d'une action corrective formelle.

L'affichage en **courbe temporelle** avec zones colorées est préférable à une simple valeur numérique car il permet de voir si le taux augmente, diminue, ou oscille — ce qui conduit à des diagnostics très différents (dérive progressive vs. problème ponctuel vs. variation normale).

**Pertinence :** La corrélation entre les pics de défauts et d'autres événements (changement d'outillage, nouveau lot de matière première, opérateur différent) ne peut être faite qu'avec une vue temporelle.

---

### 5.6 Causes de Non-Conformité (Pareto)

**Question à laquelle il répond :** *Sur quelles causes de défauts doit-on concentrer nos efforts en priorité ?*

**Pourquoi le diagramme de Pareto ?**

Le **principe de Pareto** (règle des 80/20) stipule que 20 % des causes génèrent 80 % des problèmes. Dans un contexte de production, il serait contre-productif de traiter toutes les causes de non-conformité avec la même intensité : les ressources d'amélioration (temps ingénieur, investissement, formation) sont limitées.

Le diagramme de Pareto, en combinant les barres (volume par cause) et la courbe cumulative, permet en un coup d'œil d'**identifier les 2 ou 3 causes qui concentrent l'essentiel des défauts**. C'est l'outil graphique standard de la démarche qualité (référencé dans la norme ISO 9001).

**Pertinence :** Cet indicateur n'est pas seulement un constat — il est directement actionnable : il guide les réunions de résolution de problèmes (8D, PDCA) vers les causes à traiter en priorité.

---

### 5.7 Taux de Conformité

**Question à laquelle il répond :** *Quel pourcentage de notre production est livrable ?*

**Pourquoi cet indicateur en complément du taux de défauts ?**

Le taux de conformité (`100 − taux de défauts`) peut paraître redondant. Il est pourtant maintenu séparément pour deux raisons :

1. **Lecture positive vs. négative :** Le taux de défauts focalise l'attention sur le problème ; le taux de conformité focalise sur la performance. Selon la culture de l'équipe et l'objectif de communication (rapport client, revue de direction), l'un ou l'autre est plus approprié.
2. **Engagement client :** Dans une relation fournisseur/client, le taux de conformité est souvent l'indicateur contractuel (ex. : engagement de 98 % de conformité). Le rendre visible directement en tableau de bord facilite le suivi de cet engagement.

---

### 5.8 Consommation Énergétique

**Question à laquelle il répond :** *Quel est le coût énergétique de notre production ?*

**Pourquoi intégrer un indicateur énergétique ?**

L'énergie est un **coût de production direct** dont l'importance croît avec les prix de l'électricité et les enjeux RSE (Responsabilité Sociétale des Entreprises). Dans un contexte MES 4.0, l'intégration des données énergétiques dans le tableau de bord de production est un marqueur de maturité industrielle.

Cet indicateur permet de :
- **Corréler consommation et production** : une consommation stable avec une production en baisse révèle une inefficience énergétique (machines qui tournent à vide).
- **Déclencher des alertes** : un pic de consommation inhabituel peut signaler un dysfonctionnement machine.
- **Suivre les progrès** d'une démarche d'efficience énergétique (Décret Tertiaire, ISO 50001).

**Source de données :** La colonne `ElectricEnergyReal` dans `tblfinstep` fournit la consommation mesurée à chaque étape de fabrication — donnée réelle et non estimée, ce qui renforce la fiabilité de l'indicateur.

---

## 6. Cohérence globale du tableau de bord

### 6.1 Complémentarité des indicateurs

Les 15 indicateurs ont été sélectionnés pour qu'ils se **complètent sans se dupliquer** :

```
Disponibilité         Qualité              Coût / Efficience
─────────────────     ───────────────────  ─────────────────────
Autonomie Robot       Taux de Défauts      Consommation Énergie
Occupation Machine    Taux de Conformité   Temps Cycle & NVA
OF Réalisés           Causes NC (Pareto)
Distance Robot        Production Détaillée
```

Cette structure couvre les trois dimensions du triptyque industriel **QCD (Qualité / Coût / Délai)** :
- **Qualité :** Taux de défauts, conformité, causes NC, temps cycle NVA
- **Coût :** Consommation énergétique, taux d'occupation machine, NVA
- **Délai :** OF réalisés, production réalisée, production hebdomadaire

### 6.2 Cohérence temporelle

Le **filtre de période global** appliqué à tous les KPIs permet de garantir que tous les indicateurs sont lus sur la même fenêtre temporelle. Cela évite les comparaisons incohérentes (ex. : défauts sur 7 jours vs. production sur 1 jour) et facilite la corrélation entre indicateurs lors d'une analyse.

### 6.3 Adaptation aux rôles

Le tableau de bord n'affiche pas les mêmes informations à tout le monde :

| Rôle | Focus principal |
|---|---|
| **Opérateur** | Production en cours, autonomie robot (réaction immédiate) |
| **Superviseur** | Tendances qualité, stockage, occupation machine (pilotage à la journée) |
| **Chef de production** | Vue hebdomadaire, conformité, énergie (reporting, décisions stratégiques) |
| **Admin** | Gestion système, configuration des accès |

Cette personnalisation est possible grâce au système RBAC et aux permissions KPI individuelles — elle garantit que chaque acteur est **concentré sur les informations qui relèvent de ses responsabilités**.

---

## 7. Ce que nous avons volontairement écarté

Certains indicateurs ont été envisagés puis écartés, pour les raisons suivantes :

| Indicateur écarté | Raison |
|---|---|
| **OEE complet** | Nécessite performance et qualité mesurables séparément ; données partiellement disponibles |
| **Coût de non-qualité (CNQ)** | Requiert des données de valorisation (coût unitaire) absentes de la base MES |
| **MTBF / MTTR** (fiabilité machine) | Nécessite un historique de pannes long et structuré non disponible dans la base actuelle |
| **Satisfaction client** | Hors périmètre de la ligne de production Festo |
| **Indicateurs de flux (VSM)** | Pertinents mais nécessitent une cartographie statique en dehors du scope MES |

L'exclusion de ces indicateurs n'est pas un oubli : c'est un choix de **faisabilité** (données disponibles) et de **lisibilité** (un tableau de bord trop chargé perd en efficacité opérationnelle).

---

## 8. Synthèse

Le choix des 15 indicateurs du tableau de bord MES 4.0 repose sur trois piliers :

### Pilier 1 — Couverture métier complète
Les indicateurs couvrent l'ensemble de la chaîne de valeur de la ligne Festo : de la disponibilité des équipements (robot, machine) aux résultats qualité (défauts, conformité) en passant par la logistique (stockage, flux) et l'efficience (énergie, NVA). Aucun domaine critique n'est laissé sans indicateur.

### Pilier 2 — Actionnabilité à tous les niveaux
Chaque indicateur répond à une question concrète posée par un acteur précis. Le tableau de bord n'est pas un écran de surveillance passif : il est conçu pour déclencher des décisions (lancer une maintenance, alerter le superviseur, réviser le programme de production, prioriser une action qualité).

### Pilier 3 — Ancrages dans les données réelles
Tous les indicateurs s'appuient sur des données mesurées par la ligne Festo elle-même et stockées dans la base `MES4`. Il n'y a pas d'indicateurs "calculés" sur des estimations ou des valeurs saisies manuellement. Cette exigence de **traçabilité des données** est un fondement du MES 4.0 et garantit la fiabilité des tableaux de bord présentés aux décideurs.

---

> *"On ne pilote bien que ce que l'on mesure correctement."*  
> — Adaptation du principe de Lord Kelvin, appliqué au management industriel
