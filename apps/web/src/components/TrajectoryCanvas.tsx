/**
 * TrajectoryCanvas - Interactive canvas for displaying trajectories and access polygons
 */
import React, { useRef, useEffect, useState } from "react";
import { AccessConfig, TrajectoryPoint, Cardinal } from "@/types";

interface TrajectoryCanvasProps {
  trajectories: TrajectoryPoint[];
  accesses: AccessConfig[];
  selectedAccess: Cardinal | null;
  onAccessPolygonChange: (cardinal: Cardinal, polygon: [number, number][]) => void;
  imageWidth?: number;
  imageHeight?: number;
  editable?: boolean;
}

const TrajectoryCanvas: React.FC<TrajectoryCanvasProps> = ({
  trajectories,
  accesses,
  selectedAccess,
  onAccessPolygonChange,
  imageWidth = 1280,
  imageHeight = 720,
  editable = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(1);
  const [draggingVertex, setDraggingVertex] = useState<{
    cardinal: Cardinal;
    index: number;
  } | null>(null);
  const [isDrawing] = useState(false);
  const [drawingPoints, setDrawingPoints] = useState<[number, number][]>([]);

  // Draw on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Calculate scale to fit canvas
    const maxWidth = canvas.offsetWidth;
    const maxHeight = canvas.offsetHeight;
    const scaleX = maxWidth / imageWidth;
    const scaleY = maxHeight / imageHeight;
    const newScale = Math.min(scaleX, scaleY);
    setScale(newScale);

    // Clear canvas
    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height, newScale);

    // Draw trajectories as points
    ctx.fillStyle = "#60a5fa";
    ctx.globalAlpha = 0.5;
    trajectories.forEach((point) => {
      ctx.beginPath();
      ctx.arc(point.x * newScale, point.y * newScale, 2, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;

    // Draw access polygons
    accesses.forEach((access) => {
      if (!access.polygon || access.polygon.length === 0) return;

      const isSelected = access.cardinal === selectedAccess;
      const color = getCardinalColor(access.cardinal);

      // Draw polygon
      ctx.strokeStyle = isSelected ? "#fbbf24" : color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.globalAlpha = isSelected ? 0.8 : 0.6;

      ctx.beginPath();
      const firstPoint = access.polygon[0];
      if (firstPoint) {
        ctx.moveTo(firstPoint[0] * newScale, firstPoint[1] * newScale);

        for (let i = 1; i < access.polygon.length; i++) {
          const point = access.polygon[i];
          if (point) {
            ctx.lineTo(point[0] * newScale, point[1] * newScale);
          }
        }
      }
      ctx.closePath();
      ctx.stroke();

      // Draw fill
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.1;
      ctx.fill();

      // Draw vertices (if selected and editable)
      if (isSelected && editable) {
        access.polygon.forEach((point, idx) => {
          ctx.fillStyle = "#fbbf24";
          ctx.globalAlpha = 1;
          ctx.beginPath();
          ctx.arc(point[0] * newScale, point[1] * newScale, 5, 0, Math.PI * 2);
          ctx.fill();

          // Draw vertex index
          ctx.fillStyle = "#1f2937";
          ctx.font = "12px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(
            idx.toString(),
            point[0] * newScale,
            point[1] * newScale
          );
        });
      }

      // Draw label
      if (access.centroid) {
        ctx.fillStyle = color;
        ctx.globalAlpha = 1;
        ctx.font = "bold 16px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(
          access.cardinal,
          access.centroid[0] * newScale,
          access.centroid[1] * newScale
        );
      }
    });

    // Draw drawing points (while creating new polygon)
    if (isDrawing && drawingPoints.length > 0) {
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.8;

      ctx.beginPath();
      const firstDrawPoint = drawingPoints[0];
      if (firstDrawPoint) {
        ctx.moveTo(firstDrawPoint[0] * newScale, firstDrawPoint[1] * newScale);

        for (let i = 1; i < drawingPoints.length; i++) {
          const point = drawingPoints[i];
          if (point) {
            ctx.lineTo(point[0] * newScale, point[1] * newScale);
          }
        }
      }
      ctx.stroke();

      // Draw drawing vertices
      ctx.fillStyle = "#fbbf24";
      drawingPoints.forEach((point) => {
        ctx.beginPath();
        ctx.arc(point[0] * newScale, point[1] * newScale, 4, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    ctx.globalAlpha = 1;
  }, [trajectories, accesses, selectedAccess, scale, imageWidth, imageHeight, isDrawing, drawingPoints]);

  const drawGrid = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    scale: number
  ) => {
    ctx.strokeStyle = "#374151";
    ctx.lineWidth = 0.5;

    const gridSize = 100;
    for (let x = 0; x < width; x += gridSize * scale) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    for (let y = 0; y < height; y += gridSize * scale) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  };

  const getCardinalColor = (cardinal: Cardinal): string => {
    const colors: Record<Cardinal, string> = {
      N: "#ef4444", // Red
      S: "#3b82f6", // Blue
      E: "#10b981", // Green
      O: "#f59e0b", // Amber
    };
    return colors[cardinal];
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !selectedAccess) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;

    if (editable) {
      if (isDrawing) {
        setDrawingPoints([...drawingPoints, [x, y]]);
      }
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!editable || !selectedAccess) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;

    // Check if clicking on a vertex
    const access = accesses.find((a) => a.cardinal === selectedAccess);
    if (access && access.polygon) {
      for (let i = 0; i < access.polygon.length; i++) {
        const vertex = access.polygon[i];
        if (vertex) {
          const dx = vertex[0] - x;
          const dy = vertex[1] - y;
          if (Math.sqrt(dx * dx + dy * dy) < 10 / scale) {
            setDraggingVertex({ cardinal: selectedAccess, index: i });
            return;
          }
        }
      }
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggingVertex || !editable) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale;
    const y = (e.clientY - rect.top) / scale;

    const access = accesses.find((a) => a.cardinal === draggingVertex.cardinal);
    if (access && access.polygon) {
      const newPolygon = [...access.polygon];
      newPolygon[draggingVertex.index] = [x, y];
      onAccessPolygonChange(draggingVertex.cardinal, newPolygon);
    }
  };

  const handleCanvasMouseUp = () => {
    setDraggingVertex(null);
  };

  return (
    <div className="space-y-2">
      <canvas
        ref={canvasRef}
        width={imageWidth}
        height={imageHeight}
        onClick={handleCanvasClick}
        onMouseDown={handleCanvasMouseDown}
        onMouseMove={handleCanvasMouseMove}
        onMouseUp={handleCanvasMouseUp}
        onMouseLeave={handleCanvasMouseUp}
        className="w-full border-2 border-slate-300 rounded-lg bg-gray-900 cursor-crosshair"
        style={{ maxHeight: "600px", aspectRatio: `${imageWidth}/${imageHeight}` }}
      />
      <div className="text-xs text-slate-500">
        {isDrawing && selectedAccess ? (
          <p>
            Dibujando polígono para {selectedAccess} ({drawingPoints.length} puntos) -
            Click para agregar vértices, Enter para terminar
          </p>
        ) : (
          <p>
            Selecciona un acceso y arrastra los vértices para editarlos.
            {trajectories.length > 0 && ` (${trajectories.length} puntos de trayectoria)`}
          </p>
        )}
      </div>
    </div>
  );
};

export default TrajectoryCanvas;
