import { Injectable, computed, inject, signal } from '@angular/core';
import { Subscription } from 'rxjs';

import { PathfindingRequest } from '../../core/models';
import { PathfindingApiError, PathfindingApiService } from '../../core/services/pathfinding-api.service';
import { AlgorithmSelectionService } from '../algorithms/algorithm-selection.service';
import { BoardStateService } from '../board/board-state.service';
import { PlaybackService } from './playback.service';

/**
 * Sends the board to the backend and hands the answer to the playback.
 *
 * It never changes the board. If the board is edited while a request is in flight, the answer
 * is dropped, since it describes a board that no longer exists.
 */
@Injectable({ providedIn: 'root' })
export class SearchRunnerService {
  private readonly api = inject(PathfindingApiService);
  private readonly board = inject(BoardStateService);
  private readonly selection = inject(AlgorithmSelectionService);
  private readonly playback = inject(PlaybackService);

  private pending: Subscription | null = null;
  private readonly loadingState = signal(false);
  private readonly failure = signal<{ message: string; revision: number } | null>(null);

  /** True while waiting for the backend. */
  readonly loading = this.loadingState.asReadonly();

  /** Why a search can't start yet, or `null` when it can. */
  readonly blockedReason = computed(() => {
    if (!this.board.start()) {
      return 'Place a start square to run a search.';
    }
    if (!this.board.end()) {
      return 'Place an end square to run a search.';
    }
    return null;
  });

  /** The last request's error. Hidden once the board changes, as the user may have fixed it. */
  readonly error = computed(() => {
    const failure = this.failure();
    return failure && failure.revision === this.board.revision() ? failure.message : null;
  });

  /**
   * Run the selected algorithm on the current board. With `autoplay` the animation starts
   * at once; without it the first step is drawn and the search waits, paused.
   */
  run(options: { autoplay: boolean } = { autoplay: true }): void {
    const { start, end, rows, cols, barriers } = this.board.config();
    if (this.loadingState() || !start || !end) {
      return;
    }
    const request: PathfindingRequest = {
      algorithm: this.selection.algorithm(),
      grid: { rows, cols },
      start,
      end,
      barriers,
      movement: 'four_directional',
    };
    const revision = this.board.revision();

    this.pending?.unsubscribe();
    this.playback.discard();
    this.failure.set(null);
    this.loadingState.set(true);

    this.pending = this.api.run(request).subscribe({
      next: (response) => {
        this.loadingState.set(false);
        if (this.board.revision() !== revision) {
          return; // edited meanwhile: this answer is for an old board
        }
        this.playback.load(response, options);
        if (!options.autoplay) {
          this.playback.step();
        }
      },
      error: (error: unknown) => {
        this.loadingState.set(false);
        const message = error instanceof PathfindingApiError ? error.message : 'The search failed unexpectedly. Please try again.';
        this.failure.set({ message, revision });
      },
    });
  }
}
