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

- [x] M1.1 Initialiser `backend/` (pyproject.toml, structure `app/` vide
      conforme à `CLAUDE.md` §3)
- [x] M1.2 Initialiser `frontend/` (Vite + React + TypeScript)
- [x] M1.3 `.gitignore` (venv, `__pycache__`, `node_modules`, poids de
      modèles, vidéos)
- [x] M1.4 Endpoint FastAPI `/health`
- [x] M1.5 Page frontend minimale qui appelle `/health` et affiche le statut
- [x] M1.6 `README.md` avec instructions de lancement local (backend +
      frontend)

**Critère d'acceptation** : `uvicorn` démarre, `npm run dev` démarre, le
frontend affiche que le backend répond. Aucune détection, aucune vidéo à ce
stade.

---

## M2 — Video engine

- [x] M2.1 Interface `VideoEngine` (open / read / seek / fps / timestamp),
      pensée dès le départ pour accepter plus tard un flux en plus d'un
      fichier (cf. `docs/architecture.md` §5), sans être implémentée pour le
      flux en M2
- [x] M2.2 Implémentation lecture fichier MP4
- [x] M2.3 Endpoint upload vidéo + extraction des métadonnées (durée, fps,
      résolution)
- [x] M2.4 Extraction de frame à la demande par timestamp, exposée via l'API
- [x] M2.5 Lecteur vidéo frontend basique (play / pause / seek)
- [x] M2.6 Tests unitaires (ouverture, lecture séquentielle, seek, format
      non supporté)

**Critère d'acceptation** : une vidéo MP4 uploadée est lisible dans le
frontend (play/pause/seek) avec ses métadonnées affichées, sans aucune
détection.

**Validation effectuée** : 11 tests backend (video engine + API) verts ;
vérification de bout en bout via navigateur headless (upload, métadonnées
affichées, lecture/pause, seek fonctionnel). **Limite connue de
l'environnement de validation** : le Chromium headless de ce sandbox n'a pas
le codec H.264 (open-source, sans codec propriétaire) — la vérification
navigateur a donc été faite avec un flux vidéo en VP9, et la lecture H.264
côté backend (OpenCV) a été vérifiée séparément. Les navigateurs réels
(Chrome, Edge, Firefox, Safari) supportent nativement le H.264 des vidéos de
téléphone/caméra — à reconfirmer avec un navigateur normal dès que possible.

---

## M3 — Player detection

- [x] M3.1 Choisir et intégrer un framework de détection (modèle
      nano/small, adapté CPU)
- [x] M3.2 Interface `Detector` découplée de l'implémentation choisie
- [x] M3.3 Détecteur par défaut configurable (modèle, seuil de confiance)
- [x] M3.4 Endpoint API : détection sur une frame ou un intervalle →
      bounding boxes
- [x] M3.5 Visualisation frontend des bounding boxes
- [x] M3.6 Mesure et log du FPS de traitement CPU
- [x] M3.7 Tests unitaires (interface, seuils, cas sans détection)
- [x] M3.8 Documenter les résultats de benchmark (nouveau
      `docs/benchmarks.md`)

**Critère d'acceptation** : détection stable sans crash sur le jeu de test
(clips YouTube), FPS mesuré et documenté, seuil de confiance configurable
démontré.

**Validation effectuée** : framework retenu = YOLOv8n (Ultralytics), classe
COCO "person". 20 tests backend verts (parsing/seuillage sur modèle factice
+ intégration modèle réel sans crash sur frame vide). Benchmark CPU :
~16-20 FPS selon résolution (détail dans `docs/benchmarks.md`), avec
estimation du temps de traitement pour un match complet. Validation de bout
en bout en navigateur headless : upload d'une vraie vidéo avec personnes →
2 détections correctement positionnées (confiance ~0.82-0.84) ; relever le
seuil de confiance à 0.9 fait bien disparaître les 2 détections, démontrant
que le seuil est réellement configurable depuis l'UI.

---

## M4 — Tracking

- [x] M4.1 Implémenter `TrackPoint`/`Track` (cf. `docs/data_model.md`)
- [x] M4.2 Intégrer un algorithme de tracking compatible CPU (ex. ByteTrack/SORT)
- [x] M4.3 Pipeline détection → tracking sur une séquence, persistance des
      `TrackPoint`
- [x] M4.4 Visualisation frontend des trajectoires
- [x] M4.5 Tests unitaires + test d'intégration sur fixture mesurant la
      stabilité des IDs

