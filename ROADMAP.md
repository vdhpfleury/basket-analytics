# ROADMAP — basket-analytics

Référence : `CLAUDE.md` §4 (règle de progression) et `docs/*.md`. Les
milestones sont **séquentiels et bloquants** : ne pas démarrer `M(N+1)` avant
que `M(N)` remplisse ses critères d'acceptation. Chaque tâche atomique est
cochée au fur et à mesure (`- [x]`), pas rétroactivement en bloc.

Décisions structurantes qui conditionnent tout ce qui suit (voir
`docs/requirements.md` et `docs/architecture.md`) :
- traitement **CPU uniquement** → pipeline **par lots**, pas de live avant M16 ;
- **1 caméra fixe**, vue d'ensemble ;
- correction humaine = fonctionnalité **cœur**, pas une option tardive ;
- stack : FastAPI (backend) + React/TS/Vite (frontend) + SQLite.

---

## M0 — Project specification

- [x] M0.1 Rédiger `docs/requirements.md`
- [x] M0.2 Rédiger `docs/architecture.md`
- [x] M0.3 Rédiger `docs/data_model.md`
- [x] M0.4 Rédiger `docs/statistics_definition.md`
- [x] M0.5 Rédiger `CLAUDE.md`
- [x] M0.6 Rédiger ce `ROADMAP.md`
- [ ] M0.7 Validation explicite de l'utilisateur sur l'ensemble des documents
      ci-dessus — **checkpoint obligatoire avant de commencer M1**

**Critère d'acceptation** : les 4 documents de `docs/` + `CLAUDE.md` +
`ROADMAP.md` existent, sont cohérents entre eux, et sont approuvés par
l'utilisateur.

---

## M1 — Software architecture (squelette)

- [ ] M1.1 Initialiser `backend/` (pyproject.toml, structure `app/` vide
      conforme à `CLAUDE.md` §3)
- [ ] M1.2 Initialiser `frontend/` (Vite + React + TypeScript)
- [ ] M1.3 `.gitignore` (venv, `__pycache__`, `node_modules`, poids de
      modèles, vidéos)
- [ ] M1.4 Endpoint FastAPI `/health`
- [ ] M1.5 Page frontend minimale qui appelle `/health` et affiche le statut
- [ ] M1.6 `README.md` avec instructions de lancement local (backend +
      frontend)

**Critère d'acceptation** : `uvicorn` démarre, `npm run dev` démarre, le
frontend affiche que le backend répond. Aucune détection, aucune vidéo à ce
stade.

---

## M2 — Video engine

- [ ] M2.1 Interface `VideoEngine` (open / read / seek / fps / timestamp),
      pensée dès le départ pour accepter plus tard un flux en plus d'un
      fichier (cf. `docs/architecture.md` §5), sans être implémentée pour le
      flux en M2
- [ ] M2.2 Implémentation lecture fichier MP4
- [ ] M2.3 Endpoint upload vidéo + extraction des métadonnées (durée, fps,
      résolution)
- [ ] M2.4 Extraction de frame à la demande par timestamp, exposée via l'API
- [ ] M2.5 Lecteur vidéo frontend basique (play / pause / seek)
- [ ] M2.6 Tests unitaires (ouverture, lecture séquentielle, seek, format
      non supporté)

**Critère d'acceptation** : une vidéo MP4 uploadée est lisible dans le
frontend (play/pause/seek) avec ses métadonnées affichées, sans aucune
détection.

---

## M3 — Player detection

- [ ] M3.1 Choisir et intégrer un framework de détection (modèle
      nano/small, adapté CPU)
- [ ] M3.2 Interface `Detector` découplée de l'implémentation choisie
- [ ] M3.3 Détecteur par défaut configurable (modèle, seuil de confiance)
- [ ] M3.4 Endpoint API : détection sur une frame ou un intervalle →
      bounding boxes
- [ ] M3.5 Visualisation frontend des bounding boxes
- [ ] M3.6 Mesure et log du FPS de traitement CPU
- [ ] M3.7 Tests unitaires (interface, seuils, cas sans détection)
- [ ] M3.8 Documenter les résultats de benchmark (nouveau
      `docs/benchmarks.md`)

**Critère d'acceptation** : détection stable sans crash sur le jeu de test
(clips YouTube), FPS mesuré et documenté, seuil de confiance configurable
démontré.

---

## M4 — Tracking

- [ ] M4.1 Implémenter `TrackPoint`/`Track` (cf. `docs/data_model.md`)
- [ ] M4.2 Intégrer un algorithme de tracking compatible CPU (ex. ByteTrack/SORT)
- [ ] M4.3 Pipeline détection → tracking sur une séquence, persistance des
      `TrackPoint`
- [ ] M4.4 Visualisation frontend des trajectoires
- [ ] M4.5 Tests unitaires + test d'intégration sur fixture mesurant la
      stabilité des IDs

**Critère d'acceptation** : sur un extrait test, un joueur qui traverse le
terrain conserve son ID la majorité du temps ; le taux de changement d'ID
est mesuré et documenté (pas de seuil arbitraire imposé avant d'avoir des
chiffres réels).

