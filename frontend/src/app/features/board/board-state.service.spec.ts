import { TestBed } from '@angular/core/testing';

import { Coordinate } from '../../core/models';
import { BoardStateService } from './board-state.service';

const c = (row: number, col: number): Coordinate => ({ row, col });

describe('BoardStateService', () => {
  let board: BoardStateService;

  beforeEach(() => {
    board = TestBed.inject(BoardStateService);
  });

  describe('initial state', () => {
    it('starts as an empty 20 x 20 board', () => {
      expect(board.size()).toEqual({ rows: 20, cols: 20 });
      expect(board.start()).toBeNull();
      expect(board.end()).toBeNull();
      expect(board.barrierCount()).toBe(0);
      expect(board.isBlank()).toBe(true);
      expect(board.revision()).toBe(0);
    });

    it('treats every square as unset', () => {
      expect(board.kindAt(c(0, 0))).toBe('unset');
      expect(board.kindAt(c(19, 19))).toBe('unset');
    });
  });

  describe('start and end', () => {
    it('places the start and the end', () => {
      expect(board.setStart(c(1, 2)).status).toBe('changed');
      expect(board.setEnd(c(5, 6)).status).toBe('changed');
      expect(board.start()).toEqual(c(1, 2));
      expect(board.end()).toEqual(c(5, 6));
      expect(board.kindAt(c(1, 2))).toBe('start');
      expect(board.kindAt(c(5, 6))).toBe('end');
    });

    it('moves the start instead of adding a second one', () => {
      board.setStart(c(1, 1));
      board.setStart(c(3, 3));
      expect(board.start()).toEqual(c(3, 3));
      expect(board.kindAt(c(1, 1))).toBe('unset');
    });

    it('moves the end instead of adding a second one', () => {
      board.setEnd(c(1, 1));
      board.setEnd(c(3, 3));
      expect(board.end()).toEqual(c(3, 3));
      expect(board.kindAt(c(1, 1))).toBe('unset');
    });

    it('reports no change when the marker is already there', () => {
      board.setStart(c(1, 1));
      const revision = board.revision();
      expect(board.setStart(c(1, 1)).status).toBe('unchanged');
      expect(board.revision()).toBe(revision);
    });

    it('replaces a barrier when the start or end is placed on it', () => {
      board.addBarrier(c(2, 2));
      board.addBarrier(c(4, 4));
      expect(board.setStart(c(2, 2)).status).toBe('changed');
      expect(board.setEnd(c(4, 4)).status).toBe('changed');
      expect(board.barrierCount()).toBe(0);
      expect(board.isBarrier(c(2, 2))).toBe(false);
      expect(board.kindAt(c(2, 2))).toBe('start');
      expect(board.kindAt(c(4, 4))).toBe('end');
    });

    it('refuses to put start and end on the same square', () => {
      board.setStart(c(1, 1));
      board.setEnd(c(2, 2));
      const revision = board.revision();

      expect(board.setStart(c(2, 2))).toEqual({ status: 'rejected', reason: 'start-on-end' });
      expect(board.setEnd(c(1, 1))).toEqual({ status: 'rejected', reason: 'end-on-start' });
      expect(board.start()).toEqual(c(1, 1));
      expect(board.end()).toEqual(c(2, 2));
      expect(board.revision()).toBe(revision);
    });

    it('keeps its own copy of the coordinate it was given', () => {
      const cell = c(1, 1);
      board.setStart(cell);
      cell.row = 9;
      expect(board.start()).toEqual(c(1, 1));
    });
  });

  describe('barriers', () => {
    it('adds and removes barriers', () => {
      expect(board.addBarrier(c(3, 3)).status).toBe('changed');
      expect(board.isBarrier(c(3, 3))).toBe(true);
      expect(board.kindAt(c(3, 3))).toBe('barrier');
      expect(board.barrierCount()).toBe(1);

      expect(board.removeBarrier(c(3, 3)).status).toBe('changed');
      expect(board.isBarrier(c(3, 3))).toBe(false);
      expect(board.barrierCount()).toBe(0);
    });

    it('does nothing when adding an existing barrier or removing a missing one', () => {
      board.addBarrier(c(3, 3));
      const revision = board.revision();
      expect(board.addBarrier(c(3, 3)).status).toBe('unchanged');
      expect(board.removeBarrier(c(0, 0)).status).toBe('unchanged');
      expect(board.revision()).toBe(revision);
      expect(board.barrierCount()).toBe(1);
    });

    it('never lets the start or end become a barrier', () => {
      board.setStart(c(1, 1));
      board.setEnd(c(2, 2));
      const revision = board.revision();

      expect(board.addBarrier(c(1, 1))).toEqual({ status: 'rejected', reason: 'barrier-on-start' });
      expect(board.addBarrier(c(2, 2))).toEqual({ status: 'rejected', reason: 'barrier-on-end' });
      expect(board.barrierCount()).toBe(0);
      expect(board.kindAt(c(1, 1))).toBe('start');
      expect(board.revision()).toBe(revision);
    });

    it('does not touch start or end when removing a barrier there', () => {
      board.setStart(c(1, 1));
      expect(board.removeBarrier(c(1, 1)).status).toBe('unchanged');
      expect(board.start()).toEqual(c(1, 1));
    });
  });

  describe('clearCell (unset)', () => {
    beforeEach(() => {
      board.setStart(c(0, 0));
      board.setEnd(c(9, 9));
      board.addBarrier(c(5, 5));
    });

    it('clears a barrier', () => {
      expect(board.clearCell(c(5, 5)).status).toBe('changed');
      expect(board.isBarrier(c(5, 5))).toBe(false);
    });

    it('clears the start or end when asked directly', () => {
      expect(board.clearCell(c(0, 0)).status).toBe('changed');
      expect(board.start()).toBeNull();
      expect(board.clearCell(c(9, 9)).status).toBe('changed');
      expect(board.end()).toBeNull();
    });

    it('leaves the start and end alone when told to keep endpoints', () => {
      expect(board.clearCell(c(0, 0), { keepEndpoints: true }).status).toBe('unchanged');
      expect(board.clearCell(c(9, 9), { keepEndpoints: true }).status).toBe('unchanged');
      expect(board.start()).toEqual(c(0, 0));
      expect(board.end()).toEqual(c(9, 9));
      expect(board.clearCell(c(5, 5), { keepEndpoints: true }).status).toBe('changed');
    });

    it('does nothing to an already unset square', () => {
      const revision = board.revision();
      expect(board.clearCell(c(3, 3)).status).toBe('unchanged');
      expect(board.revision()).toBe(revision);
    });
  });

  describe('bounds', () => {
    it('rejects squares outside the board for every edit', () => {
      const outside = [c(-1, 0), c(0, -1), c(20, 0), c(0, 20), c(1.5, 1), c(Number.NaN, 0)];
      for (const cell of outside) {
        const expected = { status: 'rejected', reason: 'out-of-bounds' };
        expect(board.setStart(cell)).toEqual(expected);
        expect(board.setEnd(cell)).toEqual(expected);
        expect(board.addBarrier(cell)).toEqual(expected);
        expect(board.removeBarrier(cell)).toEqual(expected);
        expect(board.clearCell(cell)).toEqual(expected);
      }
      expect(board.isBlank()).toBe(true);
      expect(board.revision()).toBe(0);
    });

    it('accepts the corners of the board', () => {
      expect(board.setStart(c(0, 0)).status).toBe('changed');
      expect(board.setEnd(c(19, 19)).status).toBe('changed');
      expect(board.addBarrier(c(0, 19)).status).toBe('changed');
      expect(board.addBarrier(c(19, 0)).status).toBe('changed');
    });
  });

  describe('resize and reset', () => {
    beforeEach(() => {
      board.setStart(c(0, 0));
      board.setEnd(c(5, 5));
      board.addBarrier(c(2, 2));
    });

    it('changing the size clears the board', () => {
      expect(board.resize(10, 10).status).toBe('changed');
      expect(board.size()).toEqual({ rows: 10, cols: 10 });
      expect(board.isBlank()).toBe(true);
    });

    it('keeps the board when the size is unchanged', () => {
      const revision = board.revision();
      expect(board.resize(20, 20).status).toBe('unchanged');
      expect(board.start()).toEqual(c(0, 0));
      expect(board.barrierCount()).toBe(1);
      expect(board.revision()).toBe(revision);
    });

    it('applies the new bounds after resizing', () => {
      board.resize(10, 10);
      expect(board.setStart(c(10, 0)).status).toBe('rejected');
      expect(board.setStart(c(9, 9)).status).toBe('changed');
    });

    it('rejects sizes the API would refuse', () => {
      for (const bad of [0, -1, 51, 1.5, Number.NaN]) {
        expect(() => board.resize(bad, 10)).toThrow(RangeError);
        expect(() => board.resize(10, bad)).toThrow(RangeError);
      }
      expect(board.size()).toEqual({ rows: 20, cols: 20 });
    });

    it('accepts the smallest and largest supported sizes', () => {
      expect(board.resize(1, 50).status).toBe('changed');
      expect(board.size()).toEqual({ rows: 1, cols: 50 });
      expect(board.resize(50, 1).status).toBe('changed');
    });

    it('reset removes start, end and barriers but keeps the size', () => {
      board.resize(30, 30);
      board.setStart(c(1, 1));
      board.addBarrier(c(2, 2));
      expect(board.reset().status).toBe('changed');
      expect(board.isBlank()).toBe(true);
      expect(board.size()).toEqual({ rows: 30, cols: 30 });
    });

    it('reset on a blank board changes nothing', () => {
      board.reset();
      const revision = board.revision();
      expect(board.reset().status).toBe('unchanged');
      expect(board.revision()).toBe(revision);
    });
  });

  describe('revision', () => {
    it('goes up by one for each real change and only then', () => {
      expect(board.revision()).toBe(0);
      board.setStart(c(0, 0));
      expect(board.revision()).toBe(1);
      board.addBarrier(c(1, 1));
      expect(board.revision()).toBe(2);
      board.addBarrier(c(1, 1)); // no change
      board.setStart(c(0, 0)); // no change
      expect(board.revision()).toBe(2);
      board.reset();
      expect(board.revision()).toBe(3);
    });
  });

  describe('config (what the API needs)', () => {
    it('describes the whole board with barriers in a stable order', () => {
      board.resize(10, 10);
      board.setStart(c(0, 0));
      board.setEnd(c(9, 9));
      board.addBarrier(c(4, 3));
      board.addBarrier(c(2, 3));
      board.addBarrier(c(2, 1));

      expect(board.config()).toEqual({
        rows: 10,
        cols: 10,
        start: c(0, 0),
        end: c(9, 9),
        barriers: [c(2, 1), c(2, 3), c(4, 3)],
      });
    });

    it('reports a missing start or end as null', () => {
      expect(board.config().start).toBeNull();
      expect(board.config().end).toBeNull();
      expect(board.config().barriers).toEqual([]);
    });
  });
});
