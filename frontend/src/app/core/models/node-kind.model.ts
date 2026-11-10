import { NodeKind, Tool } from './board.models';

export interface NodeKindInfo {
  /** Short name, also used for screen readers. */
  label: string;
  /** One-line meaning, shown in the legend. */
  description: string;
}

export const NODE_KIND_INFO: Record<NodeKind, NodeKindInfo> = {
  unset: { label: 'Empty', description: 'A free square the robot can cross.' },
  start: { label: 'Start', description: 'Where the robot begins. There is only one.' },
  end: { label: 'End', description: 'The destination. There is only one.' },
  barrier: { label: 'Barrier', description: 'An obstacle the robot cannot cross.' },
  open: { label: 'Open', description: 'Discovered by the search and waiting to be explored.' },
  closed: { label: 'Closed', description: 'Already explored by the search.' },
  path: { label: 'Path', description: 'The route found from start to end.' },
};

/** Legend order: what you place first, then what the search draws. */
export const NODE_KIND_ORDER: readonly NodeKind[] = ['unset', 'start', 'end', 'barrier', 'open', 'closed', 'path'];

export interface ToolInfo {
  id: Tool;
  label: string;
  hint: string;
}

export const TOOLS: readonly ToolInfo[] = [
  { id: 'start', label: 'Start', hint: 'Click a square to place the robot. Drag to move it.' },
  { id: 'end', label: 'End', hint: 'Click a square to place the destination. Drag to move it.' },
  { id: 'barrier', label: 'Barrier', hint: 'Click or drag to draw barriers. Start on a barrier to remove them.' },
  { id: 'unset', label: 'Unset', hint: 'Click a square to clear it. Dragging leaves start and end alone.' },
];
