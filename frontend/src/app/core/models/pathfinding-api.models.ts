import { Coordinate, GridSize } from './coordinate.model';

/** Algorithm identifiers accepted by `POST /api/v1/pathfinding/run/`. */
export type AlgorithmId = 'gbfs' | 'astar';

/** Only four-directional movement (cost 1 per move) is supported in v1. */
export type MovementRule = 'four_directional';

export interface PathfindingRequest {
  algorithm: AlgorithmId;
  grid: GridSize;
  start: Coordinate;
  end: Coordinate;
  barriers: Coordinate[];
  movement: MovementRule;
}

/**
 * One step of the search, in the order it happened.
 * `step` is a single sequence shared by open and closed events so the two
 * lists can be merged back into the exact original order for animation.
 */
export interface SearchEvent {
  step: number;
  node: Coordinate;
  g: number;
  h: number;
  /** The priority the algorithm used: `h` for GBFS, `g + h` for A*. */
  f: number;
}

export interface SearchMetrics {
  explored_nodes: number;
  /** Number of moves in the path (cells - 1). 0 when no path was found. */
  path_length: number;
  /** Total movement cost of the path. Equals `path_length` while every move costs 1. */
  path_cost: number;
  execution_time_ms: number;
}

export interface PathfindingResponse {
  algorithm: AlgorithmId;
  status: 'success';
  path_found: boolean;
  start: Coordinate;
  end: Coordinate;
  open_events: SearchEvent[];
  closed_events: SearchEvent[];
  /** Ordered cells from start to end, inclusive. Empty when no path was found. */
  path: Coordinate[];
  metrics: SearchMetrics;
}

/**
 * Body of every error response (400, 405, 415, ...).
 * `errors` maps request fields to messages using dotted paths such as
 * `grid.rows` or `barriers.2.col`; it is empty when the error is not about a field.
 */
export interface ApiErrorResponse {
  status: 'error';
  message: string;
  errors: Record<string, string[]>;
}

export interface HealthResponse {
  status: 'ok';
  service: string;
  api_version: string;
}
