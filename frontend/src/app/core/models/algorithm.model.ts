import { AlgorithmId } from './pathfinding-api.models';

export interface AlgorithmInfo {
  id: AlgorithmId;
  label: string;
  summary: string;
}

export const ALGORITHMS: readonly AlgorithmInfo[] = [
  {
    id: 'astar',
    label: 'A*',
    summary: 'Weighs the distance travelled against the distance left. Always finds a shortest path.',
  },
  {
    id: 'gbfs',
    label: 'Greedy Best-First',
    summary: 'Always heads for the square that looks closest to the end. Often quick, but the path it finds is not guaranteed to be the shortest.',
  },
];

export function algorithmLabel(id: AlgorithmId): string {
  return ALGORITHMS.find((algorithm) => algorithm.id === id)?.label ?? id;
}
