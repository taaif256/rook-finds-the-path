import { TestBed } from '@angular/core/testing';

import { Coordinate, cellKey } from '../../core/models';
import { VisualizationStateService } from '../visualization/visualization-state.service';
import { BoardInteractionService } from './board-interaction.service';
import { BoardStateService } from './board-state.service';

const c = (row: number, col: number): Coordinate => ({ row, col });

describe('BoardInteractionService', () => {
  let interaction: BoardInteractionService;
  let board: BoardStateService;
  let visualization: VisualizationStateService;

  /** A complete press-drag-release over the given squares. */
  function stroke(...cells: (Coordinate | null)[]): void {
    const [first, ...rest] = cells;
    interaction.beginStroke(first as Coordinate);
    for (const cell of rest) {
      interaction.continueStroke(cell);
    }
    interaction.endStroke();
  }

  const barrierKeys = () => [...board.barriers()].sort();

  beforeEach(() => {
    interaction = TestBed.inject(BoardInteractionService);
    board = TestBed.inject(BoardStateService);
    visualization = TestBed.inject(VisualizationStateService);
  });

  describe('tools', () => {
    it('starts with the start tool selected', () => {
      expect(interaction.tool()).toBe('start');
    });

    it('selecting a tool changes the tool and its hint', () => {
      interaction.selectTool('barrier');
      expect(interaction.tool()).toBe('barrier');
      expect(interaction.toolHint()).toMatch(/barrier/i);
      interaction.selectTool('unset');
      expect(interaction.toolHint()).toMatch(/clear/i);
    });

    it('selecting a tool dismisses an old notice', () => {
      board.setStart(c(1, 1));
      interaction.selectTool('barrier');
      stroke(c(1, 1));
      expect(interaction.notice()).not.toBeNull();
      interaction.selectTool('end');
      expect(interaction.notice()).toBeNull();
    });
  });

  describe('start and end tools', () => {
    it('places the start with a click and moves it with another', () => {
      stroke(c(2, 2));
      expect(board.start()).toEqual(c(2, 2));
      stroke(c(4, 4));
      expect(board.start()).toEqual(c(4, 4));
      expect(board.kindAt(c(2, 2))).toBe('unset');
    });

    it('lets the marker follow the pointer while dragging', () => {
      stroke(c(1, 1), c(1, 2), c(1, 3), c(2, 3));
      expect(board.start()).toEqual(c(2, 3));
      expect(board.kindAt(c(1, 1))).toBe('unset');
      expect(board.kindAt(c(1, 2))).toBe('unset');
    });

    it('places the end with the end tool', () => {
      interaction.selectTool('end');
      stroke(c(7, 7));
      expect(board.end()).toEqual(c(7, 7));
    });

    it('explains why the end cannot go on the start', () => {
      stroke(c(3, 3));
      interaction.selectTool('end');
      stroke(c(3, 3));
      expect(board.end()).toBeNull();
      expect(interaction.notice()).toBe('Start and end must be different squares.');
    });

    it('keeps explaining when a dragged marker passes over the other marker', () => {
      board.setEnd(c(1, 2));
      stroke(c(1, 1), c(1, 2));
      expect(board.start()).toEqual(c(1, 1));
      expect(interaction.notice()).toBe('Start and end must be different squares.');
      interaction.beginStroke(c(1, 1));
      interaction.continueStroke(c(1, 2));
      interaction.continueStroke(c(1, 3)); // a valid square clears the notice
      interaction.endStroke();
      expect(interaction.notice()).toBeNull();
      expect(board.start()).toEqual(c(1, 3));
    });

    it('replaces a barrier under the start marker', () => {
      board.addBarrier(c(2, 2));
      stroke(c(2, 2));
      expect(board.start()).toEqual(c(2, 2));
      expect(board.barrierCount()).toBe(0);
    });
  });

  describe('barrier tool', () => {
    beforeEach(() => interaction.selectTool('barrier'));

    it('adds a barrier with a click and removes it with another click', () => {
      stroke(c(3, 3));
      expect(barrierKeys()).toEqual([cellKey(c(3, 3))]);
      stroke(c(3, 3));
      expect(board.barrierCount()).toBe(0);
    });

    it('draws every square along a drag', () => {
      stroke(c(2, 0), c(2, 5));
      expect(barrierKeys()).toEqual(['2,0', '2,1', '2,2', '2,3', '2,4', '2,5']);
    });

    it('leaves no gaps when the pointer jumps several squares at once', () => {
      stroke(c(0, 0), c(4, 4));
      expect(barrierKeys()).toEqual(['0,0', '1,1', '2,2', '3,3', '4,4']);
      stroke(c(6, 0), c(6, 1), c(9, 1)); // a jump down a column
      expect(board.isBarrier(c(7, 1))).toBe(true);
      expect(board.isBarrier(c(8, 1))).toBe(true);
    });

    it('a stroke that starts on empty only adds, even across existing barriers', () => {
      board.addBarrier(c(1, 2));
      stroke(c(1, 0), c(1, 4));
      expect(barrierKeys()).toEqual(['1,0', '1,1', '1,2', '1,3', '1,4']);
    });

    it('a stroke that starts on a barrier only removes', () => {
      for (const col of [0, 1, 2, 4]) {
        board.addBarrier(c(1, col));
      }
      stroke(c(1, 0), c(1, 4));
      expect(board.barrierCount()).toBe(0);
      expect(board.isBarrier(c(1, 3))).toBe(false); // the gap stayed empty, it was not toggled on
    });

    it('draws across start and end without touching them or complaining', () => {
      board.setStart(c(2, 1));
      board.setEnd(c(2, 3));
      stroke(c(2, 0), c(2, 4));
      expect(board.start()).toEqual(c(2, 1));
      expect(board.end()).toEqual(c(2, 3));
      expect(barrierKeys()).toEqual(['2,0', '2,2', '2,4']);
      expect(interaction.notice()).toBeNull();
    });

    it('explains the refusal when pressing directly on start or end', () => {
      board.setStart(c(2, 1));
      board.setEnd(c(5, 5));
      stroke(c(2, 1));
      expect(interaction.notice()).toBe("The start square can't be a barrier. Move the start first.");
      stroke(c(5, 5));
      expect(interaction.notice()).toBe("The end square can't be a barrier. Move the end first.");
      expect(board.barrierCount()).toBe(0);
    });

    it('does not connect two stretches of a stroke across a gap off the board', () => {
      stroke(c(0, 0), null, c(0, 5));
      expect(barrierKeys()).toEqual(['0,0', '0,5']);
    });

    it('ignores movement when no stroke is in progress', () => {
      interaction.continueStroke(c(1, 1));
      expect(board.barrierCount()).toBe(0);
      stroke(c(0, 0));
      interaction.continueStroke(c(0, 3)); // after the release
      expect(barrierKeys()).toEqual(['0,0']);
    });

    it('finishes a stroke with the tool it began with', () => {
      interaction.beginStroke(c(0, 0));
      interaction.selectTool('unset');
      interaction.continueStroke(c(0, 2));
      interaction.endStroke();
      expect(barrierKeys()).toEqual(['0,0', '0,1', '0,2']);
    });
  });

  describe('unset tool', () => {
    beforeEach(() => {
      board.setStart(c(3, 0));
      board.setEnd(c(3, 4));
      for (const col of [1, 2, 3]) {
        board.addBarrier(c(3, col));
      }
      for (const col of [0, 4]) {
        board.addBarrier(c(5, col));
      }
      interaction.selectTool('unset');
    });

    it('clears a barrier with a click', () => {
      stroke(c(5, 0));
      expect(board.isBarrier(c(5, 0))).toBe(false);
      expect(board.isBarrier(c(5, 4))).toBe(true);
    });

    it('clears the start or end when it is clicked directly', () => {
      stroke(c(3, 0));
      expect(board.start()).toBeNull();
      stroke(c(3, 4));
      expect(board.end()).toBeNull();
    });

    it('clears barriers along a drag but never removes start or end by accident', () => {
      stroke(c(2, 0), c(3, 0), c(3, 1), c(3, 2), c(3, 3), c(3, 4), c(4, 4), c(5, 4));
      expect(board.start()).toEqual(c(3, 0));
      expect(board.end()).toEqual(c(3, 4));
      expect(barrierKeys()).toEqual(['5,0']);
    });

    it('a drag that begins on the start clears it on purpose, then keeps going carefully', () => {
      stroke(c(3, 0), c(3, 1), c(3, 4));
      expect(board.start()).toBeNull();
      expect(board.end()).toEqual(c(3, 4));
    });
  });

  describe('keyboard activation', () => {
    it('applies the selected tool once, like a click', () => {
      interaction.selectTool('barrier');
      interaction.activateCell(c(1, 1));
      expect(board.isBarrier(c(1, 1))).toBe(true);
      interaction.continueStroke(c(1, 5)); // no stroke is left open
      expect(board.barrierCount()).toBe(1);
    });
  });

  describe('visualization stays in step with the board', () => {
    beforeEach(() => visualization.mark(c(9, 9), 'closed'));

    it('is cleared when an edit changes the board', () => {
      interaction.selectTool('barrier');
      stroke(c(1, 1));
      expect(visualization.isEmpty()).toBe(true);
    });

    it('is kept when an action changes nothing', () => {
      interaction.selectTool('unset');
      stroke(c(1, 1)); // already unset
      expect(visualization.isEmpty()).toBe(false);
    });

    it('is kept when an action is refused', () => {
      board.setStart(c(1, 1));
      visualization.mark(c(9, 9), 'closed');
      interaction.selectTool('barrier');
      stroke(c(1, 1));
      expect(visualization.isEmpty()).toBe(false);
    });
  });

  describe('board-wide actions', () => {
    beforeEach(() => {
      board.setStart(c(0, 0));
      board.setEnd(c(5, 5));
      board.addBarrier(c(2, 2));
      visualization.mark(c(1, 1), 'open');
    });

    it('clearVisualization removes the drawing and keeps the board', () => {
      const config = board.config();
      const revision = board.revision();
      interaction.clearVisualization();
      expect(visualization.isEmpty()).toBe(true);
      expect(board.config()).toEqual(config);
      expect(board.revision()).toBe(revision);
    });

    it('resetBoard clears the board and the drawing but keeps the size', () => {
      board.resize(10, 10);
      board.setStart(c(0, 0));
      visualization.mark(c(1, 1), 'open');
      interaction.resetBoard();
      expect(board.isBlank()).toBe(true);
      expect(board.size()).toEqual({ rows: 10, cols: 10 });
      expect(visualization.isEmpty()).toBe(true);
    });

    it('resetBoard clears a stale drawing even when the board is already blank', () => {
      board.reset();
      visualization.mark(c(1, 1), 'open');
      interaction.resetBoard();
      expect(visualization.isEmpty()).toBe(true);
    });

    it('resizeBoard switches to a square board of that size and clears everything', () => {
      interaction.resizeBoard(30);
      expect(board.size()).toEqual({ rows: 30, cols: 30 });
      expect(board.isBlank()).toBe(true);
      expect(visualization.isEmpty()).toBe(true);
    });

    it('choosing the current size again keeps the board', () => {
      interaction.resizeBoard(20);
      expect(board.start()).toEqual(c(0, 0));
      expect(board.barrierCount()).toBe(1);
    });
  });
});
