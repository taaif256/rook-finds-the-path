import { Coordinate, GridSize } from '../../core/models';

export interface BoardRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

/**
 * The square under a viewport point, or `null` when the point is outside the board.
 * `rect` is the on-screen rectangle of the grid itself (no frame or padding).
 */
export function cellAtPoint(rect: BoardRect, size: GridSize, x: number, y: number): Coordinate | null {
  if (rect.width <= 0 || rect.height <= 0) {
    return null;
  }
  const dx = x - rect.left;
  const dy = y - rect.top;
  if (dx < 0 || dy < 0 || dx >= rect.width || dy >= rect.height) {
    return null;
  }
  return {
    row: Math.min(size.rows - 1, Math.floor((dy / rect.height) * size.rows)),
    col: Math.min(size.cols - 1, Math.floor((dx / rect.width) * size.cols)),
  };
}

/**
 * Every square on a straight line from `from` to `to`, both included (Bresenham).
 * Used so a fast drag paints a continuous stroke instead of skipping squares.
 */
export function cellsBetween(from: Coordinate, to: Coordinate): Coordinate[] {
  const cells: Coordinate[] = [];
  let row = from.row;
  let col = from.col;
  const dRow = Math.abs(to.row - row);
  const dCol = Math.abs(to.col - col);
  const stepRow = row < to.row ? 1 : -1;
  const stepCol = col < to.col ? 1 : -1;
  let error = dCol - dRow;

  for (;;) {
    cells.push({ row, col });
    if (row === to.row && col === to.col) {
      return cells;
    }
    const doubled = 2 * error;
    if (doubled > -dRow) {
      error -= dRow;
      col += stepCol;
    }
    if (doubled < dCol) {
      error += dCol;
      row += stepRow;
    }
  }
}