---

## M5 — Player identification (+ correction humaine, cœur du produit)

- [ ] M5.1 Implémenter `PlayerIdentification` en DB
- [ ] M5.2 Interface de correction manuelle : liste des tracks avec
      sélection du joueur réel (menu déroulant), par match
- [ ] M5.3 Heuristique couleur de maillot pour pré-grouper les tracks par
      équipe (aide à la correction — **pas** une identification automatique
      fiable, à documenter comme telle)
- [ ] M5.4 Sauvegarde des associations avec traçabilité (`method`,
      `manually_verified`, `verified_by`)
- [ ] M5.5 Tests : persistance correcte, un track non identifié reste
      explicitement "inconnu" (jamais assigné par défaut à un joueur)

**Critère d'acceptation** : pour un match donné, l'utilisateur peut associer
chaque track significatif à un joueur de l'effectif via l'UI, et cette
association est utilisée par la suite du pipeline.

---

## M6 — Court calibration

- [ ] M6.1 Interface de calibration manuelle (points image ↔ points terrain
      connus) sur une frame fixe
- [ ] M6.2 Calcul de l'homographie à partir des points sélectionnés
- [ ] M6.3 Sauvegarde de `CourtCalibration` par match
- [ ] M6.4 Fonction réutilisable pixel → coordonnées terrain (utilisée en
      M7/M8)
- [ ] M6.5 Visualisation terrain 2D avec projection des tracks (validation
      visuelle)
- [ ] M6.6 Tests unitaires sur l'homographie (points de contrôle connus →
      coordonnées attendues)

**Critère d'acceptation** : sur une vidéo du jeu de test, la calibration
manuelle produit une projection terrain visuellement cohérente (joueurs dans
les limites du terrain affiché).

---

## M7 — Ball detection/tracking (module isolé, le plus incertain)

- [ ] M7.1 Interface du module, indépendante du reste (entrée : frames,
      sortie : position ballon + confiance)
- [ ] M7.2 Implémentation détection ballon
- [ ] M7.3 Tracking ballon basique (trajectoire pouvant comporter des trous
      — assumé dès la conception)
- [ ] M7.4 Heuristique de possession candidate (joueur le plus proche du
      ballon, fenêtre spatio-temporelle)
- [ ] M7.5 Tests unitaires + documentation explicite des limites connues de
      ce module

**Critère d'acceptation** : le module tourne sans crash sur le jeu de test
et produit une estimation de possession candidate. Critère volontairement
qualitatif à ce stade — aucun seuil de précision chiffré n'est imposé avant
retour d'usage réel.

---

## M8 — Event detection

- [ ] M8.1 Structure de base de l'Event Engine (tracks + ballon +
      calibration → `Event`)
- [ ] M8.2 Niveau 1 : début/fin de possession, tir, panier, lancer franc
- [ ] M8.3 Niveau 2 : rebond, perte de balle, faute
- [ ] M8.4 Niveau 3 : passe, interception, contre
- [ ] M8.5 Interface de saisie manuelle d'un événement (ajout, nécessaire
      dès ce stade vu les limites de M7)
- [ ] M8.6 Tests unitaires par type d'événement (fixtures) + tests
      d'intégration sur le jeu de test

**Critère d'acceptation** : sur le match de test, une liste d'événements
plausibles de niveau 1 est produite (taux d'erreur documenté, corrigible
ensuite en M10). Les niveaux 2/3 peuvent être partiels — documenter
précisément ce qui est fiable vs. à compléter manuellement.

---

## M9 — Statistics engine

- [ ] M9.1 Implémentation conforme à `docs/statistics_definition.md`,
      strictement découplée du pipeline vision (entrée = `Event`, jamais des
      frames)
- [ ] M9.2 Calcul `TeamStatistics`
- [ ] M9.3 Calcul `PlayerStatistics`
- [ ] M9.4 Endpoint API box-score (équipe + joueurs) pour un match
- [ ] M9.5 Mécanisme de recalcul complet à partir des événements (pas
      seulement un cache figé)
- [ ] M9.6 Tests unitaires exhaustifs — un test par formule de
      `docs/statistics_definition.md`

**Critère d'acceptation** : à partir d'un jeu d'`Event` fixtures connu, le
box-score produit correspond exactement aux valeurs calculées à la main.

---

## M10 — Human validation UI

- [ ] M10.1 Vue chronologique des événements, synchronisée avec le lecteur
      vidéo
- [ ] M10.2 Actions Confirmer / Rejeter / Éditer sur un événement (joueur,
      type, position, timestamp)
- [ ] M10.3 Ajout manuel d'un événement absent
- [ ] M10.4 Suppression d'un événement
- [ ] M10.5 Recalcul automatique des statistiques après correction (branché
      sur M9.5)
- [ ] M10.6 Tests d'intégration : une correction se répercute correctement
      sur le box-score

