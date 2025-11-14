/**
 * DatasetConfigPage - Main configuration page with multi-step wizard
 * 
 * Steps:
 * 1. Load dataset (PKL trajectories)
 * 2. Configure cardinals (N, S, E, O) - Visualize & Edit
 * 3. Generate RILSA rules
 * 4. Review and save
 */
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { DatasetConfig, Cardinal, TrajectoryPoint } from "@/types";
import api from "@/lib/api";
import StepIndicator from "@/components/StepIndicator";
import LoadDatasetStep from "@/components/LoadDatasetStep";
import TrajectoryCanvas from "@/components/TrajectoryCanvas";
import AccessEditorPanel from "@/components/AccessEditorPanel";

interface DatasetConfigPageProps {
  datasetId?: string;
  onClose?: () => void;
}

const STEPS = [
  { id: 1, name: "Cargar Dataset", description: "PKL de trayectorias" },
  { id: 2, name: "Cardinalidad", description: "N, S, E, O" },
  { id: 3, name: "Movimientos", description: "Códigos RILSA" },
  { id: 4, name: "Resumen", description: "Guardar" },
];

const DatasetConfigPageNew: React.FC<DatasetConfigPageProps> = ({
  datasetId: propDatasetId,
  onClose,
}) => {
  const { datasetId: routeDatasetId } = useParams<{ datasetId: string }>();
  const datasetId = propDatasetId || routeDatasetId || "gx010323";

  const [currentStep, setCurrentStep] = useState(1);
  const [config, setConfig] = useState<DatasetConfig | null>(null);
  const [trajectories, setTrajectories] = useState<TrajectoryPoint[]>([]);
  const [selectedAccess, setSelectedAccess] = useState<Cardinal | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load initial config
  useEffect(() => {
    loadConfig();
  }, [datasetId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await api.viewConfig(datasetId);
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleTrajectoriesLoaded = (data: TrajectoryPoint[]) => {
    setTrajectories(data);
    setSuccess("Trayectorias cargadas correctamente");
  };

  const handleGenerateAccesses = async () => {
    try {
      setGenerating(true);
      const newAccesses = await api.generateAccesses(datasetId, {
        trajectories,
        imageWidth: 1920,
        imageHeight: 1080,
      });
      if (config) {
        setConfig({
          ...config,
          accesses: newAccesses,
        });
      }
      setSuccess("Accesos generados automáticamente");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en generación");
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveAccesses = async () => {
    if (!config) return;
    try {
      setSaving(true);
      const updated = await api.saveAccesses(datasetId, {
        accesses: config.accesses,
      });
      setConfig(updated);
      setSuccess("Accesos guardados");
      handleNextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateRilsa = async () => {
    try {
      setGenerating(true);
      const updated = await api.generateRilsaRules(datasetId);
      setConfig(updated);
      setSuccess("Movimientos RILSA generados");
      handleNextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en RILSA");
    } finally {
      setGenerating(false);
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
    switch (currentStep) {
      case 1:
        return (
          <LoadDatasetStep
            onTrajectoriesLoaded={handleTrajectoriesLoaded}
            onNext={handleNextStep}
            isLoading={loading}
          />
        );

      case 2:
        return config ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 2: Configurar Puntos Cardinales
              </h2>
              <p className="text-slate-600">
                Visualiza las trayectorias y define los polígonos de acceso
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="grid grid-cols-4 gap-4 mb-4">
                <button
                  onClick={handleGenerateAccesses}
                  disabled={generating || trajectories.length === 0}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  {generating ? "Generando..." : "Generar Automático"}
                </button>
                <button
                  onClick={handleSaveAccesses}
                  disabled={saving || !config.accesses.length}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  {saving ? "Guardando..." : "Guardar Accesos"}
                </button>
                <button
                  onClick={handlePrevStep}
                  className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-semibold"
                >
                  ← Atrás
                </button>
                <button
                  onClick={handleNextStep}
                  disabled={!config.accesses.length}
                  className="bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold"
                >
                  Siguiente →
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {/* Canvas */}
                <div className="col-span-2 bg-slate-100 rounded-lg p-4">
                  <TrajectoryCanvas
                    trajectories={trajectories}
                    accesses={config.accesses}
                    selectedAccess={selectedAccess}
                    onAccessPolygonChange={(cardinal, polygon) =>
                      handleUpdateAccess(cardinal, polygon)
                    }
                    imageWidth={1920}
                    imageHeight={1080}
                    editable
                  />
                </div>

                {/* Panel */}
                <div className="bg-slate-100 rounded-lg p-4">
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
        ) : null;

      case 3:
        return config ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 3: Generar Movimientos RILSA
              </h2>
              <p className="text-slate-600">
                Los códigos de movimiento se generarán automáticamente desde los accesos
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="grid grid-cols-4 gap-4 mb-6">
                <button
                  onClick={handleGenerateRilsa}
                  disabled={generating || !config.accesses.length}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-4 py-2 rounded-lg font-semibold col-span-2 transition-colors"
                >
                  {generating ? "Generando..." : "Generar Movimientos RILSA"}
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

              {config.rilsa_rules.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-900">
                    Movimientos Generados ({config.rilsa_rules.length})
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
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
              )}
            </div>
          </div>
        ) : null;

      case 4:
        return config ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                Paso 4: Resumen y Guardado
              </h2>
              <p className="text-slate-600">
                Revisa toda la configuración antes de guardar
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
              {/* Accesos */}
              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Puntos Cardinales ({config.accesses.length})
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {config.accesses.map((acc) => (
                    <div
                      key={acc.cardinal}
                      className="bg-slate-50 border border-slate-200 rounded p-3"
                    >
                      <div className="font-semibold text-slate-900">
                        {acc.cardinal}
                      </div>
                      <div className="text-sm text-slate-600">
                        Vértices: {acc.polygon.length}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* RILSA Rules */}
              <div>
                <h3 className="text-lg font-semibold mb-3">
                  Movimientos RILSA ({config.rilsa_rules.length})
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  {config.rilsa_rules.map((rule) => (
                    <div
                      key={rule.code}
                      className="bg-blue-50 border border-blue-200 rounded p-2 text-center"
                    >
                      <div className="font-mono font-bold text-blue-600">
                        {rule.code}
                      </div>
                      <div className="text-xs text-slate-600">
                        {rule.origin_access}→{rule.dest_access}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  onClick={handlePrevStep}
                  className="flex-1 bg-slate-600 hover:bg-slate-700 text-white px-4 py-3 rounded-lg font-semibold"
                >
                  ← Atrás
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg font-semibold"
                >
                  ✓ Finalizar
                </button>
              </div>
            </div>
          </div>
        ) : null;

      default:
        return null;
    }
  };

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
