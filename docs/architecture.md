# Architecture — basket-analytics

## 1. Vue d'ensemble du pipeline

```
Vidéo → Vision → Tracking → Terrain → Événements → Statistiques → Interface/Export
```

```
                    ┌─────────────────┐
                    │  Video source    │
                    │  MP4 (caméra     │
                    │  fixe)           │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Video Engine     │
                    │ decode / buffer  │
                    │ timestamps       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Detection        │
                    │ joueurs/arbitres │
                    │ (CPU, par lots)  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Tracking         │
                    │ track IDs        │
                    │ trajectoires     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Court Engine     │
                    │ calibration      │
                    │ homographie      │
                    │ coord. terrain   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Event Engine     │
                    │ tirs/rebonds/    │
                    │ fautes/passes    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Statistics       │
                    │ Engine           │
                    │ (indépendant de  │
                    │  la vision)      │
                    └────────┬─────────┘
                             │
             ┌───────────────┴────────────────┐
             ▼                                 ▼
      ┌─────────────┐                  ┌──────────────┐
      │ UI de        │                  │ Export        │
      │ validation / │                  │ CSV/XLSX/PDF  │
      │ dashboard    │                  │               │
      └─────────────┘                  └──────────────┘
```

À chaque flèche correspond une frontière de module testable indépendamment :
on doit pouvoir rejouer n'importe quelle étape à partir de la sortie de la
précédente, sans ré-exécuter tout le pipeline (important vu la contrainte
CPU : le traitement vision est lent, on ne veut pas le relancer juste pour
corriger un événement).

## 2. Séparation backend / frontend

Choix retenu (vs. une app monolithique Streamlit) : **backend FastAPI +
frontend web séparé**, pour permettre une UI de correction réactive (lecteur
vidéo avec overlay, édition frame-par-frame) difficile à obtenir avec un
framework orienté scripts comme Streamlit, et pour préparer naturellement
l'évolution vers plusieurs utilisateurs/rôles.

```
┌──────────────────┐        REST/JSON        ┌──────────────────┐
│   Frontend web    │ ──────────────────────> │  Backend FastAPI  │
│  React + TS + Vite│ <────────────────────── │                   │
└──────────────────┘                          └─────────┬─────────┘
                                                          │
                                               ┌──────────┴──────────┐
                                               │                     │
                                        ┌──────▼──────┐     ┌────────▼────────┐
                                        │   SQLite     │     │  Pipeline vision │
                                        │ (événements, │     │  (jobs par lots, │
                                        │  stats, etc.)│     │   CPU)           │
                                        └──────────────┘     └─────────────────┘
```

- **Frontend** : React + TypeScript + Vite. Choisi par défaut (aucune
  préférence exprimée) pour la maturité de l'écosystème, la quantité de
  documentation/exemples disponibles (important pour un développement
  largement autonome par Claude Code), et l'adéquation avec une UI
  interactive (lecteur vidéo, overlay, formulaires de correction,
  dashboards).
- **Backend** : FastAPI (Python), cohérent avec l'écosystème vision/IA
  (OpenCV, modèles de détection, etc. sont en Python).
- **Traitement vision** : exécuté comme des jobs asynchrones (pas dans la
  requête HTTP qui déclenche l'analyse) — un job peut prendre plusieurs
  minutes sur CPU. Le MVP peut se contenter d'un traitement en arrière-plan
  simple (ex. tâche de fond FastAPI / process séparé) ; une vraie file de
  jobs (Celery, RQ...) n'est à introduire que si le besoin se confirme
  (plusieurs matchs à traiter simultanément).

## 3. Pourquoi CPU-only change la conception

Contrairement à un pipeline pensé pour du temps réel, ici :

- le traitement est **par lots** : on importe une vidéo complète, on lance
  une analyse, on récupère un résultat plus tard (notification/statut de
  job) ;
- les modèles de détection doivent être choisis pour leur rapport
  vitesse/précision sur CPU (ex. variantes "nano"/"small" plutôt que les
  plus grosses) ;
- le FPS de traitement sera mesuré et documenté dès la Phase 3 (détection) —
  aucune promesse de performance n'est faite avant d'avoir des chiffres
  réels sur du matériel représentatif du club ;
- l'architecture logicielle doit malgré tout rester interchangeable : le
  détecteur, le tracker etc. sont définis par interface, pour pouvoir
  brancher un GPU plus tard (cloud ponctuel, ou matériel acheté par le club)
  sans réécrire le pipeline (seulement reconfigurer).

## 4. Principe de persistance

Toujours conserver les événements bruts (`Event` et sous-types), jamais
seulement les statistiques agrégées. Le moteur statistique est un calcul
dérivé, rejouable à tout moment — voir `data_model.md` section
"Statistics" et `requirements.md` section 6.

## 5. Évolutivité prévue (hors MVP, mais anticipée dans la conception)

- **Multi-utilisateurs/rôles** : le modèle de données inclut `User` et une
  notion de rôle dès le MVP, même si un seul compte existe en pratique.
- **Multi-caméra / caméra mobile** : le `Court Engine` (calibration) est
  pensé comme un module autonome prenant en entrée des coordonnées pixel et
  produisant des coordonnées terrain, pour permettre plus tard une
  calibration par segment (caméra qui bouge) ou une fusion multi-caméra sans
  changer les étapes en aval.
- **Mode live** (M16) : le `Video Engine` est conçu dès le départ avec une
  interface compatible fichier vidéo **et** flux (même si seul le fichier
  est implémenté en MVP), pour ne pas nécessiter de réécriture quand le mode
  live sera abordé.

## 6. Tests et validation

Chaque module du pipeline doit être testable isolément à partir de données
fixtures (ex. un jeu de détections connu pour tester le tracker sans
dépendre du modèle de détection réel). Le détail des types de tests
(unitaires, intégration, non-régression) attendus par phase est précisé dans
`ROADMAP.md` et `CLAUDE.md`.
