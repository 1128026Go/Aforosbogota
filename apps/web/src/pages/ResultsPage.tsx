import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "@/lib/api";
import {
  AnalysisSettings,
  VolumesResponse,
  SpeedsResponse,
  ConflictsResponse,
  ViolationsResponse,
  VolumeRow,
  ConflictEvent,
  ForbiddenMovement,
  QcSummary,
} from "@/types";
import {
  LineChart,
  Line,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  LabelList,
} from "recharts";

type TabId =
  | "volumes"
  | "speeds"
  | "conflicts"
  | "violations"
  | "settings"
  | "downloads"
  | "diagnostics";

type ResourceState<T> = {
  loading: boolean;
  error: string | null;
  status?: number;
  data: T | null;
};

const createInitialState = <T,>(): ResourceState<T> => ({
  loading: true,
  error: null,
  status: undefined,
  data: null,
});

type VolumeColumns = Record<keyof VolumeRow, boolean>;

type DownloadState = "idle" | "loading";

type ForbiddenFormAction = "input" | "save";

const SERIES_COLORS: Record<string, string> = {
  total: "#1d4ed8",
  autos: "#2563eb",
  buses: "#7c3aed",
  camiones: "#9333ea",
  motos: "#f97316",
  bicis: "#0ea5e9",
  peatones: "#ef4444",
};

const SPEED_BAR_COLORS = {
  mean: "#2563eb",
  p85: "#f97316",
};

const DEFAULT_SETTINGS: AnalysisSettings = {
  interval_minutes: 15,
  min_length_m: 5,
  max_direction_changes: 20,
  min_net_over_path_ratio: 0.2,
  ttc_threshold_s: 1.5,
};

const sanitizeDatasetId = (value?: string | null) =>
  value && value !== "undefined" ? value : undefined;

const formatNumber = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 2,
});

const stringifyForbidden = (items: ForbiddenMovement[]): string =>
  items
    .map((item) =>
      item.description && item.description.trim().length > 0
        ? `${item.rilsa_code}:${item.description}`
        : item.rilsa_code
    )
    .join("\n");

const parseForbiddenInput = (raw: string): ForbiddenMovement[] => {
  const map = new Map<string, string | undefined>();
  raw
    .split(/\n|,/) // soporta comas o saltos de línea
    .map((value) => value.trim())
    .filter(Boolean)
    .forEach((entry) => {
      const [codeRaw, ...rest] = entry.split(":");
      const normalizedCode = (codeRaw ?? "").trim();
      if (!normalizedCode) return;
      const description = rest.join(":").trim();
      map.set(normalizedCode, description.length > 0 ? description : undefined);
    });
  return Array.from(map.entries()).map(([rilsa_code, description]) => ({ rilsa_code, description }));
};

