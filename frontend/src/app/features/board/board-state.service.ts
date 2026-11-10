import { Injectable, computed, signal } from '@angular/core';

import { DEFAULT_GRID_SIZE, MAX_GRID_SIZE, MIN_GRID_SIZE } from '../../core/config/board.config';
import {
  BoardCellKind,
  BoardConfig,
  CHANGED,
  Coordinate,
  EditResult,
  GridSize,
  UNCHANGED,
  cellKey,
  rejected,
  sameCell,
} from '../../core/models';

/**
 * The board the user has built: its size, one start, one end and any barriers.
 *
 * This is the only place that knows the editing rules. It never holds anything
 * a search produced (see `VisualizationStateService`). Each edit returns an
 * `EditResult` saying whether anything changed, so callers can react (and the
 * `revision` counter only moves on real changes).
 */
@Injectable({ providedIn: 'root' })
export class BoardStateService {
  private readonly sizeState = signal<GridSize>({ rows: DEFAULT_GRID_SIZE, cols: DEFAULT_GRID_SIZE });
  private readonly startState = signal<Coordinate | null>(null);
  private readonly endState = signal<Coordinate | null>(null);
  private readonly barrierState = signal<ReadonlySet<string>>(new Set());
  private readonly revisionState = signal(0);

  readonly size = this.sizeState.asReadonly();
  readonly start = this.startState.asReadonly();
  readonly end = this.endState.asReadonly();
  /** Barrier squares as `cellKey` strings. */
  readonly barriers = this.barrierState.asReadonly();
  /** Increases by one on every edit that changed the board. */
  readonly revision = this.revisionState.asReadonly();

  readonly barrierCount = computed(() => this.barrierState().size);
  readonly isBlank = computed(
    () => !this.startState() && !this.endState() && this.barrierState().size === 0,
  );

  /** The board in the shape the API needs. Barriers are sorted so the output is stable. */
  readonly config = computed<BoardConfig>(() => {
    const { rows, cols } = this.sizeState();
    const barriers = [...this.barrierState()]
      .map((key) => {
        const [row, col] = key.split(',').map(Number);
        return { row, col };
      })
      .sort((a, b) => a.row - b.row || a.col - b.col);
    return { rows, cols, start: this.startState(), end: this.endState(), barriers };
  });

  inBounds(cell: Coordinate): boolean {
    const { rows, cols } = this.sizeState();
    return Number.isInteger(cell.row) && Number.isInteger(cell.col)
      && cell.row >= 0 && cell.row < rows && cell.col >= 0 && cell.col < cols;
  }

  isBarrier(cell: Coordinate): boolean {
    return this.barrierState().has(cellKey(cell));
  }

  kindAt(cell: Coordinate): BoardCellKind {
    if (sameCell(cell, this.startState())) {
      return 'start';
    }
    if (sameCell(cell, this.endState())) {
      return 'end';
    }
    return this.isBarrier(cell) ? 'barrier' : 'unset';
  }

  /**
   * Move the start to `cell`. Placing it on a barrier replaces the barrier, since
   * the start must be traversable. It cannot share a square with the end.
   */
  setStart(cell: Coordinate): EditResult {
    if (!this.inBounds(cell)) {
      return rejected('out-of-bounds');
    }
    if (sameCell(cell, this.endState())) {
      return rejected('start-on-end');
    }
    if (sameCell(cell, this.startState())) {
      return UNCHANGED;
    }
    this.dropBarrier(cell);
    this.startState.set({ row: cell.row, col: cell.col });
    return this.changed();
  }

  /** Move the end to `cell`. Same rules as `setStart`. */
  setEnd(cell: Coordinate): EditResult {
    if (!this.inBounds(cell)) {
      return rejected('out-of-bounds');
    }
    if (sameCell(cell, this.startState())) {
      return rejected('end-on-start');
    }
    if (sameCell(cell, this.endState())) {
      return UNCHANGED;
    }
    this.dropBarrier(cell);
    this.endState.set({ row: cell.row, col: cell.col });
    return this.changed();
  }

  /** Start and end can never become barriers. */
  addBarrier(cell: Coordinate): EditResult {
    if (!this.inBounds(cell)) {
      return rejected('out-of-bounds');
    }
    if (sameCell(cell, this.startState())) {
      return rejected('barrier-on-start');
    }
    if (sameCell(cell, this.endState())) {
      return rejected('barrier-on-end');
    }
    if (this.isBarrier(cell)) {
      return UNCHANGED;
    }
    this.barrierState.update((barriers) => new Set(barriers).add(cellKey(cell)));
    return this.changed();
  }

  /** Remove a barrier. Does nothing to start or end. */
  removeBarrier(cell: Coordinate): EditResult {
    if (!this.inBounds(cell)) {
      return rejected('out-of-bounds');
    }
    return this.dropBarrier(cell) ? this.changed() : UNCHANGED;
  }

  /**
   * Return a square to the default unset state: removes a barrier, or the start or
   * end marker sitting there. With `keepEndpoints`, start and end are left alone
   * (used while dragging, so a stroke can't remove them by accident).
   */
  clearCell(cell: Coordinate, options: { keepEndpoints?: boolean } = {}): EditResult {
    if (!this.inBounds(cell)) {
      return rejected('out-of-bounds');
    }
    if (sameCell(cell, this.startState())) {
      if (options.keepEndpoints) {
        return UNCHANGED;
      }
      this.startState.set(null);
      return this.changed();
    }
    if (sameCell(cell, this.endState())) {
      if (options.keepEndpoints) {
        return UNCHANGED;
      }
      this.endState.set(null);
      return this.changed();
    }
    return this.removeBarrier(cell);
  }

  /** Change the board size. This clears the board, since squares no longer line up. */
  resize(rows: number, cols: number): EditResult {
    for (const value of [rows, cols]) {
      if (!Number.isInteger(value) || value < MIN_GRID_SIZE || value > MAX_GRID_SIZE) {
        throw new RangeError(`Board size must be a whole number from ${MIN_GRID_SIZE} to ${MAX_GRID_SIZE}.`);
      }
    }
    const current = this.sizeState();
    if (current.rows === rows && current.cols === cols) {
      return UNCHANGED;
    }
    this.sizeState.set({ rows, cols });
    this.clearEverything();
    return this.changed();
  }

  /** Remove the start, end and every barrier. Keeps the size. */
  reset(): EditResult {
    if (this.isBlank()) {
      return UNCHANGED;
    }
    this.clearEverything();
    return this.changed();
  }

  private clearEverything(): void {
    this.startState.set(null);
    this.endState.set(null);
    this.barrierState.set(new Set());
  }

  private dropBarrier(cell: Coordinate): boolean {
    const key = cellKey(cell);
    if (!this.barrierState().has(key)) {
      return false;
    }
    this.barrierState.update((barriers) => {
      const next = new Set(barriers);
      next.delete(key);
      return next;
    });
    return true;
  }

  private changed(): EditResult {
    this.revisionState.update((revision) => revision + 1);
    return CHANGED;
  }
}
