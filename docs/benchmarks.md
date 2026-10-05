# Benchmarks — Détection (M3)

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

## Comment reproduire

```bash
cd backend
source .venv/bin/activate
python scripts/benchmark_detection.py /chemin/vers/une/vidéo.mp4 --frames 30
```
