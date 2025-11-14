import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import api from "@/lib/api";
import {
  VolumesResponse,
  SpeedsResponse,
  ConflictsResponse,
  VolumeRow,
  MovementSpeedStats,
  ConflictEvent,
} from "@/types";

type TabId = "volumes" | "speeds" | "conflicts" | "downloads";

const VEHICLE_COLUMNS: (keyof VolumeRow)[] = [
  "autos",
  "buses",
  "camiones",
  "motos",
  "bicis",
  "peatones",
];

const columnLabels: Record<keyof VolumeRow, string> = {
  interval_start: "Inicio",
  interval_end: "Fin",
  autos: "Autos",
  buses: "Buses",
  camiones: "Camiones",
  motos: "Motos",
  bicis: "Bicicletas",
  peatones: "Peatones",
  total: "Total",
};

const ResultsPage: React.FC = () => {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [activeTab, setActiveTab] = useState<TabId>("volumes");
  const [volumes, setVolumes] = useState<VolumesResponse | null>(null);
  const [speeds, setSpeeds] = useState<SpeedsResponse | null>(null);
  const [conflicts, setConflicts] = useState<ConflictsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<Record<keyof VolumeRow, boolean>>({
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
  const [downloadState, setDownloadState] = useState<"idle" | "loading">("idle");
  const [downloadMessage, setDownloadMessage] = useState<string | null>(null);
  const [conflictFilters, setConflictFilters] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchData = async () => {
      if (!datasetId) return;
      setLoading(true);
      setError(null);
      try {
        const [volumesData, speedsData, conflictsData] = await Promise.all([
          api.getVolumes(datasetId),
          api.getSpeeds(datasetId),
          api.getConflicts(datasetId),
        ]);
        setVolumes(volumesData);
        setSpeeds(speedsData);
        setConflicts(conflictsData);
        if (conflictsData?.events) {
          const filters: Record<string, boolean> = {};
          conflictsData.events.forEach((event) => {
            filters[event.pair_type] = true;
          });
          setConflictFilters(filters);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [datasetId]);

  const filteredConflictEvents = useMemo(() => {
    if (!conflicts) return [];
    return conflicts.events.filter((event) => conflictFilters[event.pair_type]);
  }, [conflicts, conflictFilters]);

  const maxSpeedValue = useMemo(() => {
    if (!speeds) return 1;
    return speeds.per_movement.reduce(
      (max, record) => Math.max(max, record.stats.p85_kmh, record.stats.max_kmh),
      1
    );
  }, [speeds]);

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

  if (!datasetId) {
    return <div className="p-12 text-center text-red-600">Dataset no encontrado.</div>;
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="bg-white border border-slate-200 rounded-2xl px-8 py-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Análisis integral – Dataset {datasetId}</h1>
          <p className="text-sm text-slate-600 mt-1">
            Visualiza volúmenes RILSA, velocidades por clase y conflictos TTC/PET. Genera reportes descargables en CSV, Excel y PDF.
          </p>
        </header>

        <nav className="flex gap-4">
          {[
            { id: "volumes", label: "Volúmenes" },
            { id: "speeds", label: "Velocidades" },
            { id: "conflicts", label: "Conflictos" },
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
            <VolumeDashboard
              data={volumes}
              visibleColumns={visibleColumns}
              onToggleColumn={toggleColumn}
            />
          ) : activeTab === "speeds" ? (
            <SpeedDashboard data={speeds} maxValue={maxSpeedValue} />
          ) : activeTab === "conflicts" ? (
            <ConflictDashboard
              data={conflicts}
              filters={conflictFilters}
              onToggleFilter={toggleConflictFilter}
              filteredEvents={filteredConflictEvents}
            />
          ) : (
            <DownloadsPanel
              state={downloadState}
              message={downloadMessage}
              onGenerate={handleDownload}
            />
          )}
        </section>
      </div>
    </div>
  );
};

interface VolumeDashboardProps {
  data: VolumesResponse | null;
  visibleColumns: Record<keyof VolumeRow, boolean>;
  onToggleColumn: (column: keyof VolumeRow) => void;
}

const VolumeDashboard: React.FC<VolumeDashboardProps> = ({ data, visibleColumns, onToggleColumn }) => {
  if (!data) {
    return <div className="text-slate-500">Sin datos de volúmenes disponibles.</div>;
  }

  const activeColumns = (Object.keys(visibleColumns) as (keyof VolumeRow)[]).filter(
    (column) => visibleColumns[column] && column !== "interval_start" && column !== "interval_end"
  );

  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Volúmenes cada {data.interval_minutes} minutos</h2>
        <p className="text-sm text-slate-500">
          Usa los toggles para elegir qué categorías visualizar en la tabla principal y en cada movimiento RILSA.
        </p>
        <div className="flex flex-wrap gap-3 mt-4">
          {VEHICLE_COLUMNS.map((column) => (
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
              {columnLabels[column]}
            </label>
          ))}
        </div>
      </header>

      <div className="overflow-x-auto border border-slate-200 rounded-xl">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Intervalo</th>
              {activeColumns.map((column) => (
                <th key={column} className="px-4 py-3 text-right font-medium text-slate-600">
                  {columnLabels[column]}
                </th>
              ))}
              {visibleColumns.total && (
                <th className="px-4 py-3 text-right font-semibold text-slate-700">Total</th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.totals_by_interval.map((row, idx) => (
              <tr key={idx} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-slate-600">
                  {row.interval_start}-{row.interval_end}
                </td>
                {activeColumns.map((column) => (
                  <td key={column} className="px-4 py-3 text-right">
                    {row[column]}
                  </td>
                ))}
                {visibleColumns.total && (
                  <td className="px-4 py-3 text-right font-semibold text-slate-800">{row.total}</td>
                )}
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
    </div>
  );
};

interface MovementTableProps {
  rows: VolumeRow[];
  visibleColumns: Record<keyof VolumeRow, boolean>;
}

const MovementTable: React.FC<MovementTableProps> = ({ rows, visibleColumns }) => {
  const columns = VEHICLE_COLUMNS.filter((column) => visibleColumns[column]);
  return (
    <table className="min-w-full text-xs mt-3">
      <thead className="bg-slate-100">
        <tr>
          <th className="text-left px-3 py-2 font-medium text-slate-600">Intervalo</th>
          {columns.map((column) => (
            <th key={column} className="px-3 py-2 text-right font-medium text-slate-600">
              {columnLabels[column]}
            </th>
          ))}
          {visibleColumns.total && (
            <th className="px-3 py-2 text-right font-semibold text-slate-700">Total</th>
          )}
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
            {visibleColumns.total && (
              <td className="px-3 py-2 text-right font-semibold text-slate-800">{row.total}</td>
            )}
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

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Velocidades por movimiento y clase</h2>
        <p className="text-sm text-slate-500">
          Las barras muestran la velocidad media y el percentil 85 por tipo de vehículo. Los extremos indican valores máximos observados.
        </p>
      </header>

      <div className="space-y-4">
        {data.per_movement.map((record: MovementSpeedStats) => (
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
}

const ConflictDashboard: React.FC<ConflictDashboardProps> = ({
  data,
  filters,
  onToggleFilter,
  filteredEvents,
}) => {
  if (!data) {
    return <div className="text-slate-500">Sin métricas de conflictos registradas.</div>;
  }

  const pairTypes = Object.keys(filters);
  const mapWidth = 640;
  const mapHeight = 360;
  const events = filteredEvents;

  const extents = events.reduce(
    (acc, event) => {
      return {
        minX: Math.min(acc.minX, event.x),
        maxX: Math.max(acc.maxX, event.x),
        minY: Math.min(acc.minY, event.y),
        maxY: Math.max(acc.maxY, event.y),
      };
    },
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
            Los puntos muestran la ubicación aproximada de conflictos detectados (TTC &lt; 1.5 s).
            Ajusta los filtros por tipo de interacción para resaltar casos relevantes.
          </p>
        </div>
        <div className="bg-slate-100 rounded-lg px-4 py-3 text-sm text-slate-700">
          Total detectado:{" "}
          <span className="font-semibold text-slate-900">{data.total_conflicts}</span>
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
          {events.map((event, idx) => {
            const x = ((event.x - extents.minX) / scaleX) * mapWidth;
            const y = ((event.y - extents.minY) / scaleY) * mapHeight;
            const severity = Math.min(event.severity, 5);
            const size = 6 + severity * 3;
            return (
              <div
                key={`${event.track_id_1}-${event.track_id_2}-${idx}`}
                className="absolute rounded-full border border-white/40 shadow-lg"
                style={{
                  left: x - size / 2,
                  top: y - size / 2,
                  width: size,
                  height: size,
                  backgroundColor: event.pair_type === "vehicle-peaton" ? "#f87171" : "#60a5fa",
                  opacity: 0.8,
                }}
                title={`Tracks ${event.track_id_1} & ${event.track_id_2} · TTC ${event.ttc_min.toFixed(2)}s`}
              />
            );
          })}
        </div>
        {events.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">
            No hay conflictos activos con los filtros seleccionados.
          </div>
        )}
      </div>
    </div>
  );
};

interface DownloadsPanelProps {
  state: "idle" | "loading";
  message: string | null;
  onGenerate: (type: "csv" | "excel" | "pdf") => void;
}

const DownloadsPanel: React.FC<DownloadsPanelProps> = ({ state, message, onGenerate }) => {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Descargas de reportes</h2>
        <p className="text-sm text-slate-500">
          Genera archivos consolidados listos para compartir. El backend produce el reporte y lo descarga automáticamente.
        </p>
      </header>

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
          description="Resumen con tablas, velocidades y conteo de conflictos para entregar."
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
