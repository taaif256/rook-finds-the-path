import { Coordinate, OverlayKind, PathfindingResponse, sameCell } from '../../core/models';

/** One thing to draw: a square and what it turns into. */
export interface PlaybackStep {
  cell: Coordinate;
  kind: OverlayKind;
}

/**
 * The response turned into an ordered list of drawing steps.
 *
 * Open and closed events share one `step` counter, so sorting them by it restores the order
 * the search happened in. The final path is drawn after the search. Start and end are left
 * out: they are always drawn on top, so drawing them would only make the animation pause.
 */
export function buildTimeline(response: PathfindingResponse): PlaybackStep[] {
  const search = [
    ...response.open_events.map((event) => ({ step: event.step, cell: event.node, kind: 'open' as OverlayKind })),
    ...response.closed_events.map((event) => ({ step: event.step, cell: event.node, kind: 'closed' as OverlayKind })),
  ].sort((a, b) => a.step - b.step);

  const path = response.path.map((cell) => ({ cell, kind: 'path' as OverlayKind }));

  return [...search, ...path]
    .filter(({ cell }) => !sameCell(cell, response.start) && !sameCell(cell, response.end))
    .map(({ cell, kind }) => ({ cell, kind }));
}
