import { useState, useEffect } from 'react';
import { getEvents, updateEvent, deleteEvent } from '../api/dataset-editor-api';
import type { TrajectoryEvent, EventFilters, EventUpdate } from '../types/dataset-editor';

export function useEvents(datasetId: string | undefined, filters?: EventFilters) {
  const [events, setEvents] = useState<TrajectoryEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = async () => {
    if (!datasetId) {
      setLoading(false);
      setEvents([]);
      setTotal(0);
      setError('No dataset ID provided');
      return;
    }

    try {
      setLoading(true);
      const response = await getEvents(datasetId, filters);
      setEvents(response.events);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar eventos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [datasetId, JSON.stringify(filters)]);

  const handleUpdateEvent = async (trackId: string | number, updates: EventUpdate) => {
    if (!datasetId) return;
    await updateEvent(datasetId, trackId, updates);
    await fetchEvents();
  };

  const handleDeleteEvent = async (trackId: string | number) => {
    if (!datasetId) return;
    await deleteEvent(datasetId, trackId);
    await fetchEvents();
  };

  return { events, total, loading, error, refetch: fetchEvents, updateEvent: handleUpdateEvent, deleteEvent: handleDeleteEvent };
}
