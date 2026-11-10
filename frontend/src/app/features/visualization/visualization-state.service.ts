import { Injectable, Signal, computed, signal } from '@angular/core';

import { Coordinate, OverlayKind, cellKey } from '../../core/models';

/**
 * What a search has drawn on the board: open, closed and path squares.
 *
 * This is deliberately separate from `BoardStateService`. It can be cleared at
 * any time without touching the user's board, and it never stores start, end or
 * barriers.
 */
@Injectable({ providedIn: 'root' })
export class VisualizationStateService {
  // Mutated in place (an animation can mark thousands of squares), so the signal
  // is told every write is a change.
  private readonly marks = signal(new Map<string, OverlayKind>(), { equal: () => false });

  private readonly generationState = signal(0);

  readonly overlay: Signal<ReadonlyMap<string, OverlayKind>> = this.marks.asReadonly();
  /**
   * Goes up by one on every `clear()`, even when there was nothing to clear. Whoever is
   * drawing (the playback) remembers the value it saw, so it can tell that someone else
   * wiped the overlay and its drawing is no longer on the board.
   */
  readonly generation = this.generationState.asReadonly();
  readonly isEmpty = computed(() => this.marks().size === 0);

  mark(cell: Coordinate, kind: OverlayKind): void {
    this.marks.update((marks) => marks.set(cellKey(cell), kind));
  }

  /** Remove everything the search drew. Does not touch the board. */
  clear(): void {
    this.generationState.update((generation) => generation + 1);
    if (this.marks().size === 0) {
      return;
    }
    this.marks.set(new Map());
  }
}
