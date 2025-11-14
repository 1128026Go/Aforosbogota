/**
 * StepIndicator - Visual step navigation
 */
import React from "react";

interface Step {
  id: number;
  name: string;
  description: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  onStepClick: (step: number) => void;
  canSkipBack?: boolean;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  onStepClick,
  canSkipBack = true,
}) => {
  return (
    <div className="w-full bg-slate-100 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        {steps.map((step, idx) => (
          <React.Fragment key={step.id}>
            {/* Step circle */}
            <button
              onClick={() => canSkipBack && onStepClick(step.id)}
              disabled={!canSkipBack && step.id > currentStep}
              className={`flex flex-col items-center cursor-pointer transition-all ${
                step.id === currentStep
                  ? "text-blue-600"
                  : step.id < currentStep
                    ? "text-green-600 cursor-pointer"
                    : "text-slate-400"
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  step.id === currentStep
                    ? "bg-blue-500 text-white"
                    : step.id < currentStep
                      ? "bg-green-500 text-white"
                      : "bg-slate-300 text-slate-600"
                }`}
              >
                {step.id < currentStep ? "✓" : step.id}
              </div>
              <span className="text-xs font-semibold mt-1 max-w-24 text-center">
                {step.name}
              </span>
              <span className="text-xs text-slate-500 mt-0.5 max-w-24 text-center">
                {step.description}
              </span>
            </button>

            {/* Connector line */}
            {idx < steps.length - 1 && (
              <div
                className={`flex-1 h-1 mx-2 ${
                  step.id < currentStep ? "bg-green-500" : "bg-slate-300"
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default StepIndicator;
