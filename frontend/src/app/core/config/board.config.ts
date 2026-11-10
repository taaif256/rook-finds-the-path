/** Board sizes offered in the UI (square boards). */
export const GRID_SIZE_OPTIONS = [10, 20, 30] as const;
export const DEFAULT_GRID_SIZE = 20;

/** Limits accepted by the backend (`grid.rows` / `grid.cols`). Keep in sync with the API contract. */
export const MIN_GRID_SIZE = 1;
export const MAX_GRID_SIZE = 50;
