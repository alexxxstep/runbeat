/**
 * Types for workout settings
 */

export type WorkoutType = 'steady' | 'progressive' | 'intervals' | 'fartlek';

export type Intensity = 'low' | 'moderate' | 'high';

export interface IntervalStage {
  id: string;
  name: string;
  durationMinutes: number;
  hrZone: [number, number];
  bpmRange: [number, number];
}

export interface WorkoutSettings {
  type: WorkoutType;
  durationMinutes: number;
  intensity: Intensity;
  hrZones: [number, number];
  genres: string[];
  intervalStages?: IntervalStage[];
}
