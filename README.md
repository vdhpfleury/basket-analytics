# basket-analytics

Analyse vidéo de matchs de basket amateur pour produire automatiquement des
statistiques d'équipe et individuelles, avec validation humaine.

- Cahier des charges : [`docs/requirements.md`](docs/requirements.md)
- Architecture : [`docs/architecture.md`](docs/architecture.md)
- Modèle de données : [`docs/data_model.md`](docs/data_model.md)
- Définition des statistiques : [`docs/statistics_definition.md`](docs/statistics_definition.md)
- Feuille de route (milestones M0→M17) : [`ROADMAP.md`](ROADMAP.md)
- Règles de travail pour Claude Code : [`CLAUDE.md`](CLAUDE.md)

Statut actuel : **M1 — squelette applicatif** (backend FastAPI + frontend
React, endpoint `/health`, aucune détection/vidéo à ce stade).

## Lancer le projet en local

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

L'API est alors disponible sur http://localhost:8000 (`GET /health` →
`{"status": "ok"}`).

Lancer les tests : `pytest` (depuis `backend/`, venv activée).

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

L'application est alors disponible sur http://localhost:5173 et affiche le
statut de connexion au backend. Le backend doit être démarré au préalable
(voir ci-dessus) pour que la page affiche "connecté".
