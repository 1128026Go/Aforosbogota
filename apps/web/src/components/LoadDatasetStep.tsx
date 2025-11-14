/**
 * LoadDatasetStep - Step 1: Load PKL trajectories
 */
import React, { useState } from "react";
import { TrajectoryPoint } from "@/types";

interface LoadDatasetStepProps {
  onTrajectoriesLoaded: (trajectories: TrajectoryPoint[]) => void;
  onNext: () => void;
  isLoading?: boolean;
}

export const LoadDatasetStep: React.FC<LoadDatasetStepProps> = ({
  onTrajectoriesLoaded,
  onNext,
  isLoading = false,
}) => {
  const [mockData] = useState<TrajectoryPoint[]>([
    // Mock data - En producción viene del PKL
    { frame_id: 1, track_id: 1, x: 100, y: 150, class_id: 0, object_type: "car", confidence: 0.95 },
    { frame_id: 2, track_id: 1, x: 120, y: 160, class_id: 0, object_type: "car", confidence: 0.93 },
    { frame_id: 3, track_id: 1, x: 140, y: 170, class_id: 0, object_type: "car", confidence: 0.94 },
    { frame_id: 1, track_id: 2, x: 300, y: 100, class_id: 0, object_type: "car", confidence: 0.92 },
    { frame_id: 2, track_id: 2, x: 310, y: 120, class_id: 0, object_type: "car", confidence: 0.91 },
    { frame_id: 3, track_id: 2, x: 320, y: 140, class_id: 0, object_type: "car", confidence: 0.93 },
  ]);

  const handleLoadDemo = () => {
    onTrajectoriesLoaded(mockData);
    onNext();
  };

  return (
    <div className="bg-white rounded-lg p-8 max-w-2xl mx-auto">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            Paso 1: Cargar Dataset
          </h2>
          <p className="text-slate-600">
            Cargue el archivo PKL con las trayectorias de los vehículos
          </p>
        </div>

        <div className="border-2 border-dashed border-slate-300 rounded-lg p-12 text-center hover:border-blue-400 transition-colors cursor-pointer">
          <div className="space-y-4">
            <svg
              className="mx-auto h-12 w-12 text-slate-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-14-12l-4 4m0 0l4 4m-4-4h16"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div>
              <p className="font-semibold text-slate-900">
                Arrastra tu archivo PKL aquí
              </p>
              <p className="text-sm text-slate-500">
                o haz clic para seleccionar
              </p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Nota:</strong> El archivo PKL debe contener las trayectorias en formato:
            <code className="bg-white px-2 py-1 rounded ml-1">
              List[TrajectoryPoint]
            </code>
          </p>
        </div>

        <div className="flex justify-center gap-4">
          <button
            onClick={handleLoadDemo}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
          >
            {isLoading ? "Cargando..." : "Usar Datos de Demo"}
          </button>
        </div>

        <div className="bg-slate-50 rounded-lg p-4">
          <h3 className="font-semibold text-slate-900 mb-2">Dataset: gx010323</h3>
          <div className="text-sm text-slate-600 space-y-1">
            <p>📊 Trayectorias: {mockData.length} puntos</p>
            <p>🚗 Tracks: 2 vehículos</p>
            <p>📹 Frames: 3 fotogramas</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadDatasetStep;
