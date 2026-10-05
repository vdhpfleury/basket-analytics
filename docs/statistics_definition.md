# Définition des statistiques — basket-analytics

Toutes les statistiques ci-dessous sont **calculées par le Statistics Engine
à partir des `Event` et `Possession`** (voir `data_model.md`), jamais
produites directement par le pipeline de vision. Convention : règles FIBA
standard (4 périodes, tir à 2 ou 3 points, lancers francs) ; le modèle de
données permet d'adapter la durée des périodes par catégorie (jeunes) sans
changer ces définitions.

## 1. Statistiques d'équipe (`TeamStatistics`)

| Statistique | Définition / formule |
|---|---|
| Score | Somme des points de tous les `ShotEvent` réussis de l'équipe (2 ou 3 pts) + `FTEvent`/`ShotEvent(type=FT)` réussis (1 pt) |
| Possessions | Nombre de `Possession` de l'équipe sur le match |
| Pace | Possessions ramenées à une durée standard (ex. pour 40 minutes), pour comparer des matchs de durée différente |
| FG tentés / réussis (FGA/FGM) | Nombre de `ShotEvent` (type `2PT` ou `3PT`) / dont `made = true` |
| 2PT tentés / réussis | `ShotEvent` filtrés sur `shot_type = 2PT` |
| 3PT tentés / réussis | `ShotEvent` filtrés sur `shot_type = 3PT` |
| FT tentés / réussis | `ShotEvent` filtrés sur `shot_type = FT` |
| Rebonds offensifs / défensifs | Compte des `ReboundEvent` par `rebound_type`, attribués à l'équipe du joueur |
| Passes décisives (assists) | Compte des `PassEvent` où `is_assist = true` |
| Interceptions (steals) | Compte des `StealEvent` |
| Contres (blocks) | Compte des `BlockEvent` |
| Pertes de balle (turnovers) | Compte des `TurnoverEvent` |
| Fautes | Compte des `FoulEvent` |

## 2. Statistiques individuelles (`PlayerStatistics`)

| Statistique | Définition / formule |
|---|---|
| Minutes jouées | Calculées à partir des intervalles de présence du joueur (déduits des tracks identifiés + substitutions si suivies) ; **à préciser en détail lors de la conception du Event Engine (M8)**, car cela suppose de détecter les entrées/sorties de joueurs — non garanti fiable en tout début de projet, peut rester approximatif ou saisi manuellement au départ |
| Points (PTS) | 2×(2PM) + 3×(3PM) + 1×(FTM) |
| FGM / FGA | Mêmes définitions qu'au niveau équipe, filtrées sur le joueur |
| 2PM / 2PA, 3PM / 3PA, FTM / FTA | Idem, filtrés par `shot_type` |
| Rebonds offensifs / défensifs | `ReboundEvent` du joueur, par type |
| Passes décisives | `PassEvent` du joueur où `is_assist = true` |
| Interceptions | `StealEvent` du joueur |
| Contres | `BlockEvent` du joueur |
| Pertes de balle | `TurnoverEvent` du joueur |
| Fautes | `FoulEvent` du joueur |

## 3. Remarques sur la fiabilité attendue en MVP

- Tant que l'étape de correction humaine (Phase 10) n'a pas été appliquée à
  un match, les statistiques affichées doivent être marquées comme
  **provisoires** (basées sur `source = auto`, `manually_verified = false`).
- Une fois les événements validés par un bénévole, les statistiques
  deviennent **définitives** pour ce match, mais restent recalculables si un
  événement est corrigé ultérieurement (voir principe de recalcul,
  `architecture.md` §4).
- Le calcul des minutes jouées par joueur est identifié comme le point le
  plus incertain du MVP (dépend de l'identification fiable des tracks) : il
  ne doit pas bloquer la sortie des autres statistiques si les données sont
  incomplètes (affichage "non disponible" plutôt qu'une valeur fausse).

## 4. Tests obligatoires (voir aussi `CLAUDE.md` et `ROADMAP.md`)

Chaque formule ci-dessus doit avoir un test unitaire dédié dans le Statistics
Engine, indépendant de tout pipeline vision, construit à partir d'`Event`
fixtures. Exemples minimaux attendus :

- un tir à 3 points réussi → +3 au score de l'équipe et au score du joueur ;
- un lancer franc raté → FTA +1, FTM inchangé, pas de point ;
- un rebond offensif → comptabilisé pour le bon joueur et la bonne équipe ;
- une passe suivie d'un panier dans la fenêtre temporelle attendue → marquée
  `is_assist = true` (règle de fenêtre à définir précisément en M8/M9, ex.
  quelques secondes entre la passe et le tir réussi).
