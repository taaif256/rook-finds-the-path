import { Coordinate } from '../../core/models';
import { BoardRect, cellAtPoint, cellsBetween } from './board-geometry';

describe('cellAtPoint', () => {
  // A 2 x 4 board drawn at (100, 50), 200 x 100 px, so every square is 50 x 50.
  const rect: BoardRect = { left: 100, top: 50, width: 200, height: 100 };
  const size = { rows: 2, cols: 4 };

  it('finds the square under a point', () => {
    expect(cellAtPoint(rect, size, 110, 60)).toEqual({ row: 0, col: 0 });
    expect(cellAtPoint(rect, size, 290, 140)).toEqual({ row: 1, col: 3 });
    expect(cellAtPoint(rect, size, 175, 60)).toEqual({ row: 0, col: 1 });
  });

  it('treats the top-left edge of a square as inside it and the far edge as the next square', () => {
    expect(cellAtPoint(rect, size, 100, 50)).toEqual({ row: 0, col: 0 });
    expect(cellAtPoint(rect, size, 149.9, 99.9)).toEqual({ row: 0, col: 0 });
    expect(cellAtPoint(rect, size, 150, 100)).toEqual({ row: 1, col: 1 });
  });

  it('returns null outside the board, including its right and bottom edges', () => {
    expect(cellAtPoint(rect, size, 99.9, 60)).toBeNull();
    expect(cellAtPoint(rect, size, 110, 49.9)).toBeNull();
    expect(cellAtPoint(rect, size, 300, 60)).toBeNull();
    expect(cellAtPoint(rect, size, 110, 150)).toBeNull();
    expect(cellAtPoint(rect, size, -5, -5)).toBeNull();
  });

  it('returns null for a board that has no size yet', () => {
    expect(cellAtPoint({ left: 0, top: 0, width: 0, height: 0 }, size, 0, 0)).toBeNull();
  });

  it('works for non-square boards and a board at the origin', () => {
    const wide = { left: 0, top: 0, width: 300, height: 100 };
    expect(cellAtPoint(wide, { rows: 1, cols: 3 }, 250, 99)).toEqual({ row: 0, col: 2 });
    expect(cellAtPoint({ left: 0, top: 0, width: 90, height: 90 }, { rows: 30, cols: 30 }, 89.9, 89.9)).toEqual({
      row: 29,
      col: 29,
    });
  });
});

describe('cellsBetween', () => {
  const c = (row: number, col: number): Coordinate => ({ row, col });

  it('returns just the square when both ends are the same', () => {
    expect(cellsBetween(c(2, 2), c(2, 2))).toEqual([c(2, 2)]);
  });

  it('walks straight lines in both directions, starting at "from"', () => {
    expect(cellsBetween(c(0, 0), c(0, 3))).toEqual([c(0, 0), c(0, 1), c(0, 2), c(0, 3)]);
    expect(cellsBetween(c(3, 1), c(0, 1))).toEqual([c(3, 1), c(2, 1), c(1, 1), c(0, 1)]);
  });

  it('walks a diagonal', () => {
    expect(cellsBetween(c(0, 0), c(3, 3))).toEqual([c(0, 0), c(1, 1), c(2, 2), c(3, 3)]);
    expect(cellsBetween(c(3, 0), c(0, 3))).toEqual([c(3, 0), c(2, 1), c(1, 2), c(0, 3)]);
  });

  it('leaves no gaps on any line (checked over many pairs)', () => {
    let seed = 12345;
    const next = (max: number) => {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      return seed % max;
    };
    for (let i = 0; i < 500; i++) {
      const from = c(next(30), next(30));
      const to = c(next(30), next(30));
      const line = cellsBetween(from, to);

      expect(line[0]).toEqual(from);
      expect(line[line.length - 1]).toEqual(to);
      expect(line.length).toBe(Math.max(Math.abs(to.row - from.row), Math.abs(to.col - from.col)) + 1);
      for (let k = 1; k < line.length; k++) {
        const dRow = Math.abs(line[k].row - line[k - 1].row);
        const dCol = Math.abs(line[k].col - line[k - 1].col);
        expect(dRow <= 1 && dCol <= 1 && dRow + dCol > 0).toBe(true);
      }
    }
  });
});
