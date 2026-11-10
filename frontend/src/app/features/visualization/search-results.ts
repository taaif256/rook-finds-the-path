import { DecimalPipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';

import { algorithmLabel } from '../../core/models';
import { PlaybackService } from './playback.service';

/** Progress while a search plays, then its numbers once it has finished. */
@Component({
  selector: 'app-search-results',
  imports: [DecimalPipe],
  templateUrl: './search-results.html',
  styleUrl: './search-results.scss',
})
export class SearchResults {
  private readonly playback = inject(PlaybackService);

  protected readonly result = this.playback.result;
  protected readonly progress = this.playback.progress;

  protected readonly finished = computed(() => {
    const status = this.playback.status();
    return status === 'completed' || status === 'no-path';
  });
  protected readonly name = computed(() => {
    const result = this.result();
    return result ? algorithmLabel(result.algorithm) : '';
  });
  protected readonly noPath = computed(() => this.playback.status() === 'no-path');
  protected readonly greedyNote = computed(() => {
    const result = this.result();
    return this.finished() && !!result?.path_found && result.algorithm === 'gbfs';
  });
}
