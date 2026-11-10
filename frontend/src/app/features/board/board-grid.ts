import { Component, ElementRef, computed, inject, signal, viewChild } from '@angular/core';

import { Coordinate, NODE_KIND_INFO, NodeKind, cellKey } from '../../core/models';
import { VisualizationStateService } from '../visualization/visualization-state.service';
import { displayKind, shadeOf } from './board-display';
import { cellAtPoint } from './board-geometry';
import { BoardInteractionService } from './board-interaction.service';
import { BoardStateService } from './board-state.service';

interface GridCell {
  row: number;
  col: number;
  kind: NodeKind;
  shade: 'light' | 'dark';
  label: string;
}

interface GridRow {
  row: number;
  cells: GridCell[];
}

/**
 * The chessboard. It only draws what the services hold and passes pointer and
 * keyboard input to `BoardInteractionService`; it makes no editing decisions.
 *
 * Mouse, touch and pen all work through pointer events on the grid as a whole
 * (the square is worked out from the pointer position), so a drag keeps painting
 * even when it moves fast or briefly leaves the board.
 *
 * Keyboard: the grid is one tab stop. Arrow keys move between squares (Home/End
 * jump to the row's ends, with Ctrl to the board's corners) and Enter or Space
 * applies the selected tool.
 */
@Component({
  selector: 'app-board-grid',
  templateUrl: './board-grid.html',
  styleUrl: './board-grid.scss',
})
export class BoardGrid {
  private readonly board = inject(BoardStateService);
  private readonly visualization = inject(VisualizationStateService);
  private readonly interaction = inject(BoardInteractionService);

  private readonly gridElement = viewChild.required<ElementRef<HTMLElement>>('grid');
  private readonly focused = signal<Coordinate>({ row: 0, col: 0 });
  private activePointer: number | null = null;

  protected readonly size = this.board.size;

  protected readonly rows = computed<GridRow[]>(() => {
    const { rows, cols } = this.board.size();
    const overlay = this.visualization.overlay();
    return Array.from({ length: rows }, (_, row) => ({
      row,
      cells: Array.from({ length: cols }, (_, col): GridCell => {
        const cell = { row, col };
        const kind = displayKind(this.board.kindAt(cell), overlay.get(cellKey(cell)));
        return {
          row,
          col,
          kind,
          shade: shadeOf(row, col),
          label: `Row ${row + 1}, column ${col + 1}: ${NODE_KIND_INFO[kind].label}`,
        };
      }),
    }));
  });

  /** The one square in the tab order. Kept inside the board after a resize. */
  protected readonly tabCell = computed<Coordinate>(() => {
    const { rows, cols } = this.board.size();
    const { row, col } = this.focused();
    return { row: Math.min(row, rows - 1), col: Math.min(col, cols - 1) };
  });

  // --- pointer ---------------------------------------------------------------

  protected onPointerDown(event: PointerEvent): void {
    if (event.pointerType === 'mouse' && event.button !== 0) {
      return;
    }
    const cell = this.cellUnder(event);
    if (!cell) {
      return;
    }
    this.activePointer = event.pointerId;
    (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
    this.focused.set(cell);
    this.interaction.beginStroke(cell);
  }

  protected onPointerMove(event: PointerEvent): void {
    if (event.pointerId !== this.activePointer) {
      return;
    }
    this.interaction.continueStroke(this.cellUnder(event));
  }

  protected onPointerEnd(event: PointerEvent): void {
    if (event.pointerId !== this.activePointer) {
      return;
    }
    this.activePointer = null;
    this.interaction.endStroke();
    const grid = event.currentTarget as HTMLElement;
    if (grid.hasPointerCapture?.(event.pointerId)) {
      grid.releasePointerCapture(event.pointerId);
    }
  }

  // --- keyboard and focus ----------------------------------------------------

  protected onFocusIn(event: FocusEvent): void {
    const cell = this.cellOf(event.target);
    if (cell) {
      this.focused.set(cell);
    }
  }

  protected onKeyDown(event: KeyboardEvent): void {
    if (event.altKey || event.metaKey) {
      return;
    }
    const current = this.cellOf(event.target);
    if (!current) {
      return;
    }
    const { rows, cols } = this.board.size();
    let next: Coordinate;
    switch (event.key) {
      case 'ArrowUp':
        next = { row: Math.max(0, current.row - 1), col: current.col };
        break;
      case 'ArrowDown':
        next = { row: Math.min(rows - 1, current.row + 1), col: current.col };
        break;
      case 'ArrowLeft':
        next = { row: current.row, col: Math.max(0, current.col - 1) };
        break;
      case 'ArrowRight':
        next = { row: current.row, col: Math.min(cols - 1, current.col + 1) };
        break;
      case 'Home':
        next = event.ctrlKey ? { row: 0, col: 0 } : { row: current.row, col: 0 };
        break;
      case 'End':
        next = event.ctrlKey ? { row: rows - 1, col: cols - 1 } : { row: current.row, col: cols - 1 };
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        this.interaction.activateCell(current);
        return;
      default:
        return;
    }
    event.preventDefault();
    this.focused.set(next);
    this.gridElement()
      .nativeElement.querySelector<HTMLElement>(`[data-row="${next.row}"][data-col="${next.col}"]`)
      ?.focus();
  }

  // --- helpers ---------------------------------------------------------------

  private cellUnder(event: PointerEvent): Coordinate | null {
    const rect = this.gridElement().nativeElement.getBoundingClientRect();
    return cellAtPoint(rect, this.board.size(), event.clientX, event.clientY);
  }

  private cellOf(target: EventTarget | null): Coordinate | null {
    const element = (target as HTMLElement | null)?.closest?.<HTMLElement>('[data-row]');
    if (!element) {
      return null;
    }
    return { row: Number(element.dataset['row']), col: Number(element.dataset['col']) };
  }
}
