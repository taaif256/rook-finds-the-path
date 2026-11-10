import { Injectable, computed, inject, signal } from '@angular/core';

import { DEFAULT_SPEED, PLAYBACK_SPEEDS, SpeedId } from '../../core/config/playback.config';
import { PathfindingResponse, SearchStatus } from '../../core/models';
import { BoardStateService } from '../board/board-state.service';
import { PlaybackStep, buildTimeline } from './playback-timeline';
import { VisualizationStateService } from './visualization-state.service';

/** A search that has been loaded for replay. */
interface Session {
  readonly response: PathfindingResponse;
  readonly steps: readonly PlaybackStep[];
  /** What the board and overlay looked like when it was loaded (see `isCurrent`). */
  readonly revision: number;
  readonly generation: number;
}

type Phase = 'paused' | 'running' | 'done';

/**
 * Replays a finished search on the board, one drawing step at a time.
 *
 * The backend computes the whole search at once; pausing, resuming, stepping and speed are
 * all done here by walking through the recorded steps. It only ever writes to
 * `VisualizationStateService`, never to the board.
 *
 * A session stops counting as soon as the board is edited or the overlay is cleared by anyone
 * else, because what is on screen no longer matches it. That is checked on every read, so
 * the status falls back to Ready straight away.
 */
@Injectable({ providedIn: 'root' })
export class PlaybackService {
  private readonly board = inject(BoardStateService);
  private readonly visualization = inject(VisualizationStateService);

  private readonly session = signal<Session | null>(null);
  private readonly phase = signal<Phase>('paused');
  private readonly drawn = signal(0);
  private readonly speedState = signal<SpeedId>(DEFAULT_SPEED);

  private frame: number | null = null;
  private lastFrameTime: number | null = null;
  private budget = 0;

  readonly speed = this.speedState.asReadonly();

  /** The loaded search, or `null` when there is none or it no longer matches the board. */
  readonly current = computed(() => {
    const session = this.session();
    return session && this.isCurrent(session) ? session : null;
  });

  /** The API response of the current search (metrics, algorithm, whether a path exists). */
  readonly result = computed(() => this.current()?.response ?? null);

  readonly status = computed<SearchStatus>(() => {
    const session = this.current();
    if (!session) {
      return 'ready';
    }
    switch (this.phase()) {
      case 'running':
        return 'running';
      case 'paused':
        return 'paused';
      case 'done':
        return session.response.path_found ? 'completed' : 'no-path';
    }
  });

  readonly progress = computed(() => ({ drawn: this.drawn(), total: this.current()?.steps.length ?? 0 }));

  /** Forget the current search and wipe what it drew. */
  discard(): void {
    this.stopTimer();
    this.session.set(null);
    this.visualization.clear();
  }

  /** Load a search and show it from the start, playing at once or waiting for a step. */
  load(response: PathfindingResponse, options: { autoplay: boolean }): void {
    this.discard();
    const steps = buildTimeline(response);
    this.drawn.set(0);
    this.session.set({
      response,
      steps,
      revision: this.board.revision(),
      generation: this.visualization.generation(), // after discard(), which clears
    });
    this.phase.set(steps.length === 0 ? 'done' : 'paused');
    if (options.autoplay) {
      this.play();
    }
  }

  /** Start, or carry on playing. */
  play(): void {
    if (!this.hasSession() || this.phase() === 'done') {
      return;
    }
    this.phase.set('running');
    this.startTimer();
  }

  pause(): void {
    if (this.hasSession() && this.phase() === 'running') {
      this.stopTimer();
      this.phase.set('paused');
    }
  }

  /** Draw exactly one more step and stay paused. */
  step(): void {
    if (!this.hasSession() || this.phase() === 'done') {
      return;
    }
    this.stopTimer();
    this.phase.set('paused');
    this.advance(1);
  }

  /** Draw everything that is left at once. */
  finish(): void {
    const session = this.current();
    if (!session || this.phase() === 'done') {
      return;
    }
    this.advance(session.steps.length);
  }

  setSpeed(id: SpeedId): void {
    this.speedState.set(id);
  }

  // --- internals -------------------------------------------------------------

  private isCurrent(session: Session): boolean {
    return session.revision === this.board.revision() && session.generation === this.visualization.generation();
  }

  /** Whether there is a session that still matches the board. Stops the clock if not. */
  private hasSession(): boolean {
    if (this.current()) {
      return true;
    }
    this.stopTimer();
    return false;
  }

  private advance(count: number): void {
    const session = this.session();
    if (!session) {
      return;
    }
    const from = this.drawn();
    const to = Math.min(session.steps.length, from + count);
    for (let index = from; index < to; index++) {
      const { cell, kind } = session.steps[index];
      this.visualization.mark(cell, kind);
    }
    this.drawn.set(to);
    if (to >= session.steps.length) {
      this.stopTimer();
      this.phase.set('done');
    }
  }

  private startTimer(): void {
    if (this.frame !== null) {
      return;
    }
    this.lastFrameTime = null;
    this.budget = 0;
    this.frame = requestAnimationFrame(this.onFrame);
  }

  private stopTimer(): void {
    if (this.frame !== null) {
      cancelAnimationFrame(this.frame);
      this.frame = null;
    }
  }

  /** Each frame draws as many steps as the chosen speed calls for, so any speed stays smooth. */
  private readonly onFrame = (time: number): void => {
    this.frame = null;
    if (!this.hasSession() || this.phase() !== 'running') {
      return;
    }
    // Cap the gap so coming back to a hidden tab doesn't jump ahead.
    const elapsed = this.lastFrameTime === null ? 0 : Math.min(time - this.lastFrameTime, 100);
    this.lastFrameTime = time;

    const rate = PLAYBACK_SPEEDS.find((option) => option.id === this.speedState())?.stepsPerSecond ?? 30;
    this.budget += (elapsed / 1000) * rate;
    const due = Math.floor(this.budget);
    this.budget -= due;
    if (due > 0) {
      this.advance(due);
    }
    if (this.phase() === 'running') {
      this.frame = requestAnimationFrame(this.onFrame);
    }
  };
}
