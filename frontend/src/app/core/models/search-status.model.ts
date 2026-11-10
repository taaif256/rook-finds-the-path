/** Where a search is in its life, as the user sees it. A frontend concept, not an API field. */
export type SearchStatus = 'ready' | 'running' | 'paused' | 'completed' | 'no-path';

export const SEARCH_STATUS_LABELS: Record<SearchStatus, string> = {
  ready: 'Ready',
  running: 'Running',
  paused: 'Paused',
  completed: 'Completed',
  'no-path': 'No Path Found',
};