**Critère d'acceptation** : sur un extrait test, un joueur qui traverse le
terrain conserve son ID la majorité du temps ; le taux de changement d'ID
est mesuré et documenté (pas de seuil arbitraire imposé avant d'avoir des
chiffres réels).

**Validation effectuée** : tracker retenu = IoU + algorithme hongrois
("SORT allégé", sans filtre de Kalman — voir `docs/benchmarks.md` pour la
justification et les limites assumées). 15 tests backend supplémentaires
(35 au total) : stabilité d'ID sur mouvement continu, nouvel ID après
disparition prolongée, deux objets suivis indépendamment sans confusion,
cas de croisement sans occlusion totale, pipeline d'intégration avec
détecteur factice. Validation de bout en bout (pipeline réel, vraie vidéo
avec personnes, navigateur headless) : trajectoires correctement affichées
et positionnées ; **aucun changement d'ID observé** au sein des
trajectoires continues sur les deux vidéos de test (détail et limites —
occlusion totale non testée — dans `docs/benchmarks.md`).

---

## M5 — Player identification (+ correction humaine, cœur du produit)

- [x] M5.1 Implémenter `PlayerIdentification` en DB
- [x] M5.2 Interface de correction manuelle : liste des tracks avec
      sélection du joueur réel (menu déroulant), par match
- [x] M5.3 Heuristique couleur de maillot pour pré-grouper les tracks par
      équipe (aide à la correction — **pas** une identification automatique
      fiable, à documenter comme telle)
- [x] M5.4 Sauvegarde des associations avec traçabilité (`method`,
      `manually_verified`, `verified_by`)
- [x] M5.5 Tests : persistance correcte, un track non identifié reste
      explicitement "inconnu" (jamais assigné par défaut à un joueur)

**Critère d'acceptation** : pour un match donné, l'utilisateur peut associer
chaque track significatif à un joueur de l'effectif via l'UI, et cette
association est utilisée par la suite du pipeline.

**Validation effectuée** : `PlayerIdentification` en mémoire (temporaire
avant M12), scoping par vidéo. Heuristique couleur = échantillonnage de la
couleur dominante sur le buste (évite tête/jambes/fond) + regroupement par
k-means (`scipy`, déjà une dépendance) — **aide visuelle seulement**,
jamais utilisée comme identification automatique. 27 tests supplémentaires
(62 au total) : roster, heuristique couleur, store d'identification (track
non identifié = `None` explicite, jamais un joueur par défaut), API
(résumé des tracks, vignette, assigner/retirer, erreurs). Validation de
bout en bout en navigateur : création d'une équipe et de 2 joueurs, lecture
des tracks à identifier (vignette + couleur + menu déroulant), assignation
d'un track à un joueur, **persistance vérifiée après rechargement de la
liste**.

---

## M6 — Court calibration

- [x] M6.1 Interface de calibration manuelle (points image ↔ points terrain
      connus) sur une frame fixe
- [x] M6.2 Calcul de l'homographie à partir des points sélectionnés
- [x] M6.3 Sauvegarde de `CourtCalibration` par match
- [x] M6.4 Fonction réutilisable pixel → coordonnées terrain (utilisée en
      M7/M8)
- [x] M6.5 Visualisation terrain 2D avec projection des tracks (validation
      visuelle)
- [x] M6.6 Tests unitaires sur l'homographie (points de contrôle connus →
      coordonnées attendues)

**Critère d'acceptation** : sur une vidéo du jeu de test, la calibration
manuelle produit une projection terrain visuellement cohérente (joueurs dans
les limites du terrain affiché).

**Validation effectuée** : catalogue de 11 repères identifiables (coins,
ligne médiane, centre, coins de raquette — dimensions FIBA 28×15m),
homographie via `cv2.findHomography` (RANSAC au-delà de 4 points). 19
tests supplémentaires (81 au total), dont un test rigoureux par
transformation perspective connue (calibrage sur 4 points, vérification
sur un 5ᵉ point non utilisé — preuve de généralisation, pas de recopiage).
Validation de bout en bout en navigateur avec une vidéo construite
spécifiquement pour ce test (terrain dessiné aux dimensions exactes +
vraie personne compositée dessus, détectée par YOLO avec confiance 0.94) :
calibration sur les 4 coins → erreur de reprojection 0,00 m, et le joueur
projeté atterrit bien à l'intérieur du rectangle du terrain affiché.

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
