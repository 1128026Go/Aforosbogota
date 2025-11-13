import { useState, useEffect } from 'react';
import { listDatasets, getDatasetInfo, getDatasetStats } from '../api/dataset-editor-api';
import type { DatasetInfo, StatsResponse } from '../types/dataset-editor';

export function useDatasets() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const { datasets: data } = await listDatasets();
      setDatasets(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar datasets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  return { datasets, loading, error, refetch: fetchDatasets };
}

export function useDatasetInfo(datasetId: string) {
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        setLoading(true);
        const data = await getDatasetInfo(datasetId);
        setInfo(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error');
      } finally {
        setLoading(false);
      }
    };
    fetchInfo();
  }, [datasetId]);

  return { info, loading, error };
}

export function useDatasetStats(datasetId: string) {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDatasetStats(datasetId);
        setStats(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [datasetId]);

  return { stats, loading };
}
