/**
 * AccessEditorPanel - Panel for editing access configurations
 */
import React from "react";
import { AccessConfig, Cardinal } from "@/types";

interface AccessEditorPanelProps {
  accesses: AccessConfig[];
  selectedAccess: Cardinal | null;
  onSelectAccess: (cardinal: Cardinal | null) => void;
  onRemovePolygon: (cardinal: Cardinal) => void;
}

const AccessEditorPanel: React.FC<AccessEditorPanelProps> = ({
  accesses,
  selectedAccess,
  onSelectAccess,
  onRemovePolygon,
}) => {

  const cardinalColors: Record<Cardinal, { bg: string; ring: string; text: string }> = {
    N: { bg: "bg-red-50", ring: "ring-red-200", text: "text-red-700" },
    S: { bg: "bg-blue-50", ring: "ring-blue-200", text: "text-blue-700" },
    E: { bg: "bg-green-50", ring: "ring-green-200", text: "text-green-700" },
    O: { bg: "bg-amber-50", ring: "ring-amber-200", text: "text-amber-700" },
  };

  const cardinalLabels: Record<Cardinal, string> = {
    N: "Norte",
    S: "Sur",
    E: "Este",
    O: "Oeste",
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2">
        {(["N", "S", "E", "O"] as Cardinal[]).map((cardinal) => {
          const access = accesses.find((a) => a.cardinal === cardinal);
          const isSelected = selectedAccess === cardinal;
          const hasPolygon = access?.polygon && access.polygon.length > 0;
          const colors = cardinalColors[cardinal];

          return (
            <button
              key={cardinal}
              onClick={() => onSelectAccess(isSelected ? null : cardinal)}
              className={`p-3 rounded-lg border-2 transition ${
                isSelected
                  ? `${colors.bg} ring-2 ${colors.ring} border-${cardinal === "N" ? "red" : cardinal === "S" ? "blue" : cardinal === "E" ? "green" : "amber"}-300`
                  : "bg-white border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-sm font-semibold text-gray-900">{cardinalLabels[cardinal]}</div>
              <div className={`text-xs mt-1 ${colors.text}`}>
                {cardinal}
              </div>
              {hasPolygon && (
                <div className="text-xs text-gray-500 mt-1">
                  {access.polygon.length} vértices
                </div>
              )}
            </button>
          );
        })}
      </div>

      {selectedAccess && (
        <div className="space-y-3 border-t pt-4">
          <h3 className="font-semibold text-gray-900">
            Editar {cardinalLabels[selectedAccess]} ({selectedAccess})
          </h3>

          {accesses.find((a) => a.cardinal === selectedAccess)?.polygon?.length === 0 ? (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-700">
                No hay polígono definido. Dibuja en el canvas o copia coordenadas.
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Vértices del polígono
                </label>
                <div className="bg-gray-50 p-3 rounded max-h-32 overflow-y-auto">
                  {accesses.find((a) => a.cardinal === selectedAccess)?.polygon?.map(
                    ([x, y], idx) => (
                      <div key={idx} className="text-xs text-gray-600 font-mono">
                        {idx}: ({x.toFixed(1)}, {y.toFixed(1)})
                      </div>
                    )
                  )}
                </div>
              </div>

              <button
                onClick={() => {
                  onRemovePolygon(selectedAccess);
                  onSelectAccess(null);
                }}
                className="w-full px-3 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 border border-red-200"
              >
                Reiniciar polígono
              </button>
            </>
          )}
        </div>
      )}

      <div className="border-t pt-4 space-y-2 text-xs text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span>Norte (N)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span>Sur (S)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span>Este (E)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-amber-500 rounded"></div>
          <span>Oeste (O)</span>
        </div>
      </div>
    </div>
  );
};

export default AccessEditorPanel;
