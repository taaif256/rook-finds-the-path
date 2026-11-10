import { TestBed } from '@angular/core/testing';

import { BoardStateService } from '../board/board-state.service';
import { VisualizationStateService } from './visualization-state.service';

describe('VisualizationStateService', () => {
  let visualization: VisualizationStateService;

  beforeEach(() => {
    visualization = TestBed.inject(VisualizationStateService);
  });

  it('starts empty', () => {
    expect(visualization.isEmpty()).toBe(true);
    expect(visualization.overlay().size).toBe(0);
  });

  it('records what the search has drawn, one kind per square', () => {
    visualization.mark({ row: 1, col: 1 }, 'open');
    visualization.mark({ row: 1, col: 2 }, 'closed');
    visualization.mark({ row: 1, col: 1 }, 'closed'); // an open square gets explored
    visualization.mark({ row: 1, col: 3 }, 'path');

    expect(visualization.isEmpty()).toBe(false);
    expect(visualization.overlay().get('1,1')).toBe('closed');
    expect(visualization.overlay().get('1,2')).toBe('closed');
    expect(visualization.overlay().get('1,3')).toBe('path');
    expect(visualization.overlay().size).toBe(3);
  });

  it('clears everything', () => {
    visualization.mark({ row: 0, col: 0 }, 'open');
    visualization.clear();
    expect(visualization.isEmpty()).toBe(true);
    expect(visualization.overlay().size).toBe(0);
  });

  it('can be cleared when already empty', () => {
    expect(() => visualization.clear()).not.toThrow();
    expect(visualization.isEmpty()).toBe(true);
  });

  it('is independent of the board: clearing it leaves the board configuration alone', () => {
    const board = TestBed.inject(BoardStateService);
    board.setStart({ row: 0, col: 0 });
    board.setEnd({ row: 5, col: 5 });
    board.addBarrier({ row: 2, col: 2 });
    const before = board.config();

    visualization.mark({ row: 1, col: 1 }, 'open');
    visualization.clear();

    expect(board.config()).toEqual(before);
    expect(board.revision()).toBe(3);
  });
});
