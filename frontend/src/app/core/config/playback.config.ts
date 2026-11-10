export type SpeedId = 'slow' | 'normal' | 'fast' | 'turbo';

export interface SpeedOption {
  id: SpeedId;
  label: string;
  /** Search events drawn per second. */
  stepsPerSecond: number;
}

/** A big board can produce a few thousand events, hence the fast end. */
export const PLAYBACK_SPEEDS: readonly SpeedOption[] = [
  { id: 'slow', label: 'Slow', stepsPerSecond: 8 },
  { id: 'normal', label: 'Normal', stepsPerSecond: 30 },
  { id: 'fast', label: 'Fast', stepsPerSecond: 120 },
  { id: 'turbo', label: 'Turbo', stepsPerSecond: 600 },
];

export const DEFAULT_SPEED: SpeedId = 'normal';
