# Benchmarks — Détection (M3) et Tracking (M4)

## Matériel de mesure

⚠️ Ces mesures ont été faites sur la machine du sandbox de développement
(cloud), **pas sur le matériel réel du club**. Elles donnent un ordre de
grandeur, à reconfirmer sur la machine qui exécutera réellement
l'application (M15 — Performance optimization).

- CPU : Intel Xeon @ 2.80GHz, 4 cœurs
- RAM : 15 Go
- Pas de GPU (conforme à la contrainte CPU-only du projet)

## Modèle et méthode

- Modèle : YOLOv8n (`ultralytics`, variante "nano", classe COCO `person`
  uniquement)
- Script : `backend/scripts/benchmark_detection.py`
- Méthode : 30 frames échantillonnées sur une vidéo de test, une frame de
  warmup exclue de la mesure, mesure du temps total de `detect()` sur les 30
  frames restantes

## Résultats

| Résolution source | FPS de détection (CPU) |
|---|---|
| 1280×720 | ~20,5 FPS |
| 640×360 | ~16,5 FPS |

YOLO redimensionne en interne les images à sa résolution d'inférence
(640px par défaut), ce qui explique que le FPS ne varie pas
proportionnellement à la résolution source.

## Ce que ça implique pour le pipeline

Le projet est explicitement **CPU-only et par lots** (pas de live en MVP,
voir `docs/architecture.md` §3). À ~18 FPS de traitement en moyenne :

- Un match de 40 minutes filmé à 25 fps représente environ 60 000 frames.
- Si on traite **une frame sur deux** pour le tracking/détection (suffisant
  pour suivre des joueurs qui ne se déplacent pas à une vitesse extrême
  d'une frame à l'autre), cela représente ~30 000 frames à traiter, soit de
  l'ordre de **25 à 30 minutes de traitement** pour la détection seule.
- Les étapes suivantes (tracking, calibration terrain, event engine)
  ajouteront un coût supplémentaire, mesuré à leurs milestones respectifs.
- Un objectif raisonnable pour le MVP est donc de l'ordre de **grandeur
  d'une heure de traitement pour un match**, pas plusieurs heures — à
  confirmer précisément en M15 une fois le pipeline complet assemblé.

## Validation qualitative (détection réelle)

Au-delà du FPS, la détection a été vérifiée sur une vraie photo contenant
des personnes (image de démonstration publique d'Ultralytics, non
committée dans le repo) : **2 personnes détectées, confiance 0.84 et
0.82**, bounding boxes cohérentes. Cette vérification manuelle complète les
tests automatisés (`backend/tests/test_yolo_detector.py`), qui utilisent un
modèle factice pour tester la logique de parsing sans dépendre d'une image
tierce ou du réseau.

## Comment reproduire (détection)

```bash
cd backend
source .venv/bin/activate
python scripts/benchmark_detection.py /chemin/vers/une/vidéo.mp4 --frames 30
```

## Tracking (M4)

### Algorithme retenu

`IoUTracker` (`backend/app/tracking/tracker.py`) : association par
recouvrement de boîtes (IoU) entre frames consécutives via l'algorithme
hongrois (`scipy.optimize.linear_sum_assignment`), **sans filtre de
Kalman** (pas de prédiction de mouvement). Choisi pour rester simple, léger
(une seule dépendance ajoutée : `scipy`), et surtout **entièrement
testable** avec des séquences synthétiques déterministes — voir
`backend/tests/test_tracker.py` (ID stable sur mouvement continu, nouvel ID
après disparition prolongée, deux objets suivis indépendamment, cas de
croisement sans occlusion totale).

Limite assumée : une occlusion complète (une personne totalement masquée
par une autre pendant une ou plusieurs frames) n'est pas garantie de
conserver le bon ID avec cette approche. Si le taux de changement d'ID
s'avère trop élevé sur de vraies vidéos de match (joueurs qui se
chevauchent beaucoup plus qu'au test), le remplacer par un tracker avec
prédiction de mouvement (SORT+Kalman, ByteTrack) est possible sans changer
l'interface `Tracker` ni le code appelant.

### Validation qualitative (pipeline réel)

Vidéo de test : photo réelle de deux personnes (même image que pour M3),
animée par un panoramique simulé (fenêtre de recadrage qui se déplace sur
l'image sur 4 secondes), pour obtenir un vrai mouvement inter-frames avec
de vraies détections YOLO — pas seulement des détections synthétiques.

- Pipeline complet (upload → détection → tracking) exécuté sans crash via
  l'API réelle (`GET /videos/{id}/tracks`).
- Sur un premier test (encodage H.264, vérifié en dehors du navigateur) :
  2 trajectoires obtenues, chacune stable sur toute sa durée de visibilité
  (34 points consécutifs pour la 1ʳᵉ personne, 24 pour la 2ᵉ, **aucun
  changement d'ID observé** au sein de chaque trajectoire). Les deux
  trajectoires se chevauchent brièvement (~0,13s) au moment où la 2ᵉ
  personne entre dans le champ, sans provoquer de confusion d'identité.
- Sur un second test, bout en bout dans le navigateur (encodage VP9, voir
  `docs/architecture.md`/limites de validation M2) : 3 trajectoires
  obtenues au lieu de 2 — une légère différence probablement due aux
  artefacts de compression VP9 qui modifient la confiance de détection
  d'une frame à l'autre. Les trajectoires restent individuellement
  cohérentes (pas de saut erratique visible dans les coordonnées
  affichées), mais ce résultat **confirme que le taux de changement d'ID
  dépend aussi de la qualité/stabilité de la détection en amont**, pas
  uniquement du tracker — à garder en tête en M9 (Event Engine) et à
  mesurer précisément sur de vraies vidéos de match dès qu'elles seront
  disponibles.

### Ce qui n'a pas été testé

Le cas difficile (occlusion totale entre deux joueurs, typique d'un match
de basket réel — contacts, écrans, duels) n'a pas pu être testé avec les
images disponibles. C'est le scénario le plus susceptible de provoquer des
changements d'ID avec `IoUTracker` ; à surveiller en priorité une fois de
vraies vidéos de match disponibles.

### Comment reproduire (tracking)

```bash
curl -X POST http://localhost:8000/videos -F "file=@video.mp4"
# récupérer l'"id" retourné, puis :
curl "http://localhost:8000/videos/<id>/tracks?confidence=0.5&sample_every_n_frames=2"
```
