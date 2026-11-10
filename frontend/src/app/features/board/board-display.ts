import { BoardCellKind, NodeKind, OverlayKind } from '../../core/models';

/**
 * What a square looks like: the user's board configuration wins, and the search
 * overlay only shows through on squares the user left unset. So the start and
 * end markers and the barriers are never hidden by an animation.
 */
export function displayKind(board: BoardCellKind, overlay: OverlayKind | undefined): NodeKind {
  if (board !== 'unset') {
    return board;
  }
  return overlay ?? 'unset';
}

/** Alternating chessboard shade for a square. */
export function shadeOf(row: number, col: number): 'light' | 'dark' {
  return (row + col) % 2 === 0 ? 'light' : 'dark';
}
