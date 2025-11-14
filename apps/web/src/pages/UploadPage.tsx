/**
 * UploadPage - Step 1: Upload PKL file and create dataset
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

interface UploadPageProps {
  onDatasetCreated?: (datasetId: string) => void;
}

const UploadPage: React.FC<UploadPageProps> = ({ onDatasetCreated }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Selecciona un archivo primero");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${import.meta.env.VITE_API_URL}/datasets/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed: ${response.status}`);
      }

      const data = await response.json();
      setSuccess(`PKL procesado exitosamente. Dataset: ${data.dataset_id}`);
      setFile(null);

      if (onDatasetCreated) {
        onDatasetCreated(data.dataset_id);
      }

      // Auto-navigate after 2 seconds
      setTimeout(() => {
        navigate(`/datasets/${data.dataset_id}/config`);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir archivo");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="py-12">
      <div className="max-w-2xl mx-auto">
        {/* Upload Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Carga un archivo PKL</h2>

          {/* Drag and Drop Zone */}
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-blue-400 transition mb-6 cursor-pointer"
            onDrop={(e) => {
              e.preventDefault();
              handleFileSelect({ target: { files: e.dataTransfer.files } } as any);
            }}
            onDragOver={(e) => e.preventDefault()}
          >
            <div className="text-4xl mb-3">📁</div>
            <input
              type="file"
              accept=".pkl"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label htmlFor="file-input" className="cursor-pointer">
              {file ? (
                <div>
                  <p className="text-green-600 font-medium">{file.name}</p>
                  <p className="text-sm text-gray-500">({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-700 font-medium">Arrastra un archivo o haz clic</p>
                  <p className="text-sm text-gray-500 mt-1">Formatos soportados: .pkl</p>
                </div>
              )}
            </label>
          </div>

          {/* Status Messages */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 text-sm">
              ❌ {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 text-green-700 text-sm">
              ✅ {success}
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full px-6 py-3 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition"
          >
            {uploading ? "Subiendo..." : "Subir y Procesar PKL"}
          </button>
        </div>

        {/* Datasets Library */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Datasets Recientes</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Sample dataset card (will be populated from API) */}
            <div
              className="border border-slate-200 rounded-lg p-4 hover:shadow-md cursor-pointer transition"
              onClick={() => navigate("/datasets/gx010323/config")}
            >
              <div className="font-medium text-gray-900">gx010323</div>
              <div className="text-xs text-gray-500 mt-1">
                📊 1500 frames | 🚗 45 tracks
              </div>
              <div className="text-xs text-gray-500 mt-2">Created: 2025-01-15</div>
            </div>
          </div>

          <p className="text-sm text-gray-500 mt-6 text-center">
            Sube un nuevo PKL para comenzar o selecciona uno existente arriba
          </p>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
