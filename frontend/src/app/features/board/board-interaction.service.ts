import { Injectable, computed, inject, signal } from '@angular/core';

import { Coordinate, EditResult, RejectReason, TOOLS, Tool, sameCell } from '../../core/models';
import { VisualizationStateService } from '../visualization/visualization-state.service';
import { cellsBetween } from './board-geometry';
import { BoardStateService } from './board-state.service';

const NOTICES: Record<RejectReason, string> = {
  'out-of-bounds': 'That square is outside the board.',
  'barrier-on-start': "The start square can't be a barrier. Move the start first.",
  'barrier-on-end': "The end square can't be a barrier. Move the end first.",
  'start-on-end': 'Start and end must be different squares.',
  'end-on-start': 'Start and end must be different squares.',
};

/** One press-drag-release on the board. */
interface Stroke {
  readonly tool: Tool;
  /** For the barrier tool: decided by the first square, so a stroke only adds or only removes. */
  readonly barrierMode: 'add' | 'remove';
  last: Coordinate | null;
}

/**
 * What the user's actions do: which tool is selected, how a click or drag applies
 * it to the board, and the toolbar's board-wide actions.
 *
 * Any edit that changes the board also clears the visualization, because a drawn
 * search no longer matches the board it ran on.
 */
@Injectable({ providedIn: 'root' })
export class BoardInteractionService {
  private readonly board = inject(BoardStateService);
  private readonly visualization = inject(VisualizationStateService);

  private readonly toolState = signal<Tool>('start');
  private readonly noticeState = signal<string | null>(null);
  private stroke: Stroke | null = null;

  readonly tool = this.toolState.asReadonly();
  /** Why the last action was refused, or `null`. Cleared by the next successful action. */
  readonly notice = this.noticeState.asReadonly();
  readonly toolHint = computed(() => TOOLS.find((tool) => tool.id === this.toolState())?.hint ?? '');

  selectTool(tool: Tool): void {
    this.toolState.set(tool);
    this.noticeState.set(null);
  }

  // --- click and drag --------------------------------------------------------

  /** Pointer pressed on `cell`: applies the tool there and starts a stroke. */
  beginStroke(cell: Coordinate): void {
    const tool = this.toolState();
    this.stroke = {
      tool,
      barrierMode: tool === 'barrier' && this.board.isBarrier(cell) ? 'remove' : 'add',
      last: cell,
    };
    this.applyAt(this.stroke, cell, true);
  }

  /** Pointer moved to `cell` (or off the board, `null`) during a stroke. */
  continueStroke(cell: Coordinate | null): void {
    const stroke = this.stroke;
    if (!stroke) {
      return;
    }
    if (!cell) {
      stroke.last = null; // left the board: don't draw a line across the gap on re-entry
      return;
    }
    if (sameCell(stroke.last, cell)) {
      return;
    }
    const markerTool = stroke.tool === 'start' || stroke.tool === 'end';
    // A marker just follows the pointer. Barriers and unsetting cover every square passed over.
    const squares = markerTool || !stroke.last ? [cell] : cellsBetween(stroke.last, cell).slice(1);
    for (const square of squares) {
      this.applyAt(stroke, square, false);
    }
    stroke.last = cell;
  }

  endStroke(): void {
    this.stroke = null;
  }

  /** A single press, as from the keyboard. */
  activateCell(cell: Coordinate): void {
    this.beginStroke(cell);
    this.endStroke();
  }

  // --- board-wide actions ----------------------------------------------------

  /** Remove start, end and barriers, and anything a search drew. */
  resetBoard(): void {
    this.board.reset();
    this.visualization.clear();
    this.noticeState.set(null);
  }

  /** Switch to a square board of `size`. Clears the board. */
  resizeBoard(size: number): void {
    this.board.resize(size, size);
    this.visualization.clear();
    this.noticeState.set(null);
  }

  /** Remove what a search drew and keep the board. */
  clearVisualization(): void {
    this.visualization.clear();
  }

  // --- internals -------------------------------------------------------------

  private applyAt(stroke: Stroke, cell: Coordinate, initial: boolean): void {
    let result: EditResult;
    switch (stroke.tool) {
      case 'start':
        result = this.board.setStart(cell);
        break;
      case 'end':
        result = this.board.setEnd(cell);
        break;
      case 'barrier':
        result = stroke.barrierMode === 'add' ? this.board.addBarrier(cell) : this.board.removeBarrier(cell);
        break;
      case 'unset':
        // Pressing directly on start or end clears it on purpose; dragging over them does not.
        result = this.board.clearCell(cell, { keepEndpoints: !initial });
        break;
    }

    if (result.status === 'changed') {
      this.visualization.clear();
      this.noticeState.set(null);
    } else if (result.status === 'rejected') {
      // Painting barriers across start or end is normal during a drag, so only a direct press
      // (or moving a marker) explains the refusal.
      const markerTool = stroke.tool === 'start' || stroke.tool === 'end';
      if (initial || markerTool) {
        this.noticeState.set(NOTICES[result.reason]);
      }
    }
  }
}
