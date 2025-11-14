/**
 * StepNavigation - Multi-step wizard navigation component
 * Handles 7-step workflow for AFOROS RILSA v3.0.2
 */
import React from "react";

export type StepKey = "upload" | "config" | "results";

export interface Step {
  id: number;
  key: StepKey;
  name: string;
  description: string;
  requiresDataset: boolean;
  route: (datasetId?: string) => string;
}

export const STEPS: Step[] = [
  {
    id: 1,
    key: "upload",
    name: "Subir PKL",
    description: "Carga archivo PKL y crea dataset",
    requiresDataset: false,
    route: () => "/datasets/upload",
  },
  {
    id: 2,
    key: "config",
    name: "Configurar Accesos",
    description: "Define puntos cardinales y accesos",
    requiresDataset: true,
    route: (datasetId) => `/datasets/${datasetId}/config`,
  },
  {
    id: 3,
    key: "results",
    name: "Resultados",
    description: "Resumen final y descargas",
    requiresDataset: true,
    route: (datasetId) => `/datasets/${datasetId}/results`,
  },
];

interface StepNavigationProps {
  currentStep: StepKey;
  datasetId?: string;
  onNavigate: (step: StepKey, route: string) => void;
}

const StepNavigation: React.FC<StepNavigationProps> = ({
  currentStep,
  datasetId,
  onNavigate,
}) => {
  const currentStepObj = STEPS.find((s) => s.key === currentStep);
  const currentStepId = currentStepObj?.id || 1;

  const handleStepClick = (step: Step) => {
    // Disable if requires dataset and no dataset
    if (step.requiresDataset && !datasetId) {
      return;
    }
    const route = step.route(datasetId);
    onNavigate(step.key, route);
  };

  return (
    <div className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Step Title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {currentStepObj?.name}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {currentStepObj?.description}
          </p>
        </div>

        {/* Step Indicator Bar */}
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => {
            const isCompleted = step.id < currentStepId;
            const isCurrent = step.id === currentStepId;
            const isDisabled = step.requiresDataset && !datasetId;
            const isClickable =
              !isCurrent && !isDisabled && (step.id <= currentStepId || step.id === currentStepId + 1);

            return (
              <React.Fragment key={step.id}>
                {/* Step Circle */}
                <button
                  onClick={() => handleStepClick(step)}
                  disabled={!isClickable}
                  className={`relative flex-shrink-0 w-12 h-12 rounded-full font-medium text-sm transition-all ${
                    isCompleted
                      ? "bg-green-500 text-white hover:bg-green-600"
                      : isCurrent
                      ? "bg-blue-500 text-white ring-4 ring-blue-200"
                      : isDisabled
                      ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                      : isClickable
                      ? "bg-slate-100 text-gray-700 hover:bg-slate-200 cursor-pointer"
                      : "bg-gray-100 text-gray-400 cursor-not-allowed"
                  }`}
                  title={step.description}
                >
                  {isCompleted ? "✓" : step.id}
                </button>

                {/* Connector Line */}
                {idx < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 transition-colors ${
                      step.id < currentStepId
                        ? "bg-green-500"
                        : step.id === currentStepId
                        ? "bg-blue-300"
                        : "bg-gray-200"
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Step Labels (below) */}
        <div className="flex items-center justify-between mt-3">
          {STEPS.map((step) => (
            <div
              key={step.id}
              className={`text-xs font-medium text-center flex-1 ${
                step.id === currentStepId ? "text-blue-600" : "text-gray-500"
              }`}
            >
              <div className="truncate">{step.name}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StepNavigation;
