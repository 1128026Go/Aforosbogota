/**
 * App Component - Main router and layout for AFOROS RILSA v3.0.2
 */
import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate, Navigate, useLocation } from "react-router-dom";
import StepNavigation, { StepKey } from "@/components/StepNavigation";

// Import pages (will create them next)
import UploadPage from "@/pages/UploadPage";
import DatasetConfigPage from "@/pages/DatasetConfigPageNew";
import ResultsPage from "@/pages/ResultsPage";

import "./App.css";

const AppContent: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [datasetId, setDatasetId] = useState<string | null>(null);

  // Determine current step based on route
  const getCurrentStep = (): StepKey => {
    const path = window.location.pathname;
    if (path.includes("/upload")) return "upload";
    if (path.includes("/config")) return "config";
    if (path.includes("/results")) return "results";
    return "upload";
  };

  const handleNavigate = (_step: StepKey, route: string) => {
    navigate(route);
  };

  const handleDatasetCreated = (newDatasetId: string) => {
    setDatasetId(newDatasetId);
    // Auto-navigate to config step
    navigate(`/datasets/${newDatasetId}/config`);
  };

  useEffect(() => {
    const match = location.pathname.match(/^\/datasets\/([^/]+)\/(config|results)/);
    const matchedDatasetId = match?.[1];
    console.log("[App] matchedDatasetId:", matchedDatasetId, "pathname:", location.pathname);

    if (!matchedDatasetId || matchedDatasetId === "undefined") {
      if (datasetId !== null) {
        setDatasetId(null);
      }
      if (match) {
        navigate("/datasets/upload", { replace: true });
      }
      return;
    }

    if (matchedDatasetId !== datasetId) {
      setDatasetId(matchedDatasetId);
    }
  }, [location, datasetId, navigate]);

  const normalizedDatasetId = datasetId && datasetId !== "undefined" ? datasetId : undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      <StepNavigation
        currentStep={getCurrentStep()}
        datasetId={normalizedDatasetId}
        onNavigate={handleNavigate}
      />

      <div className="max-w-7xl mx-auto">
        <Routes>
          {/* Step 1: Upload */}
          <Route
            path="/datasets/upload"
            element={<UploadPage onDatasetCreated={handleDatasetCreated} />}
          />

          {/* Step 2: Config */}
          <Route
            path="/datasets/:datasetId/config"
            element={<DatasetConfigPage />}
          />

          {/* Step 3: Resultados */}
          <Route
            path="/datasets/:datasetId/results"
            element={<ResultsPage />}
          />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/datasets/upload" replace />} />
          <Route path="*" element={<Navigate to="/datasets/upload" replace />} />
        </Routes>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
