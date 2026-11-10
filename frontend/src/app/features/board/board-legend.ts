import { Component } from '@angular/core';

import { NODE_KIND_INFO, NODE_KIND_ORDER } from '../../core/models';

/** What each square colour means. */
@Component({
  selector: 'app-board-legend',
  templateUrl: './board-legend.html',
  styleUrl: './board-legend.scss',
})
export class BoardLegend {
  protected readonly items = NODE_KIND_ORDER.map((kind) => ({ kind, ...NODE_KIND_INFO[kind] }));
}
