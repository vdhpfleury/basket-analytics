# Modèle de données — basket-analytics

Principe directeur (voir `requirements.md` §6 et `architecture.md` §4) : on
conserve toujours les événements bruts, jamais uniquement les statistiques
agrégées. Les entités ci-dessous sont décrites de façon logique (champs et
relations) ; le choix exact des types SQLite/SQLAlchemy sera précisé à
l'implémentation (M12), ce document est la référence fonctionnelle.

## 1. Entités organisationnelles

### Club
- `id`
- `name`
- `created_at`

### Team
- `id`
- `club_id` (optionnel — une équipe adverse n'appartient pas au club)
- `name`
- `category` (ex. "Seniors", "U15"...) — prévu dès le MVP même si une seule
  catégorie est utilisée au départ

### Player
- `id`
- `team_id`
- `full_name`
- `jersey_number` (nullable — peut être inconnu tant que non confirmé)
- `license_number` (nullable)
- `consent_image` (booléen/nullable — voir section RGPD ci-dessous)

### User (prévu dès le MVP, un seul compte utilisé en pratique)
- `id`
- `email`
- `role` (ex. "admin" pour le MVP ; valeurs futures : "bénévole",
  "lecture seule"...)
- `created_at`

## 2. Entités vidéo et match

### Match
- `id`
- `date`
- `team_home_id`, `team_away_id`
- `category` (hérité des équipes, dénormalisé pour faciliter les requêtes)
- `video_id`
- `status` (ex. "importé", "en cours d'analyse", "à valider", "validé")

### Video
- `id`
- `match_id`
- `file_path`
- `duration_seconds`
- `fps_source`
- `resolution`
- `retention_until` (nullable — date après laquelle la vidéo source peut être
  supprimée, voir RGPD)
- `imported_at`

### Period
- `id`
- `match_id`
- `index` (1, 2, 3, 4, prolongation...)
- `start_timestamp`, `end_timestamp` (en secondes, relatif à la vidéo)

## 3. Vision et tracking (sorties brutes du pipeline, avant toute statistique)

### TrackPoint
- `id`
- `track_id`
- `timestamp`
- `x_pixel`, `y_pixel`
- `bbox` (x, y, largeur, hauteur)
- `confidence`

### Track
- `id`
- `match_id`
- `first_seen`, `last_seen`
- `player_id` (nullable tant que non identifié — voir PlayerIdentification)

### PlayerIdentification
Table de correction humaine : association entre un `track` détecté et un
`player` réel, avec traçabilité de la méthode.
- `id`
- `track_id`
- `player_id`
- `method` (ex. "numéro de maillot", "couleur équipe", "correction manuelle")
- `confidence` (nullable si saisie manuelle)
- `manually_verified` (booléen)
- `verified_by` (user_id, nullable)
- `verified_at`

### CourtCalibration
- `id`
- `match_id` (ou `video_id` si plusieurs calibrations par vidéo deviennent
  nécessaires — un seul enregistrement par match pour le MVP, caméra fixe)
- `homography_matrix` (sérialisée)
- `reference_points` (points image ↔ points terrain utilisés pour calibrer)
- `created_at`

## 4. Événements

### Event (table de base commune, ou colonne `type` + table unique selon
l'implémentation — à trancher en M8/M12 ; champs communs listés ici)
- `id`
- `match_id`
- `timestamp`
- `event_type` (`shot`, `rebound`, `foul`, `turnover`, `pass`, `steal`,
  `block`, `possession_start`, `possession_end`, ...)
- `player_id` (nullable — un événement peut être détecté avant
  identification du joueur)
- `team_id`
- `x`, `y` (coordonnées terrain, issues de `CourtCalibration`, nullable si
  non applicable)
- `confidence`
- `source` (`auto` ou `manual`)
- `manually_verified` (booléen)
- `created_at`, `updated_at`

### Sous-types (champs spécifiques, en plus des champs communs `Event`)

**ShotEvent**
- `shot_type` (`2PT`, `3PT`, `FT`)
- `made` (booléen)

**ReboundEvent**
- `rebound_type` (`offensive`, `defensive`)

**FoulEvent**
- `foul_type` (ex. personnelle, technique, antisportive)

**TurnoverEvent**
- `turnover_type` (nullable, ex. perte simple, marcher, 3 secondes...)

**PassEvent**
- `target_player_id` (nullable)
- `is_assist` (booléen, déterminé a posteriori si la passe précède un panier)

**StealEvent**
- `stolen_from_player_id` (nullable)

**BlockEvent**
- `shot_event_id` (référence au tir contré, nullable)

### Possession
- `id`
- `match_id`
- `team_id`
- `start_timestamp`, `end_timestamp`
- `end_reason` (`shot_made`, `turnover`, `period_end`, ...)

## 5. Statistiques (dérivées, recalculables)

Les statistiques ne sont pas la source de vérité : elles sont recalculées à
partir des `Event`. Pour la performance, un **cache** peut être persisté,
mais il doit toujours pouvoir être régénéré intégralement.

### TeamStatistics (vue/cache, par match)
- `match_id`, `team_id`
- score, possessions, pace, FG (tentés/réussis), 2PT, 3PT, FT, rebonds
  off./déf., passes décisives, interceptions, contres, pertes de balle,
  fautes — détail des formules dans `statistics_definition.md`

### PlayerStatistics (vue/cache, par match et par joueur)
- `match_id`, `player_id`
- minutes jouées, points, FGM/FGA, 2PM/2PA, 3PM/3PA, FTM/FTA, rebonds
  off./déf., passes décisives, interceptions, contres, pertes de balle,
  fautes

## 6. Vie privée / RGPD (champs prévus dès le MVP, non nécessairement
exploités immédiatement — voir `requirements.md` §5.3)

- `Player.consent_image` : consentement à l'image du joueur (nullable =
  non renseigné).
- `Video.retention_until` : date de purge prévue de la vidéo source.
- Possibilité future (non implémentée en MVP) : un flag
  `Export.faces_blurred` si un export anonymisé est généré.

## 7. Diagramme relationnel simplifié

```
Club ──< Team ──< Player ──< PlayerIdentification >── Track ──< TrackPoint
                     │                                   │
                     │                                   │
Match >── Team(home/away)                        Match ──< CourtCalibration
  │
  ├──< Video
  ├──< Period
  ├──< Event <── (ShotEvent | ReboundEvent | FoulEvent | TurnoverEvent
  │               | PassEvent | StealEvent | BlockEvent)
  ├──< Possession
  ├──< TeamStatistics (cache)
  └──< PlayerStatistics (cache)

User (role) — indépendant, utilisé par PlayerIdentification.verified_by
```
