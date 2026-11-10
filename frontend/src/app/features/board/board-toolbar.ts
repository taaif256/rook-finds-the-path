import { Component, computed, inject } from '@angular/core';

import { GRID_SIZE_OPTIONS } from '../../core/config/board.config';
import { TOOLS } from '../../core/models';
import { PlaybackService } from '../visualization/playback.service';
import { VisualizationStateService } from '../visualization/visualization-state.service';
import { BoardInteractionService } from './board-interaction.service';
import { BoardStateService } from './board-state.service';

/** Tool buttons, board size and the board-wide actions. */
@Component({
  selector: 'app-board-toolbar',
  templateUrl: './board-toolbar.html',
  styleUrl: './board-toolbar.scss',
})
export class BoardToolbar {
  private readonly board = inject(BoardStateService);
  private readonly visualization = inject(VisualizationStateService);
  private readonly playback = inject(PlaybackService);
  protected readonly interaction = inject(BoardInteractionService);

  protected readonly tools = TOOLS;
  protected readonly sizeOptions = GRID_SIZE_OPTIONS;

  protected readonly currentSize = computed(() => this.board.size().rows);
  protected readonly canClearVisualization = computed(
    () => !this.visualization.isEmpty() || this.playback.status() !== 'ready',
  );
  protected readonly canResetBoard = computed(() => !this.board.isBlank() || !this.visualization.isEmpty());

  protected onSizeChange(event: Event): void {
    const size = Number((event.target as HTMLSelectElement).value);
    if (Number.isInteger(size)) {
      this.interaction.resizeBoard(size);
    }
  }
}
