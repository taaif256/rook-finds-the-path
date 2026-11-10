import { Injectable, signal } from '@angular/core';

import { AlgorithmId } from '../../core/models';

/** Which algorithm the next search will use. */
@Injectable({ providedIn: 'root' })
export class AlgorithmSelectionService {
  private readonly selected = signal<AlgorithmId>('astar');

  readonly algorithm = this.selected.asReadonly();

  select(id: AlgorithmId): void {
    this.selected.set(id);
  }
}
