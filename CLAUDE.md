# CLAUDE.md — basket-analytics

Ce fichier est la référence de travail pour quiconque (humain ou Claude Code)
développe sur ce dépôt. Il complète les documents de `docs/` :

- `docs/requirements.md` — cahier des charges (quoi et pourquoi)
- `docs/architecture.md` — architecture technique (comment, globalement)
- `docs/data_model.md` — modèle de données
- `docs/statistics_definition.md` — définitions exactes des statistiques
- `ROADMAP.md` — découpage en milestones et tâches atomiques (quand, dans
  quel ordre)

**Lire `docs/requirements.md` et `docs/architecture.md` avant toute
implémentation.** Ce `CLAUDE.md` ne répète pas leur contenu, il donne les
règles de travail.

## 1. Résumé du projet

Application qui analyse la vidéo d'un match de basket amateur (une caméra
fixe, vue d'ensemble) pour produire des statistiques d'équipe et
individuelles, avec validation humaine systématique. Contrainte structurante :
**traitement CPU uniquement**, donc pipeline par lots (pas de live en MVP).

Pipeline : `Vidéo → Vision → Tracking → Terrain → Événements → Statistiques
→ Interface/Export` (détail dans `docs/architecture.md`).

## 2. Stack technique retenue

- **Backend** : Python, FastAPI.
- **Frontend** : React + TypeScript + Vite.
- **Base de données** : SQLite pour le MVP.
- **Vision/IA** : OpenCV + modèles de détection légers adaptés CPU (à
  benchmarker en M3, pas de choix figé avant d'avoir des mesures réelles).
- **Traitement vision** : jobs asynchrones en arrière-plan, pas dans le
  cycle requête/réponse HTTP.

Ne pas dévier de cette stack sans in discuter explicitement avec
l'utilisateur — un changement de stack est une décision produit, pas une
décision d'implémentation.

## 3. Structure de dossiers cible

```
basket-analytics/
├── backend/
│   ├── app/
│   │   ├── api/            # routes FastAPI
│   │   ├── video/          # video engine (lecture, buffer, timestamps)
│   │   ├── detection/      # détection joueurs/arbitres
│   │   ├── tracking/       # suivi des tracks
│   │   ├── court/          # calibration terrain / homographie
│   │   ├── events/         # event engine
│   │   ├── statistics/     # statistics engine (indépendant de la vision)
│   │   ├── storage/        # modèles DB / repositories
│   │   └── export/         # export CSV/XLSX/PDF
│   ├── models/              # poids de modèles IA (gitignored)
│   ├── tests/
│   ├── scripts/
│   ├── configs/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/
│   ├── package.json
│   └── vite.config.ts
├── docs/
├── CLAUDE.md
├── ROADMAP.md
└── README.md
```

Cette structure est créée progressivement, milestone par milestone (voir
`ROADMAP.md` — M1 crée le squelette, pas ce document). Ne pas créer de
dossiers vides "au cas où" avant qu'un milestone ne les nécessite.

## 4. Règle de progression : ne jamais sauter une étape

Les milestones (`ROADMAP.md`, M0 → M17) sont **séquentiels et bloquants**.
Règles non négociables :

1. Un milestone n'est considéré terminé que lorsque ses critères
   d'acceptation sont remplis et vérifiables (tests qui passent, démo
   manuelle possible quand c'est pertinent).
2. Ne jamais commencer l'implémentation d'un milestone `N+1` avant que `N`
   soit validé — y compris si une optimisation ou une fonctionnalité du
   futur semble "facile à faire tant qu'on y est".
3. En cas de doute sur la complétude d'un milestone, le signaler
   explicitement plutôt que de supposer que c'est bon et d'avancer.
4. Toujours garder la séparation vision / statistiques (voir
   `docs/architecture.md` §4) — un correctif de détection ne doit jamais
   nécessiter de modifier le Statistics Engine, et inversement.

## 5. Conventions de code

- Python : `black` + `ruff` pour le formatage/lint, typage (`mypy` ou a
  minima type hints cohérents), docstrings courtes uniquement quand le
  "pourquoi" n'est pas évident par le nom des fonctions.
- TypeScript/React : ESLint + Prettier, composants fonctionnels, pas de
  logique métier dans les composants d'affichage (séparer
  appels API / état / présentation).
- Pas de commentaire qui répète ce que le code dit déjà. Un commentaire est
  justifié par une contrainte cachée, un contournement, ou une subtilité qui
  surprendrait un relecteur.
- Pas d'abstraction anticipée pour des besoins hypothétiques (ex. ne pas
  construire un système de plugins pour les détecteurs tant qu'un seul
  détecteur n'a pas été implémenté et validé).

## 6. Tests obligatoires (voir aussi `ROADMAP.md` par milestone)

- **Tests unitaires** : obligatoires dès qu'un module a une logique non
  triviale (Statistics Engine particulièrement — chaque formule de
  `docs/statistics_definition.md` doit avoir son test).
- **Tests d'intégration** : pour chaque jonction du pipeline (ex.
  détection → tracking, event → statistics).
- **Tests de non-régression** : dès qu'un jeu de vidéos de référence existe
  (M14), toute modification du pipeline vision doit être comparée aux
  résultats précédents sur ce jeu de référence.
- Écrire les tests **pendant** le développement de chaque milestone, pas
  après coup en fin de projet.

## 7. Stratégie Git

- Une branche par milestone ou par tâche atomique significative (voir
  `ROADMAP.md`), jamais de développement direct sur `main`.
- Commits petits et descriptifs, qui correspondent chacun à une tâche
  atomique de la roadmap quand c'est possible.
- Ne pas committer : poids de modèles téléchargés, vidéos de test, fichiers
  `__pycache__`/`node_modules` — un `.gitignore` est mis en place dès M1.
- Ne pas committer de vidéos contenant des personnes réelles tant que la
  question RGPD (`docs/requirements.md` §5.3) n'a pas été tranchée avec le
  club — utiliser exclusivement des extraits publics (YouTube) ou des
  fixtures synthétiques pour les tests automatisés versionnés.

## 8. Rôle de Claude Code sur ce projet

Le développement est très majoritairement autonome (décision explicite de
l'utilisateur). En conséquence :

- Chaque tâche terminée doit être **vérifiable sans relire tout le code** :
  un test qui passe, un script de démo, une sortie claire.
- En cas d'ambiguïté sur une décision produit (pas uniquement technique),
  poser la question plutôt que de choisir par défaut silencieusement —
  notamment pour tout ce qui touche à la vie privée (RGPD), aux formules de
  statistiques, ou à un changement de stack.
- Mettre à jour `ROADMAP.md` (cocher les tâches, noter les écarts) au fur et
  à mesure, pas uniquement en fin de milestone.
