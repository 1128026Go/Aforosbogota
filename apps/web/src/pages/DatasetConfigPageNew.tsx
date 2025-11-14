/**
 * DatasetConfigPage - Main configuration page for cardinal and RILSA setup
 */
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  DatasetConfig,
  Cardinal,
  AnalysisSettings,
  ForbiddenMovement,
  DatasetMetadata,
} from "@/types";
import api from "@/lib/api";
import StepIndicator from "@/components/StepIndicator";
import TrajectoryCanvas from "@/components/TrajectoryCanvas";
import AccessEditorPanel from "@/components/AccessEditorPanel";

interface DatasetConfigPageProps {
  datasetId?: string;
  onClose?: () => void;
}

const STEPS = [
  { id: 1, name: "Cardinalidad", description: "N, S, E, O" },
  { id: 2, name: "Movimientos", description: "Códigos RILSA" },
  { id: 3, name: "Resumen", description: "Guardar" },
];

const DatasetConfigPageNew: React.FC<DatasetConfigPageProps> = ({
  datasetId: propDatasetId,
  onClose,
}) => {
  const navigate = useNavigate();
  const { datasetId: routeDatasetId } = useParams<{ datasetId: string }>();
  const datasetId = propDatasetId || routeDatasetId;

  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<DatasetConfig | null>(null);
  const [analysisSettings, setAnalysisSettings] = useState<AnalysisSettings | null>(null);
  const [forbiddenMovements, setForbiddenMovements] = useState<ForbiddenMovement[]>([]);
  const [metadata, setMetadata] = useState<DatasetMetadata | null>(null);
  const [selectedAccess, setSelectedAccess] = useState<Cardinal | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generatingAccesses, setGeneratingAccesses] = useState(false);
  const [generatingRilsa, setGeneratingRilsa] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load initial config
  useEffect(() => {
    if (!datasetId) {
      setError("Dataset no especificado. Regresa al paso de carga y selecciona un archivo.");
      return;
    }
    loadConfig(datasetId);
  }, [datasetId]);

  useEffect(() => {
    if (config && config.accesses.length > 0) {
      const first = config.accesses[0]?.cardinal ?? null;
      setSelectedAccess((current) => current || first);
    }
  }, [config]);

  const loadConfig = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const [configData, settingsData, forbiddenData, metadataData] = await Promise.all([
        api.viewConfig(id),
        api.getAnalysisSettings(id).catch(() => null),
        api.getForbiddenMovements(id).catch(() => []),
        api.getDataset(id).catch(() => null),
      ]);

      const mergedForbidden = configData.forbidden_movements ?? forbiddenData;

      setConfig({
        ...configData,
        forbidden_movements: mergedForbidden,
      });
      setAnalysisSettings(settingsData);
      setForbiddenMovements(mergedForbidden);
      setMetadata(metadataData);
      setSuccess(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido al cargar la configuración");
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFinish = () => {
    if (onClose) {
      onClose();
      return;
    }
    if (datasetId) {
      navigate(`/datasets/${datasetId}/results`);
    }
  };

  const handleGenerateAccesses = async () => {
    if (!datasetId) return;
    try {
      setGeneratingAccesses(true);
      setError(null);
      setSuccess(null);

      const response = await api.generateAccesses(datasetId, {
        imageWidth: metadata?.width,
        imageHeight: metadata?.height,
        maxSamples: 10000,
      });

      const newAccesses = response.accesses;

      if (!newAccesses || newAccesses.length === 0) {
        setSuccess("No se generaron accesos automáticamente. Añádelos manualmente.");
        return;
      }

      setConfig((previous) =>
        previous
          ? {
              ...previous,
              accesses: newAccesses,
            }
          : {
              dataset_id: datasetId,
              accesses: newAccesses,
              rilsa_rules: [],
              forbidden_movements: forbiddenMovements,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
      );
      setSelectedAccess(newAccesses[0]?.cardinal ?? null);
      setSuccess("Accesos generados automáticamente. Revisa y ajusta antes de guardar.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudieron generar accesos automáticamente. Revisa el dataset normalizado."
      );
    } finally {
      setGeneratingAccesses(false);
    }
  };

  const handleSaveAccesses = async () => {
    if (!config || !datasetId) return;
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      const updated = await api.saveAccesses(datasetId, {
        accesses: config.accesses,
      });
      setConfig(updated);
      setSuccess("Accesos guardados");
      handleNextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar accesos");
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateRilsa = async () => {
    if (!datasetId) return;
    try {
      setGeneratingRilsa(true);
      setError(null);
      setSuccess(null);
      const updated = await api.generateRilsaRules(datasetId);
      setConfig(updated);
      setSuccess("Movimientos RILSA generados");
      handleNextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en la generación de movimientos RILSA");
    } finally {
      setGeneratingRilsa(false);
    }
  };

  const handleRemovePolygon = (cardinal: Cardinal) => {
    if (!config) return;
    setConfig({
      ...config,
      accesses: config.accesses.filter((a) => a.cardinal !== cardinal),
    });
  };

  const handleUpdateAccess = (cardinal: Cardinal, polygon: [number, number][]) => {
    if (!config) return;
    setConfig({
      ...config,
      accesses: config.accesses.map((a) =>
        a.cardinal === cardinal ? { ...a, polygon } : a
      ),
    });
  };

  // Render each step
  const renderStep = () => {
    if (!config) {
      return (
        <div className="text-center text-slate-600">
          No se pudo cargar la configuración del dataset.
        </div>
      );
    }

    const hasAccesses = config.accesses.length > 0;

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 1: Configurar Puntos Cardinales
              </h2>
              <p className="text-slate-600">
                Ajusta los accesos cardinales usando la previsualización y los polígonos interactivos.
              </p>
            </div>

            {metadata && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">Resumen del dataset</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-600">
                  <div>
                    <span className="font-semibold text-slate-800 block">Frames</span>
                    {metadata.frames ?? "—"}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800 block">Tracks</span>
                    {metadata.tracks ?? "—"}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800 block">Resolución</span>
                    {metadata.width && metadata.height ? `${metadata.width}×${metadata.height}` : "—"}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800 block">FPS</span>
                    {metadata.fps ?? "—"}
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-slate-200 p-4 bg-slate-50 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={handleGenerateAccesses}
                  disabled={generatingAccesses}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  {generatingAccesses ? "Generando..." : "Generar accesos automáticamente"}
                </button>
                <button
                  onClick={handleSaveAccesses}
                  disabled={saving || !hasAccesses}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  {saving ? "Guardando..." : "Guardar accesos"}
                </button>
                <button
                  onClick={handleNextStep}
                  disabled={!hasAccesses}
                  className="bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  Siguiente →
                </button>
              </div>

              {!hasAccesses && (
                <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm text-slate-600">
                  Aún no hay accesos definidos. Genera accesos automáticos o dibuja los polígonos manualmente.
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 bg-slate-900/90 rounded-lg p-4 min-h-[320px] flex items-center justify-center">
                  {hasAccesses ? (
                    <TrajectoryCanvas
                      trajectories={[]}
                      accesses={config.accesses}
                      selectedAccess={selectedAccess}
                      onAccessPolygonChange={(cardinal, polygon) =>
                        handleUpdateAccess(cardinal, polygon)
                      }
                      imageWidth={metadata?.width ?? 1280}
                      imageHeight={metadata?.height ?? 720}
                      editable
                    />
                  ) : (
                    <p className="text-sm text-slate-200 text-center">
                      Genera accesos o dibuja manualmente para comenzar a ajustar las áreas cardinales.
                    </p>
                  )}
                </div>

                <div className="bg-white rounded-lg p-4 border border-slate-200 min-h-[320px]">
                  <AccessEditorPanel
                    accesses={config.accesses}
                    selectedAccess={selectedAccess}
                    onSelectAccess={setSelectedAccess}
                    onRemovePolygon={handleRemovePolygon}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 2: Generar Movimientos RILSA
              </h2>
              <p className="text-slate-600">
                Genera los códigos de movimiento a partir de los accesos definidos y revisa el listado resultante.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <button
                  onClick={handleGenerateRilsa}
                  disabled={generatingRilsa || !config.accesses.length}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold md:col-span-2 transition-colors"
                >
                  {generatingRilsa ? "Generando..." : "Generar Movimientos RILSA"}
                </button>
                <button
                  onClick={handlePrevStep}
                  className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-semibold"
                >
                  ← Atrás
                </button>
                <button
                  onClick={handleNextStep}
                  disabled={!config.rilsa_rules.length}
                  className="bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold"
                >
                  Siguiente →
                </button>
              </div>

              {config.rilsa_rules.length > 0 ? (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-900">
                    Movimientos Generados ({config.rilsa_rules.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {config.rilsa_rules.map((rule) => (
                      <div
                        key={rule.code}
                        className="bg-slate-50 border border-slate-200 rounded-lg p-3"
                      >
                        <div className="font-mono font-bold text-blue-600 text-lg">
                          {rule.code}
                        </div>
                        <div className="text-sm text-slate-700 mt-1">
                          {rule.origin_access} → {rule.dest_access}
                        </div>
                        <div className="text-xs text-slate-600 capitalize mt-1">
                          {rule.movement_type}
                        </div>
                        <div className="text-xs text-slate-600 mt-2">
                          {rule.description}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-600">
                  Genera los movimientos para visualizar la tabla completa.
                </p>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 3: Resumen y Guardado
              </h2>
              <p className="text-slate-600">
                Revisa toda la configuración antes de cerrar y pasar al análisis.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
              <div className="flex flex-col md:flex-row gap-4">
                <button
                  onClick={handlePrevStep}
                  className="md:flex-1 bg-slate-600 hover:bg-slate-700 text-white px-4 py-3 rounded-lg font-semibold"
                >
                  ← Atrás
                </button>
                <button
                  onClick={handleFinish}
                  className="md:flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg font-semibold"
                >
                  ✓ Finalizar
                </button>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Puntos Cardinales ({config.accesses.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {config.accesses.map((acc) => (
                    <div
                      key={acc.cardinal}
                      className="bg-slate-50 border border-slate-200 rounded p-3"
                    >
                      <div className="font-semibold text-slate-900">{acc.cardinal}</div>
                      <div className="text-sm text-slate-600">
                        Vértices: {acc.polygon.length}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Movimientos RILSA ({config.rilsa_rules.length})
                </h3>
                {config.rilsa_rules.length ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {config.rilsa_rules.map((rule) => (
                      <div
                        key={rule.code}
                        className="bg-blue-50 border border-blue-200 rounded p-2 text-center"
                      >
                        <div className="font-mono font-bold text-blue-600">{rule.code}</div>
                        <div className="text-xs text-slate-600">
                          {rule.origin_access}→{rule.dest_access}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">
                    No hay movimientos generados todavía.
                  </p>
                )}
              </div>

              {analysisSettings && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Configuración avanzada aplicada</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-slate-600">
                    <div>
                      <span className="font-semibold text-slate-800 block">Intervalo (min)</span>
                      {analysisSettings.interval_minutes}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800 block">Longitud mínima (m)</span>
                      {analysisSettings.min_length_m}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800 block">Máx. cambios dirección</span>
                      {analysisSettings.max_direction_changes}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800 block">Relación neta mínima</span>
                      {analysisSettings.min_net_over_path_ratio}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-800 block">Umbral TTC (s)</span>
                      {analysisSettings.ttc_threshold_s}
                    </div>
                  </div>
                </div>
              )}

              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Movimientos prohibidos ({forbiddenMovements.length})
                </h3>
                {forbiddenMovements.length ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {forbiddenMovements.map((movement) => (
                      <div
                        key={movement.rilsa_code}
                        className="bg-rose-50 border border-rose-200 rounded p-3"
                      >
                        <div className="font-mono font-bold text-rose-600">
                          {movement.rilsa_code}
                        </div>
                        <div className="text-sm text-slate-600 mt-1">
                          {movement.description || "Sin descripción"}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">
                    No hay maniobras prohibidas configuradas para este dataset.
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!datasetId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="max-w-md text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-3">Dataset no encontrado</h1>
          <p className="text-slate-600">
            No se proporcionó un identificador de dataset. Regresa al paso de carga e intenta nuevamente.
          </p>
        </div>
      </div>
    );
  }

  if (loading && !config) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Configuración de Dataset
          </h1>
          <p className="text-slate-600">
            Dataset ID: <span className="font-mono font-semibold">{datasetId}</span>
          </p>
        </div>

        {/* Step Indicator */}
        <StepIndicator
          steps={STEPS}
          currentStep={currentStep}
          onStepClick={(step) => {
            if (step <= currentStep) {
              setCurrentStep(step);
            }
          }}
          canSkipBack={true}
        />

        {/* Alerts */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            ✓ {success}
          </div>
        )}

        {/* Content */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {renderStep()}
        </div>
      </div>
    </div>
  );
};

export default DatasetConfigPageNew;
