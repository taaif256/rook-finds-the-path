import { OverlayKind } from '../../core/models';
import { displayKind, shadeOf } from './board-display';

describe('displayKind', () => {
  it('shows the search overlay on squares the user left unset', () => {
    for (const overlay of ['open', 'closed', 'path'] as OverlayKind[]) {
      expect(displayKind('unset', overlay)).toBe(overlay);
    }
    expect(displayKind('unset', undefined)).toBe('unset');
  });

  it('never lets the overlay hide start, end or barriers', () => {
    for (const board of ['start', 'end', 'barrier'] as const) {
      for (const overlay of ['open', 'closed', 'path', undefined] as const) {
        expect(displayKind(board, overlay)).toBe(board);
      }
    }
  });
});

describe('shadeOf', () => {
  it('alternates like a chessboard, starting light in the top-left', () => {
    expect(shadeOf(0, 0)).toBe('light');
    expect(shadeOf(0, 1)).toBe('dark');
    expect(shadeOf(1, 0)).toBe('dark');
    expect(shadeOf(1, 1)).toBe('light');
    expect(shadeOf(7, 12)).toBe('dark');
  });
});