**Critère d'acceptation** : un utilisateur peut parcourir un match entier,
valider/corriger les événements, et voir les statistiques se mettre à jour,
sans manipulation technique.

---

## M11 — Match dashboard

- [ ] M11.1 Fiche match : score, box-score équipe et joueurs
- [ ] M11.2 Shot chart (tirs réussis/ratés positionnés sur le terrain 2D)
- [ ] M11.3 Heatmap de présence (optionnelle — reporter explicitement si le
      temps manque, ne pas la bâcler)
- [ ] M11.4 Indicateur de fiabilité du match (provisoire / validé — cf.
      `docs/statistics_definition.md` §3)
- [ ] M11.5 Tests frontend de base (rendu correct sur données fixture)

**Critère d'acceptation** : la fiche d'un match validé est lisible et
correcte pour un non-développeur du club.

---

## M12 — Database / persistence

- [ ] M12.1 Schéma SQLAlchemy conforme à `docs/data_model.md`
- [ ] M12.2 Migrations (Alembic ou équivalent léger)
- [ ] M12.3 Intégration SQLite (remplace tout stockage temporaire de
      prototypage utilisé en M2-M11)
- [ ] M12.4 Script de sauvegarde/restauration de la base
- [ ] M12.5 Vérification des champs RGPD (`consent_image`,
      `retention_until`) effectivement présents et exploitables
- [ ] M12.6 Tests d'intégration DB (CRUD sur chaque entité principale)

**Critère d'acceptation** : toutes les données produites par M2-M11 sont
persistées durablement (redémarrage de l'application sans perte de données).

---

## M13 — Export

- [ ] M13.1 Export CSV des événements bruts
- [ ] M13.2 Export Excel (box-score équipe + joueurs)
- [ ] M13.3 Export PDF (rapport de match)
- [ ] M13.4 Export JSON complet (événements + stats, pour recalcul externe)
- [ ] M13.5 Endpoint unifié `export_match(match_id, format)`
- [ ] M13.6 Tests : fichiers générés valides et ouvrables (vérification de
      structure)

**Critère d'acceptation** : pour un match validé, les 4 formats sont
générables depuis l'interface en un clic chacun.

---

## M14 — Testing (consolidation)

- [ ] M14.1 Constituer un jeu de 2-3 vidéos de référence courtes (clips
      YouTube), référencées sans forcément être commitées (poids/taille —
      cf. `.gitignore`)
- [ ] M14.2 Suite de non-régression comparant les sorties du pipeline sur ce
      jeu de référence entre deux versions
- [ ] M14.3 Revue globale de la couverture de tests (backend + frontend),
      combler les trous identifiés
- [ ] M14.4 Documenter la procédure de test pour un futur contributeur

**Critère d'acceptation** : la suite de tests passe intégralement et de
façon reproductible ; une régression significative du pipeline vision sur le
jeu de référence est détectable.

---

## M15 — Performance optimization

- [ ] M15.1 Mesurer : FPS vidéo, FPS détection, FPS tracking, latence totale
      par match, RAM/CPU
- [ ] M15.2 Identifier le goulot d'étranglement principal (mesuré, pas
      supposé)
- [ ] M15.3 Optimisations ciblées selon les mesures réelles (taille de
      modèle, résolution réduite, traitement par lots)
- [ ] M15.4 Documenter les temps de traitement obtenus par type de match

**Critère d'acceptation** : un objectif de latence de traitement par match
est documenté et atteint sur le matériel réel du club (objectif cohérent
avec la contrainte CPU-only, pas un objectif temps réel).

---

## M16 — Live mode (hors périmètre MVP)

À n'aborder qu'après validation explicite de M0 à M15.

- [ ] M16.1 Étude de faisabilité sur le matériel CPU réellement disponible
      à ce stade (conclure "non réalisable sans GPU" est un résultat valide,
      pas un échec)
- [ ] M16.2 Si viable : adapter le Video Engine à un flux (webcam/RTSP) en
      plus du fichier
- [ ] M16.3 Si viable : pipeline à latence contrôlée (buffer + traitement
      asynchrone, quelques secondes de retard acceptées)

**Critère d'acceptation** : une décision go/no-go documentée et chiffrée,
avant toute implémentation.

---

## M17 — Packaging / déploiement

- [ ] M17.1 Script d'installation (dépendances, téléchargement des poids de
      modèles)
- [ ] M17.2 Vérification d'environnement au démarrage (CPU, espace disque,
      versions Python/Node)
- [ ] M17.3 Initialisation de la base de données au premier lancement
- [ ] M17.4 Documentation d'installation pour un bénévole non développeur
- [ ] M17.5 Configuration du dossier de stockage vidéo et de la politique de
      rétention (RGPD)

**Critère d'acceptation** : un bénévole du club, non développeur, peut
installer et lancer l'application en suivant uniquement la documentation.

---

## Suivi

Ce document est mis à jour au fil de l'eau (cases cochées, écarts notés),
pas rétroactivement. Un milestone n'est marqué fait que lorsque son critère
d'acceptation est vérifié, pas lorsque le code est simplement écrit.
