import { Component, computed, inject } from '@angular/core';

import { ALGORITHMS } from '../../core/models';
import { PlaybackService } from '../visualization/playback.service';
import { SearchRunnerService } from '../visualization/search-runner.service';
import { AlgorithmSelectionService } from './algorithm-selection.service';

/** Pick the algorithm for the next run. Locked while a search is in progress. */
@Component({
  selector: 'app-algorithm-selector',
  templateUrl: './algorithm-selector.html',
  styleUrl: './algorithm-selector.scss',
})
export class AlgorithmSelector {
  private readonly playback = inject(PlaybackService);
  private readonly runner = inject(SearchRunnerService);
  protected readonly selection = inject(AlgorithmSelectionService);

  protected readonly algorithms = ALGORITHMS;
  protected readonly locked = computed(
    () => this.runner.loading() || this.playback.status() === 'running' || this.playback.status() === 'paused',
  );
}