const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const { datasetId: routeDatasetId } = useParams<{ datasetId: string }>();
  const datasetId = sanitizeDatasetId(routeDatasetId);
  useEffect(() => {
    if (!datasetId) {
      navigate("/datasets/upload", { replace: true });
    }
  }, [datasetId, navigate]);

  const [activeTab, setActiveTab] = useState<TabId>("volumes");
  const [analysisSettings, setAnalysisSettings] = useState<AnalysisSettings | null>(null);
  const [settingsDraft, setSettingsDraft] = useState<AnalysisSettings | null>(null);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [volumesState, setVolumesState] = useState<ResourceState<VolumesResponse>>(createInitialState<VolumesResponse>());
  const [speedsState, setSpeedsState] = useState<ResourceState<SpeedsResponse>>(createInitialState<SpeedsResponse>());
  const [conflictsState, setConflictsState] = useState<ResourceState<ConflictsResponse>>(createInitialState<ConflictsResponse>());
  const [violationsState, setViolationsState] = useState<ResourceState<ViolationsResponse>>(createInitialState<ViolationsResponse>());
  const [qcState, setQcState] = useState<ResourceState<QcSummary>>(createInitialState<QcSummary>());
  const [forbiddenInput, setForbiddenInput] = useState("");
  const [forbiddenSaving, setForbiddenSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadState, setDownloadState] = useState<DownloadState>("idle");
  const [downloadMessage, setDownloadMessage] = useState<string | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<VolumeColumns>({
    interval_start: true,
    interval_end: true,
    autos: true,
    buses: true,
    camiones: true,
    motos: true,
    bicis: true,
    peatones: true,
    total: true,
  });
  const [conflictFilters, setConflictFilters] = useState<Record<string, boolean>>({});
  const [ttcFilter, setTtcFilter] = useState<number>(DEFAULT_SETTINGS.ttc_threshold_s);

  const initializeFilters = useCallback((events: ConflictEvent[]) => {
    const filters: Record<string, boolean> = {};
    events.forEach((evt) => {
      filters[evt.pair_type] = true;
    });
    setConflictFilters(filters);
  }, []);

  const parseApiError = (err: unknown): { message: string; status?: number } => {
    if (err && typeof err === "object") {
      const apiError = err as { detail?: string; message?: string; status?: number };
      return {
        message: apiError.detail || apiError.message || "Error inesperado",
        status: typeof apiError.status === "number" ? apiError.status : undefined,
      };
    }
    if (err instanceof Error) {
      return { message: err.message, status: undefined };
    }
    return { message: "Error inesperado", status: undefined };
  };

  const fetchVolumes = useCallback(async () => {
    if (!datasetId) return;
    setVolumesState((prev) => ({ ...prev, loading: true, error: null, status: undefined }));
    try {
      const data = await api.getVolumes(datasetId);
      setVolumesState({ loading: false, error: null, status: undefined, data });
    } catch (err) {
      const { message, status } = parseApiError(err);
      setVolumesState({ loading: false, error: message, status, data: null });
    }
  }, [datasetId]);

  const fetchSpeeds = useCallback(async () => {
    if (!datasetId) return;
    setSpeedsState((prev) => ({ ...prev, loading: true, error: null, status: undefined }));
    try {
      const data = await api.getSpeeds(datasetId);
      setSpeedsState({ loading: false, error: null, status: undefined, data });
    } catch (err) {
      const { message, status } = parseApiError(err);
      setSpeedsState({ loading: false, error: message, status, data: null });
    }
  }, [datasetId]);

  const fetchConflicts = useCallback(async () => {
    if (!datasetId) return;
    setConflictsState((prev) => ({ ...prev, loading: true, error: null, status: undefined }));
    try {
      const data = await api.getConflicts(datasetId);
      setConflictsState({ loading: false, error: null, status: undefined, data });
      if (data?.events?.length) {
        initializeFilters(data.events);
      } else {
        setConflictFilters({});
      }
    } catch (err) {
      const { message, status } = parseApiError(err);
      setConflictsState({ loading: false, error: message, status, data: null });
      setConflictFilters({});
    }
  }, [datasetId, initializeFilters]);

  const fetchViolations = useCallback(async () => {
    if (!datasetId) return;
    setViolationsState((prev) => ({ ...prev, loading: true, error: null, status: undefined }));
    try {
      const data = await api.getViolations(datasetId);
      setViolationsState({ loading: false, error: null, status: undefined, data });
    } catch (err) {
      const { message, status } = parseApiError(err);
      setViolationsState({ loading: false, error: message, status, data: null });
    }
  }, [datasetId]);

  const fetchQcSummary = useCallback(async () => {
    if (!datasetId) return;
    setQcState((prev) => ({ ...prev, loading: true, error: null, status: undefined }));
    try {
      const data = await api.getQcSummary(datasetId);
      setQcState({ loading: false, error: null, status: undefined, data });
    } catch (err) {
      const { message, status } = parseApiError(err);
      setQcState({ loading: false, error: message, status, data: null });
    }
  }, [datasetId]);

  const refreshAnalysis = useCallback(async () => {
    if (!datasetId) return;
    await Promise.all([
      fetchVolumes(),
      fetchSpeeds(),
      fetchConflicts(),
      fetchViolations(),
      fetchQcSummary(),
    ]);
  }, [datasetId, fetchVolumes, fetchSpeeds, fetchConflicts, fetchViolations, fetchQcSummary]);

  const loadAll = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const [settingsData, forbiddenData] = await Promise.all([
        api.getAnalysisSettings(datasetId),
        api.getForbiddenMovements(datasetId),
      ]);
      setAnalysisSettings(settingsData);
      setSettingsDraft(settingsData);
      setTtcFilter(settingsData.ttc_threshold_s);
      setForbiddenInput(stringifyForbidden(forbiddenData));
    } catch (err) {
      const { message } = parseApiError(err);
      setError(message);
    }
    await Promise.all([
      fetchVolumes(),
      fetchSpeeds(),
      fetchConflicts(),
      fetchViolations(),
      fetchQcSummary(),
    ]);
    setLoading(false);
  }, [datasetId, fetchVolumes, fetchSpeeds, fetchConflicts, fetchViolations, fetchQcSummary]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const filteredConflictEvents = useMemo(() => {
    if (!conflictsState.data) return [];
    return conflictsState.data.events.filter(
      (event) => conflictFilters[event.pair_type] && event.ttc_min <= ttcFilter
    );
  }, [conflictsState.data, conflictFilters, ttcFilter]);

  const maxSpeedValue = useMemo(() => {
    if (!speedsState.data) return 1;
    return speedsState.data.per_movement.reduce(
      (max, record) => Math.max(max, record.stats.p85_kmh, record.stats.max_kmh),
      1
    );
  }, [speedsState.data]);

  const handleDownload = async (type: "csv" | "excel" | "pdf") => {
    if (!datasetId) return;
    setDownloadState("loading");
    setDownloadMessage(null);
    try {
      let fileName: string;
      if (type === "csv") {
        fileName = await api.requestCsvReport(datasetId);
      } else if (type === "excel") {
        fileName = await api.requestExcelReport(datasetId);
      } else {
        fileName = await api.requestPdfReport(datasetId);
      }
      const blob = await api.downloadReport(datasetId, fileName);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = fileName;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setDownloadMessage(`Descarga lista: ${fileName}`);
    } catch (err) {
      setDownloadMessage(`Error: ${(err as Error).message}`);
    } finally {
      setDownloadState("idle");
    }
  };

  const toggleColumn = (column: keyof VolumeRow) => {
    setVisibleColumns((prev) => ({
      ...prev,
      [column]: !prev[column],
    }));
  };

  const toggleConflictFilter = (pairType: string) => {
    setConflictFilters((prev) => ({
      ...prev,
      [pairType]: !prev[pairType],
    }));
  };

  const handleSettingsDraft = <K extends keyof AnalysisSettings>(
    key: K,
    value: AnalysisSettings[K]
  ) => {
    setSettingsDraft((prev) => (prev ? { ...prev, [key]: value } : { ...DEFAULT_SETTINGS, [key]: value }));
  };

  const handleSaveSettings = async () => {
    if (!datasetId || !settingsDraft) return;
    setSettingsSaving(true);
    try {
      const saved = await api.updateAnalysisSettings(datasetId, settingsDraft);
      setAnalysisSettings(saved);
      setTtcFilter(saved.ttc_threshold_s);
      setDownloadMessage("Configuración avanzada guardada correctamente");
      await refreshAnalysis();
    } catch (err) {
      setDownloadMessage(`Error al guardar configuración: ${(err as Error).message}`);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleResetSettings = () => {
    if (analysisSettings) {
      setSettingsDraft(analysisSettings);
      setTtcFilter(analysisSettings.ttc_threshold_s);
    }
  };

  const handleForbiddenChange = (value: string, origin: ForbiddenFormAction) => {
    if (origin === "input") {
      setForbiddenInput(value);
    }
  };

  const handleSaveForbidden = async () => {
    if (!datasetId) return;
    setForbiddenSaving(true);
    try {
      const parsed = parseForbiddenInput(forbiddenInput);
      const updated = await api.updateForbiddenMovements(datasetId, parsed);
      setForbiddenInput(stringifyForbidden(updated));
      await refreshAnalysis();
      setDownloadMessage("Lista de maniobras prohibidas actualizada");
    } catch (err) {
      setDownloadMessage(`Error al actualizar maniobras prohibidas: ${(err as Error).message}`);
    } finally {
      setForbiddenSaving(false);
    }
  };

  const missingConfigMessage = "Aún no se han generado cardinales/RILSA para este dataset. Ve al paso de configuración y pulsa ‘Generar accesos’.";
  const emptyDataMessage = "No se detectaron trayectorias válidas con las reglas actuales (posible PKL con pocos objetos o muy corto).";

  const renderLoadingMessage = (text: string) => (
    <div className="text-center text-slate-500">{text}</div>
  );

  const renderErrorMessage = (text: string) => (
    <div className="text-center text-red-600">{text}</div>
  );

  const renderInfoMessage = (text: string) => (
    <div className="text-center text-slate-500">{text}</div>
  );

  const isMissingConfig = (state: ResourceState<unknown>) =>
    state.status === 404 && state.error !== null && state.error.toLowerCase().includes("dataset sin datos normalizados");

  const renderVolumesTab = () => {
    if (volumesState.loading) return renderLoadingMessage("Cargando volúmenes…");
    if (volumesState.error) {
      if (isMissingConfig(volumesState)) {
        return renderInfoMessage(missingConfigMessage);
      }
      return renderErrorMessage(`Error al cargar volúmenes: ${volumesState.error}`);
    }
    if (!volumesState.data || volumesState.data.totals_by_interval.length === 0) {
      return renderInfoMessage(emptyDataMessage);
    }
    return (
      <VolumeDashboard
        data={volumesState.data}
        visibleColumns={visibleColumns}
        onToggleColumn={toggleColumn}
      />
    );
  };

  const renderSpeedsTab = () => {
    if (speedsState.loading) return renderLoadingMessage("Cargando velocidades…");
    if (speedsState.error) {
      if (isMissingConfig(speedsState)) {
        return renderInfoMessage(missingConfigMessage);
      }
      return renderErrorMessage(`Error al cargar velocidades: ${speedsState.error}`);
    }
    if (!speedsState.data || speedsState.data.per_movement.length === 0) {
      return renderInfoMessage(emptyDataMessage);
    }
    return <SpeedDashboard data={speedsState.data} maxValue={maxSpeedValue} />;
  };

  const renderConflictsTab = () => {
    if (conflictsState.loading) return renderLoadingMessage("Cargando conflictos…");
    if (conflictsState.error) {
      if (isMissingConfig(conflictsState)) {
        return renderInfoMessage(missingConfigMessage);
      }
      return renderErrorMessage(`Error al cargar conflictos: ${conflictsState.error}`);
    }
    if (!conflictsState.data) {
      return renderInfoMessage(emptyDataMessage);
    }
    return (
      <ConflictDashboard
        data={conflictsState.data}
        filters={conflictFilters}
        onToggleFilter={toggleConflictFilter}
        filteredEvents={filteredConflictEvents}
        severityThreshold={ttcFilter}
        onSeverityChange={setTtcFilter}
        onRefresh={refreshAnalysis}
      />
    );
  };

  const renderViolationsTab = () => {
    if (violationsState.loading) return renderLoadingMessage("Cargando maniobras indebidas…");
    if (violationsState.error) {
      if (isMissingConfig(violationsState)) {
        return renderInfoMessage(missingConfigMessage);
      }
      return renderErrorMessage(`Error al cargar maniobras indebidas: ${violationsState.error}`);
    }
    return (
      <ViolationsPanel
        data={violationsState.data}
        forbiddenInput={forbiddenInput}
        onForbiddenChange={handleForbiddenChange}
        onSaveForbidden={handleSaveForbidden}
        saving={forbiddenSaving}
      />
    );
  };

  const renderDiagnosticsTab = () => {
    if (qcState.loading) return renderLoadingMessage("Cargando resumen de control de calidad…");
    if (qcState.error) {
      if (isMissingConfig(qcState)) {
        return renderInfoMessage(missingConfigMessage);
      }
      return renderErrorMessage(`Error al cargar el resumen QC: ${qcState.error}`);
    }
    if (!qcState.data) {
      return renderInfoMessage(emptyDataMessage);
    }
    return <QcSummaryPanel data={qcState.data} />;
  };

  if (!datasetId) {
    return <div className="p-12 text-center text-red-600">Dataset no encontrado.</div>;
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="bg-white border border-slate-200 rounded-2xl px-8 py-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Análisis integral – Dataset {datasetId}</h1>
          <p className="text-sm text-slate-600 mt-1">
            Ajusta la configuración avanzada, monitorea volúmenes, velocidades, conflictos TTC/PET y maniobras indebidas en un solo lugar.
          </p>
        </header>

        <nav className="flex flex-wrap gap-4">
          {[
            { id: "volumes", label: "Volúmenes" },
            { id: "speeds", label: "Velocidades" },
            { id: "conflicts", label: "Conflictos" },
            { id: "violations", label: "Maniobras indebidas" },
            { id: "diagnostics", label: "Diagnóstico" },
            { id: "settings", label: "Configuración avanzada" },
            { id: "downloads", label: "Descargas" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabId)}
              className={`px-4 py-2 rounded-lg border transition ${
                activeTab === tab.id
                  ? "border-blue-500 bg-blue-50 text-blue-700 font-semibold"
                  : "border-slate-200 bg-white text-slate-600 hover:border-blue-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
          {loading ? (
            <div className="text-center text-slate-500">Cargando análisis…</div>
          ) : error ? (
            <div className="text-center text-red-600">Error: {error}</div>
          ) : activeTab === "volumes" ? (
            renderVolumesTab()
          ) : activeTab === "speeds" ? (
            renderSpeedsTab()
          ) : activeTab === "conflicts" ? (
            renderConflictsTab()
          ) : activeTab === "violations" ? (
            renderViolationsTab()
          ) : activeTab === "diagnostics" ? (
            renderDiagnosticsTab()
          ) : activeTab === "settings" ? (
            <SettingsPanel
              settings={analysisSettings}
              draft={settingsDraft}
              onFieldChange={handleSettingsDraft}
              onSave={handleSaveSettings}
              onReset={handleResetSettings}
              saving={settingsSaving}
            />
          ) : (
            <DownloadsPanel
              state={downloadState}
              message={downloadMessage}
              onGenerate={handleDownload}
              totalVehicles={volumesState.data?.totals_by_interval.reduce((sum, row) => sum + row.total, 0) ?? 0}
              totalViolations={violationsState.data?.total_violations ?? 0}
              totalConflicts={conflictsState.data?.total_conflicts ?? 0}
            />
          )}
        </section>
      </div>
    </div>
  );
};

interface VolumeDashboardProps {
  data: VolumesResponse | null;
  visibleColumns: VolumeColumns;
  onToggleColumn: (column: keyof VolumeRow) => void;
}

const VolumeDashboard: React.FC<VolumeDashboardProps> = ({ data, visibleColumns, onToggleColumn }) => {
  if (!data) {
    return <div className="text-slate-500">Sin datos de volúmenes disponibles.</div>;
  }

  const activeColumns = (Object.keys(visibleColumns) as (keyof VolumeRow)[]).filter(
    (column) => visibleColumns[column] && !["interval_start", "interval_end", "total"].includes(column)
  );

  const chartData = data.totals_by_interval.map((row) => ({
    interval: `${row.interval_start}-${row.interval_end}`,
    total: row.total,
    autos: row.autos,
    buses: row.buses,
    camiones: row.camiones,
    motos: row.motos,
    bicis: row.bicis,
    peatones: row.peatones,
  }));

  const seriesToRender = ["total", ...activeColumns];

  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Volúmenes cada {data.interval_minutes} minutos</h2>
        <p className="text-sm text-slate-500">
          Visualiza la evolución por intervalo y activa las categorías que quieras destacar en la tabla y gráfica.
        </p>
        <div className="flex flex-wrap gap-3 mt-4">
          {(["autos", "buses", "camiones", "motos", "bicis", "peatones"] as (keyof VolumeRow)[]).map((column) => (
            <label
              key={column}
              className={`flex items-center gap-2 text-sm px-3 py-1 rounded-full border ${
                visibleColumns[column]
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-200 text-slate-500"
              }`}
            >
              <input
                type="checkbox"
                checked={visibleColumns[column]}
                onChange={() => onToggleColumn(column)}
              />
              {column.toUpperCase()}
            </label>
          ))}
        </div>
      </header>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5f5" />
            <XAxis dataKey="interval" tick={{ fontSize: 10 }} interval={Math.max(0, Math.floor(chartData.length / 8))} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={(value: number) => formatNumber.format(value)} />
            <Legend />
            {seriesToRender.map((seriesKey) => (
              <Line
                key={seriesKey}
                type="monotone"
                dataKey={seriesKey}
                stroke={SERIES_COLORS[seriesKey] || "#1d4ed8"}
                strokeWidth={seriesKey === "total" ? 3 : 2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <VolumeTables data={data} visibleColumns={visibleColumns} />
    </div>
  );
};

const VolumeTables: React.FC<{ data: VolumesResponse; visibleColumns: VolumeColumns }> = ({ data, visibleColumns }) => {
  const columns = (Object.keys(visibleColumns) as (keyof VolumeRow)[]).filter(
    (column) =>
      visibleColumns[column] && column !== "interval_start" && column !== "interval_end"
  );

  return (
    <>
      <div className="overflow-x-auto border border-slate-200 rounded-xl">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Intervalo</th>
              {columns.map((column) => (
                <th key={column} className="px-4 py-3 text-right font-medium text-slate-600">
                  {column.toUpperCase()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.totals_by_interval.map((row, idx) => (
              <tr key={idx} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-slate-600">
                  {row.interval_start}-{row.interval_end}
                </td>
                {columns.map((column) => (
                  <td key={column} className="px-4 py-3 text-right">
                    {row[column]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-900">Movimientos RILSA</h3>
        {data.movements.map((movement) => (
          <details key={movement.rilsa_code} className="border border-slate-200 rounded-lg">
            <summary className="px-4 py-3 cursor-pointer flex items-center justify-between bg-slate-50 rounded-lg">
              <span className="font-semibold text-slate-800">
                {movement.rilsa_code} – {movement.description}
              </span>
              <span className="text-xs text-slate-500">
                Total: {movement.rows.reduce((sum, row) => sum + row.total, 0)}
              </span>
            </summary>
            <div className="overflow-x-auto px-4 pb-4">
              <MovementTable rows={movement.rows} visibleColumns={visibleColumns} />
            </div>
          </details>
        ))}
      </div>
    </>
  );
};

interface MovementTableProps {
  rows: VolumeRow[];
  visibleColumns: VolumeColumns;
}

const MovementTable: React.FC<MovementTableProps> = ({ rows, visibleColumns }) => {
  const columns = (Object.keys(visibleColumns) as (keyof VolumeRow)[]).filter(
    (column) =>
      visibleColumns[column] && column !== "interval_start" && column !== "interval_end"
  );
  return (
    <table className="min-w-full text-xs mt-3">
      <thead className="bg-slate-100">
        <tr>
          <th className="text-left px-3 py-2 font-medium text-slate-600">Intervalo</th>
          {columns.map((column) => (
            <th key={column} className="px-3 py-2 text-right font-medium text-slate-600">
              {column.toUpperCase()}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr key={idx} className="border-t border-slate-100">
            <td className="px-3 py-2 font-mono text-slate-600">
              {row.interval_start}-{row.interval_end}
            </td>
            {columns.map((column) => (
              <td key={column} className="px-3 py-2 text-right">
                {row[column]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

interface SpeedDashboardProps {
  data: SpeedsResponse | null;
  maxValue: number;
}

const SpeedDashboard: React.FC<SpeedDashboardProps> = ({ data, maxValue }) => {
  if (!data || data.per_movement.length === 0) {
    return <div className="text-slate-500">Sin datos de velocidad suficientes.</div>;
  }

  const chartData = data.per_movement.slice(0, 20).map((record) => ({
    key: `${record.rilsa_code}-${record.vehicle_class}`,
    rilsa_code: record.rilsa_code,
    vehicle_class: record.vehicle_class,
    mean_kmh: record.stats.mean_kmh,
    p85_kmh: record.stats.p85_kmh,
    count: record.stats.count,
  }));

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Velocidades por movimiento y clase</h2>
        <p className="text-sm text-slate-500">
          Compara velocidad media y percentil 85 para los movimientos con más trayectorias.
        </p>
      </header>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5f5" />
            <XAxis
              dataKey="key"
              tickFormatter={(value: string | number) => {
                if (typeof value === "string") {
                  const [movement] = value.split("-");
                  return movement ?? value;
                }
                return String(value);
              }}
              tick={{ fontSize: 10 }}
              interval={0}
            />
            <YAxis tick={{ fontSize: 10 }} domain={[0, Math.ceil(maxValue / 5) * 5]} />
            <Tooltip formatter={(value: number) => `${formatNumber.format(value)} km/h`} />
            <Legend />
            <Bar dataKey="mean_kmh" fill={SPEED_BAR_COLORS.mean} radius={[4, 4, 0, 0]}>
              <LabelList dataKey="count" position="top" formatter={(value: number) => `${value} tr.`} />
            </Bar>
            <Bar dataKey="p85_kmh" fill={SPEED_BAR_COLORS.p85} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-4">
        {data.per_movement.map((record) => (
          <div key={`${record.rilsa_code}-${record.vehicle_class}`} className="border border-slate-200 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {record.rilsa_code} · {record.description}
                </p>
                <p className="text-xs text-slate-500 uppercase tracking-wide">
                  {record.vehicle_class} · {record.stats.count} trayectorias
                </p>
              </div>
              <div className="text-xs text-slate-500 text-right">
                <div>Media: {record.stats.mean_kmh.toFixed(1)} km/h</div>
                <div>P85: {record.stats.p85_kmh.toFixed(1)} km/h</div>
              </div>
            </div>

            <div className="relative h-10 bg-slate-100 rounded-md overflow-hidden">
              <div
                className="absolute left-0 top-0 h-full bg-blue-400/70"
                style={{ width: `${(record.stats.mean_kmh / maxValue) * 100}%` }}
              />
              <div
                className="absolute left-0 top-0 h-full bg-blue-600/60"
                style={{ width: `${(record.stats.p85_kmh / maxValue) * 100}%` }}
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 border-l-2 border-red-500"
                style={{ left: `${(record.stats.max_kmh / maxValue) * 100}%` }}
              >
                <span className="absolute left-2 -translate-y-1/2 text-xs text-red-600">
                  Máx {record.stats.max_kmh.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface ConflictDashboardProps {
  data: ConflictsResponse | null;
  filters: Record<string, boolean>;
  onToggleFilter: (pairType: string) => void;
  filteredEvents: ConflictEvent[];
  severityThreshold: number;
  onSeverityChange: (value: number) => void;
  onRefresh: () => Promise<void>;
}

const ConflictDashboard: React.FC<ConflictDashboardProps> = ({
  data,
  filters,
  onToggleFilter,
  filteredEvents,
  severityThreshold,
  onSeverityChange,
  onRefresh,
}) => {
  if (!data) {
    return <div className="text-slate-500">Sin métricas de conflictos registradas.</div>;
  }

  const pairTypes = Object.keys(filters);
  const mapWidth = 640;
  const mapHeight = 360;

  const extents = filteredEvents.reduce(
    (acc, event) => ({
      minX: Math.min(acc.minX, event.x),
      maxX: Math.max(acc.maxX, event.x),
      minY: Math.min(acc.minY, event.y),
      maxY: Math.max(acc.maxY, event.y),
    }),
    { minX: 0, maxX: 1, minY: 0, maxY: 1 }
  );
  const scaleX = extents.maxX - extents.minX || 1;
  const scaleY = extents.maxY - extents.minY || 1;

  return (
    <div className="space-y-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Conflictos TTC &amp; PET</h2>
          <p className="text-sm text-slate-500">
            Ajusta filtros por tipo de interacción y umbral TTC para resaltar los eventos más severos.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="bg-slate-100 rounded-lg px-4 py-3 text-sm text-slate-700">
            Total detectado: <span className="font-semibold text-slate-900">{data.total_conflicts}</span>
          </div>
          <button
            onClick={onRefresh}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Recalcular análisis
          </button>
        </div>
      </header>

      <div className="flex flex-wrap gap-3">
        {pairTypes.map((type) => (
          <label key={type} className="flex items-center gap-2 text-sm px-3 py-1 border border-slate-200 rounded-full">
            <input
              type="checkbox"
              checked={filters[type]}
              onChange={() => onToggleFilter(type)}
            />
            {type}
          </label>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm text-slate-600 flex items-center gap-2">
          Umbral TTC (s)
          <input
            type="range"
            min={0.5}
            max={3.0}
            step={0.1}
            value={severityThreshold}
            onChange={(event) => onSeverityChange(parseFloat(event.target.value))}
          />
          <span className="font-semibold text-slate-800">{severityThreshold.toFixed(1)}</span>
        </label>
      </div>

      <div className="relative border border-slate-200 rounded-xl overflow-hidden">
        <div
          className="relative"
          style={{
            width: mapWidth,
            height: mapHeight,
            background: "linear-gradient(135deg, #0f172a, #1e293b)",
          }}
        >
          <div className="absolute inset-12 border-2 border-slate-600/60 rounded-lg pointer-events-none" />
          {filteredEvents.map((event, idx) => {
            const x = ((event.x - extents.minX) / scaleX) * mapWidth;
            const y = ((event.y - extents.minY) / scaleY) * mapHeight;
            const intensity = Math.min(1, 1 / Math.max(event.ttc_min, 0.1));
            const size = 6 + intensity * 12;
            const baseColor = event.pair_type === "vehicle-peaton" ? "255, 99, 132" : "59, 130, 246";
            return (
              <div
                key={`${event.track_id_1}-${event.track_id_2}-${idx}`}
                className="absolute rounded-full border border-white/40 shadow-lg"
                style={{
                  left: x - size / 2,
                  top: y - size / 2,
                  width: size,
                  height: size,
                  backgroundColor: `rgba(${baseColor}, ${0.35 + intensity * 0.4})`,
                  boxShadow: `0 0 ${8 + intensity * 12}px rgba(${baseColor}, ${0.5})`,
                }}
                title={`Tracks ${event.track_id_1} & ${event.track_id_2} · TTC ${event.ttc_min.toFixed(2)}s`}
              />
            );
          })}
        </div>
        {filteredEvents.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">
            No hay conflictos con los filtros actuales.
          </div>
        )}
      </div>
    </div>
  );
};

interface ViolationsPanelProps {
  data: ViolationsResponse | null;
  forbiddenInput: string;
  onForbiddenChange: (value: string, origin: ForbiddenFormAction) => void;
  onSaveForbidden: () => void;
  saving: boolean;
}

const ViolationsPanel: React.FC<ViolationsPanelProps> = ({ data, forbiddenInput, onForbiddenChange, onSaveForbidden, saving }) => {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Maniobras indebidas detectadas</h2>
        <p className="text-sm text-slate-500">
          Ajusta los movimientos RILSA prohibidos y recalcúla el resumen para detectar infracciones en segundos.
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Lista de movimientos prohibidos</h3>
          <textarea
            value={forbiddenInput}
            onChange={(event) => onForbiddenChange(event.target.value, "input")}
            rows={8}
            className="w-full border border-slate-200 rounded-lg p-3 font-mono text-sm"
            placeholder="Ejemplo: 5:Giro izquierda restringido"
          />
          <p className="text-xs text-slate-500 mt-1">
            Separa códigos por línea o coma. Puedes añadir descripción usando ":".
          </p>
          <button
            onClick={onSaveForbidden}
            disabled={saving}
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-slate-400"
          >
            {saving ? "Guardando…" : "Guardar y recalcular"}
          </button>
        </div>

        <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
          <h3 className="text-sm font-semibold text-slate-700">Resumen detectado</h3>
          {data && data.total_violations > 0 ? (
            <>
              <p className="text-sm text-slate-600 mt-2">
                Total de maniobras indebidas: <span className="font-semibold text-slate-900">{data.total_violations}</span>
              </p>
              <table className="mt-3 w-full text-xs">
                <thead className="bg-slate-100">
                  <tr>
                    <th className="left px-3 py-2 text-left font-semibold text-slate-600">RILSA</th>
                    <th className="left px-3 py-2 text-left font-semibold text-slate-600">Descripción</th>
                    <th className="px-3 py-2 text-right font-semibold text-slate-600">Conteo</th>
                  </tr>
                </thead>
                <tbody>
                  {data.by_movement.map((item) => (
                    <tr key={item.rilsa_code} className="border-t border-slate-200">
                      <td className="px-3 py-2 font-mono text-slate-700">{item.rilsa_code}</td>
                      <td className="px-3 py-2 text-slate-600">{item.description || "—"}</td>
                      <td className="px-3 py-2 text-right font-semibold text-slate-800">{item.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p className="text-sm text-slate-500 mt-2">No se detectaron maniobras indebidas con la configuración actual.</p>
          )}
        </div>
      </div>
    </div>
  );
};

interface SettingsPanelProps {
  settings: AnalysisSettings | null;
  draft: AnalysisSettings | null;
  onFieldChange: <K extends keyof AnalysisSettings>(key: K, value: AnalysisSettings[K]) => void;
  onSave: () => void;
  onReset: () => void;
  saving: boolean;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ settings, draft, onFieldChange, onSave, onReset, saving }) => {
  const currentDraft = draft || settings || DEFAULT_SETTINGS;
  const currentSettings = settings || DEFAULT_SETTINGS;

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Configuración avanzada de análisis</h2>
        <p className="text-sm text-slate-500">
          Estos parámetros afectan los cálculos de volúmenes, filtros de trayectoria, conflictos TTC y detección de maniobras indebidas.
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <label className="block text-sm text-slate-600">
            Intervalo de consolidación (min)
            <select
              value={currentDraft.interval_minutes}
              onChange={(event) => onFieldChange("interval_minutes", Number(event.target.value))}
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
            >
              {[5, 10, 12, 15, 20, 30].map((value) => (
                <option key={value} value={value}>
                  {value} minutos
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm text-slate-600">
            Longitud mínima de trayectoria (m)
            <input
              type="number"
              min={1}
              step={0.5}
              value={currentDraft.min_length_m}
              onChange={(event) => onFieldChange("min_length_m", Number(event.target.value))}
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
            />
          </label>

          <label className="block text-sm text-slate-600">
            Máx. cambios de dirección permitidos
            <input
              type="number"
              min={0}
              step={1}
              value={currentDraft.max_direction_changes}
              onChange={(event) => onFieldChange("max_direction_changes", Number(event.target.value))}
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
            />
          </label>
        </div>

        <div className="space-y-4">
          <label className="block text-sm text-slate-600">
            Ratio mínimo desplazamiento neto / recorrido
            <input
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={currentDraft.min_net_over_path_ratio}
              onChange={(event) => onFieldChange("min_net_over_path_ratio", Number(event.target.value))}
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
            />
          </label>

          <label className="block text-sm text-slate-600">
            Umbral TTC para conflictos (s)
            <input
              type="number"
              min={0.5}
              max={5}
              step={0.1}
              value={currentDraft.ttc_threshold_s}
              onChange={(event) => onFieldChange("ttc_threshold_s", Number(event.target.value))}
              className="mt-1 w-full border border-slate-200 rounded-lg px-3 py-2"
            />
          </label>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs text-slate-600">
            <p className="font-semibold text-slate-700 mb-2">Configuración aplicada actualmente</p>
            <ul className="space-y-1">
              <li>Intervalo: {currentSettings.interval_minutes} min</li>
              <li>Longitud mínima: {currentSettings.min_length_m} m</li>
              <li>Máx. cambios dirección: {currentSettings.max_direction_changes}</li>
              <li>Ratio neto: {currentSettings.min_net_over_path_ratio}</li>
              <li>TTC mínimo: {currentSettings.ttc_threshold_s} s</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={onSave}
          disabled={saving}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold"
        >
          {saving ? "Guardando…" : "Guardar y recalcular"}
        </button>
        <button
          onClick={onReset}
          disabled={saving}
          className="border border-slate-200 px-4 py-2 rounded-lg text-slate-600 hover:border-blue-200 hover:text-blue-600"
        >
          Restablecer
        </button>
      </div>
    </div>
  );
};

interface DownloadsPanelProps {
  state: DownloadState;
  message: string | null;
  onGenerate: (type: "csv" | "excel" | "pdf") => void;
  totalVehicles: number;
  totalViolations: number;
  totalConflicts: number;
}

const DownloadsPanel: React.FC<DownloadsPanelProps> = ({ state, message, onGenerate, totalVehicles, totalViolations, totalConflicts }) => {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Descargas de reportes</h2>
        <p className="text-sm text-slate-500">
          Genera archivos consolidados con la configuración actual: CSV detallado, Excel multi-hoja y PDF ejecutivo con resumen de volúmenes, velocidades, conflictos y maniobras indebidas.
        </p>
      </header>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 grid md:grid-cols-3 gap-4 text-sm text-slate-600">
        <div>
          <p className="font-semibold text-slate-800">Total vehículos</p>
          <p>{formatNumber.format(totalVehicles)}</p>
        </div>
        <div>
          <p className="font-semibold text-slate-800">Maniobras indebidas</p>
          <p>{formatNumber.format(totalViolations)}</p>
        </div>
        <div>
          <p className="font-semibold text-slate-800">Conflictos TTC</p>
          <p>{formatNumber.format(totalConflicts)}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <DownloadCard
          title="CSV detallado"
          description="Conteos por intervalo, movimiento y categoría para análisis rápido."
          emoji="📊"
          disabled={state === "loading"}
          onClick={() => onGenerate("csv")}
        />
        <DownloadCard
          title="Excel multi-hoja"
          description="Hoja Totales + pestañas por movimiento RILSA, listo para Excel."
          emoji="📈"
          disabled={state === "loading"}
          onClick={() => onGenerate("excel")}
        />
        <DownloadCard
          title="PDF ejecutivo"
          description="Portada + resumen de volúmenes, velocidades, conflictos y maniobras indebidas."
          emoji="📄"
          disabled={state === "loading"}
          onClick={() => onGenerate("pdf")}
        />
      </div>

      {message && (
        <div className="px-4 py-3 rounded-lg border border-slate-200 bg-slate-50 text-sm text-slate-600">
          {message}
        </div>
      )}
    </div>
  );
};

interface DownloadCardProps {
  title: string;
  description: string;
  emoji: string;
  onClick: () => void;
  disabled: boolean;
}

const DownloadCard: React.FC<DownloadCardProps> = ({ title, description, emoji, onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`flex flex-col items-start h-full px-5 py-6 border rounded-xl text-left transition ${
      disabled ? "border-slate-200 bg-slate-50 text-slate-400" : "border-slate-200 hover:border-blue-300"
    }`}
  >
    <span className="text-3xl mb-3">{emoji}</span>
    <h3 className="text-base font-semibold text-slate-800 mb-2">{title}</h3>
    <p className="text-sm text-slate-500 flex-1">{description}</p>
    <span className="text-sm text-blue-600 font-medium mt-3">Generar y descargar</span>
  </button>
);

export default ResultsPage;

interface QcSummaryPanelProps {
  data: QcSummary;
}

const CLASS_ORDER = ["auto", "bus", "camion", "moto", "bici", "peaton", "ignore"];

const QcSummaryPanel: React.FC<QcSummaryPanelProps> = ({ data }) => {
  const classEntries = CLASS_ORDER.map((cls) => [cls, data.counts_by_class?.[cls] ?? 0]);
  const movementEntries = Object.entries(data.counts_by_movement || {}).sort((a, b) =>
    a[0].localeCompare(b[0], undefined, { numeric: true })
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Resumen de control de calidad</h2>
          <p className="text-sm text-slate-500">
            Compara los tracks detectados en el parquet contra los considerados en los cálculos por clase y movimiento.
          </p>
        </div>
      </header>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
          <p className="font-semibold text-slate-800">Tracks brutos</p>
          <p className="text-2xl font-bold text-slate-900">{data.total_tracks_raw}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
          <p className="font-semibold text-slate-800">Tracks contados (sin ignore)</p>
          <p className="text-2xl font-bold text-slate-900">{data.counted_tracks}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
          <p className="font-semibold text-slate-800">Tracks ignorados</p>
          <p className="text-2xl font-bold text-slate-900">{data.counts_by_class?.ignore ?? 0}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <div className="bg-slate-100 px-4 py-3 font-semibold text-slate-800">Conteo por clase</div>
          <table className="w-full text-sm">
            <tbody>
              {classEntries.map(([cls, count]) => (
                <tr key={cls} className="border-t border-slate-200">
                  <td className="px-4 py-2 font-semibold text-slate-700 uppercase">{cls}</td>
                  <td className="px-4 py-2 text-right font-mono text-slate-800">{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <div className="bg-slate-100 px-4 py-3 font-semibold text-slate-800">Conteo por movimiento RILSA</div>
          {movementEntries.length ? (
            <table className="w-full text-sm">
              <tbody>
                {movementEntries.map(([code, count]) => (
                  <tr key={code} className="border-t border-slate-200">
                    <td className="px-4 py-2 font-mono text-blue-700">{code}</td>
                    <td className="px-4 py-2 text-right font-mono text-slate-800">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-4 py-3 text-sm text-slate-500">Sin movimientos contabilizados</div>
          )}
        </div>
      </div>
    </div>
  );
};
