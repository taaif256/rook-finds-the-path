/** A zero-based grid position. `row` grows downward, `col` grows rightward. */
export interface Coordinate {
  row: number;
  col: number;
}

export interface GridSize {
  rows: number;
  cols: number;
}

/** A stable string key for using a cell in a `Set` or `Map`. */
export function cellKey(cell: Coordinate): string {
  return `${cell.row},${cell.col}`;
}

export function sameCell(a: Coordinate | null | undefined, b: Coordinate | null | undefined): boolean {
  return !!a && !!b && a.row === b.row && a.col === b.col;
}
