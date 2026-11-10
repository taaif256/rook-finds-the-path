import { Component, computed, inject } from '@angular/core';

import { PLAYBACK_SPEEDS, SpeedId } from '../../core/config/playback.config';
import { SEARCH_STATUS_LABELS } from '../../core/models';
import { PlaybackService } from './playback.service';
import { SearchRunnerService } from './search-runner.service';

/** Run / Pause / Resume, Step, Skip to end and speed, with the search status. */
@Component({
  selector: 'app-playback-controls',
  templateUrl: './playback-controls.html',
  styleUrl: './playback-controls.scss',
})
export class PlaybackControls {
  protected readonly playback = inject(PlaybackService);
  protected readonly runner = inject(SearchRunnerService);

  protected readonly speeds = PLAYBACK_SPEEDS;
  protected readonly status = this.playback.status;

  /** `ready`, `completed` and `no-path` all mean "nothing in progress": the next run starts fresh. */
  private readonly idle = computed(() => {
    const status = this.status();
    return status === 'ready' || status === 'completed' || status === 'no-path';
  });

  protected readonly statusLabel = computed(() =>
    this.runner.loading() ? 'Searching…' : SEARCH_STATUS_LABELS[this.status()],
  );
  protected readonly statusKey = computed(() => (this.runner.loading() ? 'loading' : this.status()));

  protected readonly primaryLabel = computed(() => {
    switch (this.status()) {
      case 'running':
        return 'Pause';
      case 'paused':
        return 'Resume';
      case 'ready':
        return 'Run';
      default:
        return 'Run again';
    }
  });

  protected readonly canStartNew = computed(() => !this.runner.loading() && this.runner.blockedReason() === null);
  protected readonly primaryDisabled = computed(() => this.runner.loading() || (this.idle() && !this.canStartNew()));
  protected readonly canStep = computed(
    () => !this.runner.loading() && (this.status() === 'paused' || (this.status() === 'ready' && this.canStartNew())),
  );
  protected readonly canFinish = computed(() => this.status() === 'running' || this.status() === 'paused');
  /** Only worth saying when it's the reason the Run button is off. */
  protected readonly blockedReason = computed(() => (this.idle() ? this.runner.blockedReason() : null));

  protected onPrimary(): void {
    switch (this.status()) {
      case 'running':
        this.playback.pause();
        break;
      case 'paused':
        this.playback.play();
        break;
      default:
        this.runner.run({ autoplay: true });
    }
  }

  protected onStep(): void {
    if (this.status() === 'paused') {
      this.playback.step();
    } else {
      this.runner.run({ autoplay: false }); // fetch, then draw the first step and wait
    }
  }

  protected onSpeedChange(event: Event): void {
    this.playback.setSpeed((event.target as HTMLSelectElement).value as SpeedId);
  }
}
