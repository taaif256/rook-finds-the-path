# Architecture, API Contract and Implementation Plan

## 1. System overview

```
┌──────────────────────────── Angular (frontend/) ────────────────────────────┐
│  Board feature        Visualization feature        Algorithms feature       │
│  - chessboard grid    - animation controller       - algorithm selector     │
│  - tools & drawing    - playback (pause/step/speed)- metrics / info panel   │
│  - BoardState         - VisualizationState (overlay)                        │
│                              core/: API services, models, config            │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ JSON over HTTP  (CORS: http://localhost:4200)
                                ▼
┌──────────────────────────── Django + DRF (backend/) ────────────────────────┐
│  api/ (views, serializers)  ──►  services/  ──►  algorithms/                │
│  validation + HTTP only         orchestration     pure search logic         │
│                                 + event formatting (greedy_best_first, astar)│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Responsibilities**

| Layer | Owns | Must not |
|---|---|---|
| Angular | Interaction, board editing, presentation, animation playback, UI status (Ready / Running / Paused / Completed / No Path Found) | Run pathfinding |
| DRF views and serializers | HTTP, request validation, status codes | Contain search logic |
| Service layer | Calling an algorithm, timing it, shaping the response | Know about HTTP |
| Algorithms | Search only: frontier, closed set, parents, path reconstruction | Know about JSON or the UI |

The backend is stateless. The whole search is computed per request and returned as an ordered
event history, which the frontend replays. Pause, resume and step are therefore pure frontend
features and no server session is needed.

## 2. Repository layout

```
chessboard-robot-navigation/
├── backend/
│   ├── manage.py, requirements.txt, .env.example
│   ├── config/                    settings, root urls, api_v1_urls, health view, exceptions.py (error envelope)
│   └── apps/pathfinding/
│       ├── api/                   urls.py, views.py, serializers.py
│       ├── algorithms/            pure search logic, no Django imports (see section 5)
│       ├── services/              pathfinding_service.py, visualization_serializer.py
│       └── tests/
├── frontend/src/app/
│   ├── core/                      config/, models/, services/
│   ├── features/{board,visualization,algorithms}/
│   └── shared/
└── docs/
```

## 3. Two kinds of cell state (kept separate)

- **BoardState** (user-owned, persists until reset): each cell is `unset`, `barrier`, plus one
  `start` and one `end` position.
- **VisualizationState** (algorithm-owned overlay, disposable): each cell may additionally be
  `open`, `closed` or `path`.

The renderer composes the two, with start and end always drawn on top. *Clear Visualization*
drops the overlay only; *Reset Board* drops both. Running an algorithm never writes to BoardState.

## 4. API contract (`/api/v1/`)

Coordinates are `{ "row": int, "col": int }`, zero-based, `row` increasing downward.
All field names are `snake_case`.

### `GET /api/v1/health/`

`200 OK`
```json
{ "status": "ok", "service": "chessboard-robot-navigation-api", "api_version": "v1" }
```

### `POST /api/v1/pathfinding/run/`

Request:
```json
{
  "algorithm": "astar",
  "grid": { "rows": 10, "cols": 10 },
  "start": { "row": 0, "col": 0 },
  "end": { "row": 9, "col": 9 },
  "barriers": [{ "row": 2, "col": 3 }, { "row": 3, "col": 3 }],
  "movement": "four_directional"
}
```

| Field | Rule |
|---|---|
| `algorithm` | `"gbfs"` or `"astar"`; anything else is rejected |
| `grid.rows`, `grid.cols` | JSON integers, 1 to 50 inclusive |
| `start`, `end` | `{row, col}` JSON integers; in bounds, distinct from each other, not on a barrier |
| `barriers` | optional (default empty); a list of `{row, col}`, at most 2500 entries; every entry in bounds; duplicates are tolerated and de-duplicated |
| `movement` | optional, only `"four_directional"` is accepted (default) |

Integers must be real JSON integers: `"3"`, `3.0` and `true` are rejected.

**Validation order.** The shape and types of the request are checked first, and every problem found
is reported at once (for example a bad algorithm and a bad grid size together). The grid rules
(coordinates in bounds, start different from end, nothing on a barrier) run only once the shape is
valid, and report the first rule that fails. Unknown extra fields are ignored.

Response `200 OK`. This is a real response for the request `{"algorithm": "astar", "grid": {"rows": 1, "cols": 3}, "start": {"row": 0, "col": 0}, "end": {"row": 0, "col": 2}, "barriers": []}` (`execution_time_ms` varies from run to run):
```json
{
  "algorithm": "astar",
  "status": "success",
  "path_found": true,
  "start": {"row": 0, "col": 0},
  "end": {"row": 0, "col": 2},
  "open_events": [
    {"step": 0, "node": {"row": 0, "col": 0}, "g": 0, "h": 2, "f": 2},
    {"step": 2, "node": {"row": 0, "col": 1}, "g": 1, "h": 1, "f": 2},
    {"step": 4, "node": {"row": 0, "col": 2}, "g": 2, "h": 0, "f": 2}
  ],
  "closed_events": [
    {"step": 1, "node": {"row": 0, "col": 0}, "g": 0, "h": 2, "f": 2},
    {"step": 3, "node": {"row": 0, "col": 1}, "g": 1, "h": 1, "f": 2},
    {"step": 5, "node": {"row": 0, "col": 2}, "g": 2, "h": 0, "f": 2}
  ],
  "path": [{"row": 0, "col": 0}, {"row": 0, "col": 1}, {"row": 0, "col": 2}],
  "metrics": {"explored_nodes": 3, "path_length": 2, "path_cost": 2, "execution_time_ms": 0.042}
}
```

**Decisions beyond the written spec**

1. **Shared `step` counter.** Open and closed events are separate lists, as required, but both
   carry one global, strictly increasing `step`. Sorting the union of the two lists by `step`
   restores the exact order the search happened in, which the animation needs (a node is opened
   *between* closings).
2. **Re-opened nodes.** A* can find a cheaper route to an already-open node and emit a second
   open event for it. The frontend treats the latest event as current.
3. **`f` means "the priority the algorithm used":** `h` for GBFS, `g + h` for A*.
4. **`path_length` is the number of moves** (cells − 1); `path_cost` is the total movement cost.
   They are equal while every move costs 1. `path` lists cells from start to end inclusive.
5. **No path is not an error.** It returns `200` with `path_found: false`, `path: []`,
   `path_length: 0`, `path_cost: 0`, and the full exploration history. The UI shows
   "No Path Found".
6. **Search status** (Ready, Running, Paused, Completed, No Path Found) is a frontend concept.
   The API `status` is always `"success"` on a `200`.
7. **Algorithm ids** `gbfs` / `astar` are my choice for the identifiers; the spec only fixed `astar`.
8. **`explored_nodes`** is the number of nodes taken from the frontier and explored, i.e. the number
   of `closed_events`. It includes the end node when it is reached.
9. **One error envelope for every error** (including 405 and 415, and on every endpoint), so the
   frontend needs a single error type. `errors` maps request fields to message lists using dotted
   paths (`grid.rows`, `start.row`, `barriers.2.col`) and is empty when the error is not about a
   field.
10. **Response size.** The whole search history is returned in one response, as the spec suggests.
    Measured on a 50x50 board, even the heaviest searches (a maze, or exhausting half the board when
    no path exists) produce about 3,600 to 3,900 events, 150 to 255 KiB, and under 30 ms of search time.

Errors all use the same body, on every endpoint:

```json
{
  "status": "error",
  "message": "Invalid request.",
  "errors": {
    "algorithm": ["Unknown algorithm \"dijkstra\". Valid algorithms: gbfs, astar."],
    "grid.rows": ["Must be an integer between 1 and 50."],
    "barriers.2.col": ["This field is required."]
  }
}
```

| Status | When | `message` | `errors` |
|---|---|---|---|
| `400` | Validation failure | `Invalid request.` | one entry per bad field |
| `400` | Body is not valid JSON | the parser's message | empty |
| `405` | Wrong HTTP method (`Allow` header is set) | `Method "GET" not allowed.` | empty |
| `415` | Content type is not JSON | `Unsupported media type ...` | empty |

A body that is not a JSON object reports under the key `non_field_errors`.

## 5. Algorithms (implemented in Phase 2)

All code is in `backend/apps/pathfinding/algorithms/` and is plain Python with no Django imports.

| Module | Role |
|---|---|
| `problem.py` | `Coordinate`, `SearchProblem` (the one place grid input is validated), `InvalidSearchProblemError`, size limits, neighbour order |
| `heuristics.py` | `manhattan_distance` |
| `frontier.py` | `PriorityFrontier`, the min-heap both algorithms share |
| `events.py` | `SearchEvent`, `EventKind`, `EventRecorder` (the visualization history) |
| `result.py` | `SearchResult`, `AlgorithmId` |
| `path.py` | `reconstruct_path` (parent map to ordered path) |
| `greedy_best_first.py`, `astar.py` | the two searches |
| `registry.py` | `get_algorithm("astar")`, `UnknownAlgorithmError` |

**How they work**

- Heuristic: Manhattan distance, admissible and consistent for 4-directional unit-cost moves.
- GBFS orders the frontier by `h`. A* orders by `g + h`. Both use the same `heapq`-based frontier.
- **Deterministic ties.** The frontier orders by `(f, h, insertion order)` and neighbours are visited
  up, down, left, right, so every search and animation is reproducible and tests can assert exact
  sequences.
- **GBFS** discovers each node at most once (a node in the open set or closed set is never added
  again), so it never re-expands anything. It is not optimal and the UI must say so. Its `g` values are
  the cost of the route it happened to discover and are reported for display only.
- **A\*** keeps `g` scores and parents. When it finds a cheaper route to a node that is already
  open, it updates that node's `g` and parent and records another open event (verified by a test
  fixture). Out-of-date heap entries are skipped when popped. Closed nodes are never re-opened:
  the Manhattan heuristic is consistent, so the first time a node is explored its `g` is already
  optimal.
- **Events** are written to a recorder that is separate from the search's own data structures
  (heap, open/closed sets, scores, parents). The search returns them in `SearchResult.events`, and
  `services/visualization_serializer.py` turns those into `open_events` / `closed_events`.
- The searches stop when the end node is taken from the frontier (and so gets a closed event), or
  when the frontier is empty (no path; the whole reachable region has been explored).
- Timing (`execution_time_ms`) is measured by the service layer, not by the algorithms.

**Validation.** `SearchProblem` raises `InvalidSearchProblemError` with a `field` (`grid.rows`,
`grid.cols`, `start`, `end` or `barriers`) and a message, for: grid size outside 1 to 50 or not an
integer, a malformed or out-of-bounds coordinate, start equal to end, and start or end on a barrier.
The request serializer maps these to the `400` response, so the rules live in one place.

**Tests** (`backend/apps/pathfinding/tests/`, `python manage.py test`, 171 tests in total across
Phases 1 to 3; the algorithm tests are described here and the API tests in section 6). Beyond the cases listed in the spec, A* and GBFS are checked against an
independent breadth-first search on thousands of random grids (path length for A*, reachability for
both), every run is checked against event invariants (including that each explored node had the
best priority in the frontier), and a deliberately broken copy of each algorithm was confirmed to
make the suite fail.

## 6. The API layer (implemented in Phase 3)

```
POST /api/v1/pathfinding/run/
  views.PathfindingRunView            thin: validate, run, respond
    -> serializers.PathfindingRequestSerializer   shape and types; grid rules via SearchProblem
    -> services.run_pathfinding                   picks the algorithm, times the search
    -> services.build_run_response                the only place that knows the response shape
  config.exceptions.api_exception_handler         turns every error into the envelope above
