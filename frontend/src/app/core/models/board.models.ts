import { Coordinate } from './coordinate.model';

/** What a user can put on a square. This is the board configuration. */
export type BoardCellKind = 'unset' | 'start' | 'end' | 'barrier';

/** What a search draws on top of an unset square. This is the disposable visualization. */
export type OverlayKind = 'open' | 'closed' | 'path';

/** Everything a square can look like. */
export type NodeKind = BoardCellKind | OverlayKind;

/** The editing tools in the toolbar. */
export type Tool = 'start' | 'end' | 'barrier' | 'unset';

/** The board as the API needs it (see `PathfindingRequest`). */
export interface BoardConfig {
  rows: number;
  cols: number;
  start: Coordinate | null;
  end: Coordinate | null;
  barriers: Coordinate[];
}

export type RejectReason = 'out-of-bounds' | 'barrier-on-start' | 'barrier-on-end' | 'start-on-end' | 'end-on-start';

export type EditResult =
  | { readonly status: 'changed' }
  | { readonly status: 'unchanged' }
  | { readonly status: 'rejected'; readonly reason: RejectReason };

export const CHANGED: EditResult = { status: 'changed' };
export const UNCHANGED: EditResult = { status: 'unchanged' };
export function rejected(reason: RejectReason): EditResult {
  return { status: 'rejected', reason };
}
