import { useNavigate } from "@/main";

type StepKey =
  | "upload"
  | "config"
  | "validation"
  | "editor"
  | "rules"
  | "history"
  | "live";

interface Step {
  key: StepKey;
  label: string;
  path: string; // usa {datasetId} como placeholder
}

const steps: Step[] = [
  { key: "upload",    label: "1. Subir PKL",          path: "/datasets/upload" },
  { key: "config",    label: "2. Configuración",      path: "/datasets/{datasetId}/config" },
  { key: "validation",label: "3. Validación",         path: "/datasets/{datasetId}/validation" },
  { key: "editor",    label: "4. Editor",             path: "/datasets/{datasetId}/editor" },
  { key: "rules",     label: "5. Reglas",             path: "/datasets/{datasetId}/rules" },
  { key: "history",   label: "6. Historial",          path: "/datasets/{datasetId}/history" },
  { key: "live",      label: "7. Reproductor / Live", path: "/datasets/{datasetId}/detail" },
];

export type StepNavigationKey = StepKey;

interface StepNavigationProps {
  currentStepKey: StepKey;
  datasetId?: string; // cambio de datasetKey a datasetId para consistencia
}

export function StepNavigation({ currentStepKey, datasetId }: StepNavigationProps) {
  const navigate = useNavigate();

  const currentIndex = steps.findIndex((s) => s.key === currentStepKey);

  const buildPath = (step: Step): string | null => {
    if (step.key === "upload") return step.path;
    if (!datasetId) return null; // pasos >1 requieren datasetId
    return step.path.replace("{datasetId}", datasetId);
  };

  const goToStep = (step: Step) => {
    const path = buildPath(step);
    if (!path) return;
    navigate(path);
  };

  const goPrev = () => {
    if (currentIndex > 0) {
      goToStep(steps[currentIndex - 1]);
    }
  };

  const goNext = () => {
    if (currentIndex < steps.length - 1) {
      goToStep(steps[currentIndex + 1]);
    }
  };

  return (
    <div className="flex flex-col gap-2 mb-4">
      {/* barra de pasos */}
      <div className="flex flex-wrap gap-2">
        {steps.map((step, index) => {
          const isActive = step.key === currentStepKey;
          const requiresDataset = index > 0;
          const disabled = requiresDataset && !datasetId;

          return (
            <button
              key={step.key}
              type="button"
              onClick={() => !disabled && goToStep(step)}
              className={[
                "px-3 py-1 rounded text-sm border",
                isActive ? "font-semibold border-blue-500" : "border-gray-300",
                disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer",
              ].join(" ")}
            >
              {step.label}
            </button>
          );
        })}
      </div>

      {/* botones Anterior / Siguiente */}
      <div className="flex justify-between">
        <button
          type="button"
          onClick={goPrev}
          disabled={currentIndex <= 0}
          className={[
            "px-3 py-1 rounded border text-sm",
            currentIndex <= 0 ? "opacity-40 cursor-not-allowed" : "",
          ].join(" ")}
        >
          ← Anterior
        </button>
        <button
          type="button"
          onClick={goNext}
          disabled={
            currentIndex >= steps.length - 1 ||
            (!datasetId && currentIndex === 0)
          }
          className={[
            "px-3 py-1 rounded border text-sm",
            currentIndex >= steps.length - 1 ||
            (!datasetId && currentIndex === 0)
              ? "opacity-40 cursor-not-allowed"
              : "",
          ].join(" ")}
        >
          Siguiente →
        </button>
      </div>
    </div>
  );
}