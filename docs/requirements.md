# Cahier des charges — basket-analytics

## 1. Contexte

Outil interne développé pour une association de basket, destiné dans un premier
temps à une équipe évoluant en championnat départemental. L'objectif est
d'analyser la vidéo d'un match pour produire automatiquement des statistiques
d'équipe et individuelles, avec une étape de validation humaine systématique
(l'IA ne cherche pas à être parfaite dès le départ — elle propose, l'humain
corrige).

Le développement est quasi entièrement délégué à Claude Code, de façon
autonome, par phases validées une à une. Ce document, ainsi que
`architecture.md`, `data_model.md` et `statistics_definition.md`, constituent
la référence que chaque phase doit respecter.

## 2. Objectif produit

À partir d'une vidéo de match, produire :

- les statistiques d'équipe (score, possessions, tirs, rebonds, fautes, etc.) ;
- les statistiques individuelles par joueur ;
- une liste d'événements horodatés, consultables et corrigibles ;
- une localisation des tirs sur un terrain 2D (shot chart) ;
- un export des résultats (CSV / Excel / PDF) ;
- une interface de correction humaine pour fiabiliser les résultats.

Le mode temps réel / quasi-live est un objectif à long terme (M16), explicitement
**hors périmètre du MVP**.

## 3. Entrées

| Paramètre            | Valeur retenue pour le MVP                                   |
|-----------------------|----------------------------------------------------------------|
| Source vidéo          | Fichier vidéo (MP4), caméra fixe                               |
| Nombre de caméras     | 1                                                               |
| Cadrage               | Vue d'ensemble du terrain, fixe (pas de suivi/zoom manuel)      |
| Résolution / FPS      | Variable selon le matériel du club — à mesurer sur les premiers échantillons, pas de contrainte stricte imposée à l'avance |
| Données de test       | Extraits de matchs publics (YouTube) dans un premier temps, puis vidéos réelles du club |

Le pipeline doit être conçu pour qu'une caméra mobile ou plusieurs caméras
puissent être ajoutées plus tard sans réécriture complète (voir
`architecture.md`), mais ce n'est pas un objectif du MVP.

## 4. Sorties

### 4.1 Statistiques d'équipe

Score, possessions, pace, FG (tentés/réussis), 2PT, 3PT, lancers francs,
rebonds (off./déf.), passes décisives, interceptions, contres, pertes de
balle, fautes. Détail des formules dans `statistics_definition.md`.

### 4.2 Statistiques individuelles

Par joueur : minutes jouées, points, FGM/FGA, 2PM/2PA, 3PM/3PA, FTM/FTA,
rebonds offensifs/défensifs, passes décisives, interceptions, contres,
pertes de balle, fautes.

### 4.3 Événements

Chaque événement détecté (ou saisi manuellement) est une entité horodatée et
traçable — voir `data_model.md` pour le schéma complet (`Event`, et ses
sous-types `ShotEvent`, `ReboundEvent`, `FoulEvent`, `TurnoverEvent`,
`PassEvent`, `StealEvent`, `BlockEvent`).

### 4.4 Export

CSV, Excel (XLSX) et PDF (rapport de match). Export JSON brut des événements
pour permettre un recalcul ultérieur des statistiques (voir principe en
section 6).

## 5. Contraintes

### 5.1 Matérielles

- **CPU uniquement** pour l'inférence IA dans un premier temps (pas de GPU
  garanti côté club). Conséquence directe : le traitement se fait **par
  lots, après le match** (latence de quelques minutes à quelques heures
  acceptée), pas en flux temps réel.
- Stockage **local** (disque du club ou d'un bénévole) pour le MVP, pas
  d'infrastructure cloud payante.
- Volume attendu : 1 à 3 matchs par semaine pour une seule équipe au départ.

### 5.2 Fonctionnelles

- Identification des joueurs **partielle et non fiable à 100 %** : les
  numéros de maillot ne sont pas toujours lisibles à l'écran. **L'interface
  de correction humaine (association track → joueur) est une fonctionnalité
  cœur du MVP**, pas une option différée.
- Un seul utilisateur/administrateur pour le MVP, mais le modèle de données
  doit intégrer dès le départ une notion d'utilisateur et de rôle, même non
  exploitée immédiatement, pour permettre plus tard la correction
  collaborative par plusieurs bénévoles.

### 5.3 Vie privée / RGPD

Le club suit aujourd'hui une équipe au niveau départemental, mais gère aussi
des catégories jeunes. Par défaut, et tant que la question n'est pas tranchée
avec le club :

- prévoir un champ de consentement à l'image (par joueur/match) dans le
  modèle de données ;
- prévoir une durée de rétention vidéo configurable (pas de conservation
  illimitée par défaut) ;
- prévoir la possibilité technique (future, pas nécessairement implémentée en
  MVP) de flouter les visages à l'export/partage.

Ce point n'est pas bloquant pour le MVP (l'équipe actuellement suivie est
prioritaire) mais doit être présent dans le schéma de données dès `M0`/`M12`
pour éviter une migration douloureuse plus tard.

## 6. Principe directeur : séparer vision et statistiques

Les statistiques ne sont jamais calculées directement dans le code de vision.
Le pipeline vision produit des `Event` bruts ; un moteur statistique
indépendant les consomme pour produire les box-scores. Cela permet d'améliorer
la détection sans toucher au calcul des stats, et de **recalculer** les
statistiques si la définition d'un stat change ou si un événement est corrigé
a posteriori. Les événements bruts sont donc toujours conservés, jamais
seulement le résultat agrégé.

## 7. Hors périmètre du MVP (explicitement exclu, traité en phases ultérieures)

- Mode live / quasi temps réel (M16).
- Multi-caméra, caméra mobile avec suivi automatique.
- Détection et tracking du ballon fiables (M7 — module séparé, reconnu comme
  le plus difficile du pipeline).
- Identification automatique fiable des joueurs sans intervention humaine.
- Gestion multi-utilisateurs concurrente (prévue dans le modèle de données,
  non exploitée en MVP).
- Lecture OCR automatique du tableau d'affichage.

## 8. Utilisateurs cibles

Un seul profil pour le MVP : un bénévole/administrateur du club qui importe la
vidéo, lance le traitement, corrige les événements proposés via l'interface de
validation, et exporte le rapport de match. Pas de notion de spectateur ou de
consultation publique dans le MVP.

## 9. Glossaire rapide

- **Track** : trajectoire d'une détection suivie dans le temps, avant toute
  identification (ex. "Track #17").
- **Player** : identité réelle d'un joueur (numéro de licence, nom, numéro de
  maillot), associée à un ou plusieurs tracks après correction humaine.
- **Possession** : intervalle de temps pendant lequel une équipe contrôle le
  ballon, de la récupération à la perte/au tir/à la fin de période.
- **Event** : tout fait de jeu horodaté et typé (tir, rebond, faute,
  interception, etc.).
