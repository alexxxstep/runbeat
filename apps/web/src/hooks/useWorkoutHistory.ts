import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface WorkoutHistoryItem {
  id: string;
  user_id: string;
  type: string;
  duration_minutes: number;
  intensity: string;
  hr_zones: number[];
  genres?: string[];
  interval_stages?: Array<{
    name: string;
    duration_minutes: number;
    hr_zone: [number, number];
    bpm_range: [number, number];
  }>;
  prompt?: string;
  completed_at?: string;
  created_at: string;
}

export function useWorkoutHistory(userId?: string) {
  const [workouts, setWorkouts] = useState<WorkoutHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      return;
    }

    const fetchHistory = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await api.getWorkouts(userId);
        setWorkouts(response.workouts || []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load workouts'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId]);

  const deleteWorkout = async (workoutId: string) => {
    if (!userId) {
      return;
    }

    try {
      await api.deleteWorkout(workoutId, userId);
      // Remove from local state
      setWorkouts((prev) => prev.filter((w) => w.id !== workoutId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete workout');
      throw err;
    }
  };

  const refresh = async () => {
    if (!userId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.getWorkouts(userId);
      setWorkouts(response.workouts || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workouts');
    } finally {
      setLoading(false);
    }
  };

  return { workouts, loading, error, deleteWorkout, refresh };
}
