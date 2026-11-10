import { Component, computed, inject } from '@angular/core';

import { Coordinate } from '../../core/models';
import { AlgorithmSelector } from '../algorithms/algorithm-selector';
import { PlaybackControls } from '../visualization/playback-controls';
import { SearchResults } from '../visualization/search-results';
import { BoardGrid } from './board-grid';
import { BoardInteractionService } from './board-interaction.service';
import { BoardLegend } from './board-legend';
import { BoardStateService } from './board-state.service';
import { BoardToolbar } from './board-toolbar';

/** Position as a person counts it: from 1. */
function describe(cell: Coordinate | null): string {
  return cell ? `row ${cell.row + 1}, column ${cell.col + 1}` : 'Not placed';
}

/** The board editing screen: toolbar, chessboard, tool hint, board summary and legend. */
@Component({
  selector: 'app-board-page',
  imports: [BoardToolbar, BoardGrid, BoardLegend, AlgorithmSelector, PlaybackControls, SearchResults],
  templateUrl: './board-page.html',
  styleUrl: './board-page.scss',
})
export class BoardPage {
  private readonly board = inject(BoardStateService);
  protected readonly interaction = inject(BoardInteractionService);

  protected readonly startLabel = computed(() => describe(this.board.start()));
  protected readonly endLabel = computed(() => describe(this.board.end()));
  protected readonly barrierCount = this.board.barrierCount;
}
