# Rook finds the path: Chessboard Robot Navigation Visualizer

An interactive visualizer for **Greedy Best-First Search** and **A\*** on a chessboard-style grid.
Angular renders and animates; Django REST Framework validates requests and runs the algorithms.

## Prerequisites

- Python 3.12+ (Django 6.1 requirement)
- Node.js 22.22.3+ or 24.15+ (Angular 22 requirement) and npm

## Backend

```bash
cd backend
pipenv install 
pipenv shell
python manage.py runserver 8000
```

Check it: <http://localhost:8000/api/v1/health/>

Try a search (A* on a 10x10 board with a short wall):

```bash
curl -X POST http://localhost:8000/api/v1/pathfinding/run/ \
  -H 'Content-Type: application/json' \
  -d '{"algorithm": "astar",
       "grid": {"rows": 10, "cols": 10},
       "start": {"row": 0, "col": 0},
       "end": {"row": 9, "col": 9},
       "barriers": [{"row": 2, "col": 3}, {"row": 3, "col": 3}, {"row": 4, "col": 3}]}'
```

Use `"algorithm": "gbfs"` for Greedy Best-First Search. The request and response formats, and the
error format, are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#4-api-contract-apiv1).

Run the tests (no database is used):

```bash
python manage.py test
```

Optional environment variables (defaults work for local development; see `backend/.env.example`):

| Variable | Default |
|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key, **set your own outside local use** |
| `DJANGO_DEBUG` | `true` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` |

## Frontend

```bash
cd frontend
npm install
npm start                          # http://localhost:4200
```

The header shows whether the app can reach the backend. The API base URL lives in
`src/app/core/config/api.config.ts` (`http://localhost:8000/api/v1`).

```bash
npm test -- --watch=false          # unit tests (Vitest + jsdom, no browser needed)
npm run build                      # production build into dist/
```

## Project layout

```
backend/    Django + DRF API (config/, apps/pathfinding/)
frontend/   Angular app (src/app/core, features, shared)
docs/       Architecture, API contract, implementation plan
```