```

- The serializer does not repeat the grid rules. It builds a `SearchProblem` and translates its
  `InvalidSearchProblemError` into a request-field error, so the rules live in one place.
- The service layer is independent of HTTP; its clock can be injected, so timing is testable.
- `execution_time_ms` covers the search only (not validation or JSON encoding) and is rounded to 3
  decimals.

**API tests** (`test_pathfinding_endpoint.py`, `test_pathfinding_endpoint_errors.py`,
`test_pathfinding_service.py`, `test_error_format.py`): exact golden responses for both algorithms,
the spec example, no-path responses, optional fields, board-size limits, and every kind of invalid
payload (field by field, with the exact error keys). One test sends 120 random boards through HTTP
and checks the response against the algorithms and the independent BFS oracle. Mutation testing
(deliberately breaking the serializer, handler, service and formatter) was used to confirm the
tests fail when behaviour changes, and it exposed one gap (reporting an out-of-range grid size
together with unrelated errors) which now has a test.

## 7. Implementation plan

| Phase | Scope | Status |
|---|---|---|
| 1 | Angular app, Django + DRF project, CORS, `/api/v1/` routing, health check | **Done** |
| 2 | GBFS, A*, validation, path reconstruction, algorithm tests | **Done** |
| 3 | `POST /pathfinding/run/`, serializers, events + metrics, endpoint tests | **Done** |
| 4 | Chessboard grid, tools, drawing, BoardState | Next |
| 5 | API integration, animation controller, pause / resume / step / speed, path rendering | |
| 6 | Responsive styling, error handling, legends, algorithm descriptions, docs | |
