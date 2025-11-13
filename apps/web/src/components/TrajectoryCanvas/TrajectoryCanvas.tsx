/**
 * Componente compartido de renderizado de trayectorias
 * Renderiza todas las trayectorias como líneas densas con pan/zoom/fit
 */

import React, { useRef, useEffect, useCallback, useState } from 'react';

export interface Track {
  id: string;
  cls: string;
  polyline: [number, number][];
}

export interface AccessPoint {
  id: string;
  display_name: string;
  cardinal: string;
  cardinal_official: string;
  x: number;
  y: number;
  gate?: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
}

export interface ViewState {
  x: number;
  y: number;
  scale: number;
}

interface TrajectoryCanvasProps {
  tracks: Track[];
  accesses?: AccessPoint[];
  width?: number;
  height?: number;
  colorMode?: 'class' | 'single' | 'heat';
  lineWidth?: number;
  opacity?: number;
  panZoomEnabled?: boolean;
  onViewChange?: (view: ViewState) => void;
  initialView?: ViewState;
  backgroundColor?: string;
  showAccessPoints?: boolean;
  highlightedTrackIds?: string[];
}

const CLASE_COLORS: Record<string, string> = {
  car: '#3498db',
  motorcycle: '#e74c3c',
  bus: '#f39c12',
  truck: '#9b59b6',
  bicycle: '#2ecc71',
  person: '#1abc9c',
};

function hexToRgba(hex: string | undefined, alpha: number): string {
  if (!hex || !hex.startsWith('#')) {
    hex = '#888888';
  }
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export default function TrajectoryCanvas({
  tracks,
  accesses = [],
  width = 1200,
  height = 600,
  colorMode = 'class',
  lineWidth = 1.5,
  opacity = 0.15,
  panZoomEnabled = true,
  onViewChange,
  initialView,
  backgroundColor = '#000000',
  showAccessPoints = true,
  highlightedTrackIds = [],
}: TrajectoryCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Estado de vista (pan/zoom)
  const [viewState, setViewState] = useState<ViewState>(
    initialView || { x: 0, y: 0, scale: 1 }
  );

  // Estado de interacción
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState<{ x: number; y: number } | null>(null);

  // Calcular bounds de todos los datos
  const calculateBounds = useCallback(() => {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    // Bounds de accesos
    accesses.forEach((acc) => {
      if (acc.gate) {
        minX = Math.min(minX, acc.gate.x1, acc.gate.x2);
        maxX = Math.max(maxX, acc.gate.x1, acc.gate.x2);
        minY = Math.min(minY, acc.gate.y1, acc.gate.y2);
        maxY = Math.max(maxY, acc.gate.y1, acc.gate.y2);
      } else if (!isNaN(acc.x) && !isNaN(acc.y)) {
        minX = Math.min(minX, acc.x);
        maxX = Math.max(maxX, acc.x);
        minY = Math.min(minY, acc.y);
        maxY = Math.max(maxY, acc.y);
      }
    });

    // Bounds de trayectorias
    tracks.forEach((track) => {
      track.polyline.forEach(([x, y]) => {
        if (!isNaN(x) && !isNaN(y)) {
          minX = Math.min(minX, x);
          maxX = Math.max(maxX, x);
          minY = Math.min(minY, y);
          maxY = Math.max(maxY, y);
        }
      });
    });

    return { minX, maxX, minY, maxY };
  }, [tracks, accesses]);

  // Función para ajustar vista (Fit)
  const fitToView = useCallback(() => {
    const bounds = calculateBounds();
    if (!isFinite(bounds.minX)) return;

    const padding = 60;
    const dataWidth = bounds.maxX - bounds.minX || 1;
    const dataHeight = bounds.maxY - bounds.minY || 1;
    const scaleX = (width - padding * 2) / dataWidth;
    const scaleY = (height - padding * 2) / dataHeight;
    const scale = Math.min(scaleX, scaleY);

    const x = padding + (width - padding * 2 - dataWidth * scale) / 2 - bounds.minX * scale;
    const y = padding + (height - padding * 2 - dataHeight * scale) / 2 - bounds.minY * scale;

    const newView = { x, y, scale };
    setViewState(newView);
    onViewChange?.(newView);
  }, [width, height, calculateBounds, onViewChange]);

  // Función para resetear vista
  const resetView = useCallback(() => {
    const newView = { x: 0, y: 0, scale: 1 };
    setViewState(newView);
    onViewChange?.(newView);
  }, [onViewChange]);

  // Función para hacer zoom
  const zoom = useCallback((delta: number, centerX?: number, centerY?: number) => {
    setViewState((prev) => {
      const zoomFactor = delta > 0 ? 1.1 : 0.9;
      const newScale = Math.max(0.1, Math.min(10, prev.scale * zoomFactor));

      // Si se proporciona un centro, zoom hacia ese punto
      if (centerX !== undefined && centerY !== undefined) {
        const scaleChange = newScale / prev.scale;
        const newX = centerX - (centerX - prev.x) * scaleChange;
        const newY = centerY - (centerY - prev.y) * scaleChange;
        return { x: newX, y: newY, scale: newScale };
      }

      return { ...prev, scale: newScale };
    });
  }, []);

  // Función de transformación de coordenadas
  const transform = useCallback(
    (x: number, y: number): [number, number] => {
      return [
        viewState.x + x * viewState.scale,
        viewState.y + y * viewState.scale,
      ];
    },
    [viewState]
  );

  // Dibujar canvas
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Limpiar fondo
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Dibujar todas las trayectorias
    tracks.forEach((track) => {
      const isHighlighted = highlightedTrackIds.includes(track.id);
      const color = colorMode === 'class'
        ? (CLASE_COLORS[track.cls] || '#95a5a6')
        : '#888888';

      ctx.strokeStyle = hexToRgba(color, isHighlighted ? 0.6 : opacity);
      ctx.lineWidth = isHighlighted ? lineWidth * 2 : lineWidth;
      ctx.beginPath();

      track.polyline.forEach(([px, py], i) => {
        if (isNaN(px) || isNaN(py)) return;
        const [x, y] = transform(px, py);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();
    });

    // Dibujar puntos de acceso
    if (showAccessPoints) {
      accesses.forEach((access) => {
        // Si tiene gate, dibujar línea
        if (access.gate) {
          const [x1, y1] = transform(access.gate.x1, access.gate.y1);
          const [x2, y2] = transform(access.gate.x2, access.gate.y2);

          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 4;
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();

          // Círculos en los extremos
          ctx.fillStyle = '#ffffff';
          ctx.beginPath();
          ctx.arc(x1, y1, 6, 0, Math.PI * 2);
          ctx.fill();
          ctx.beginPath();
          ctx.arc(x2, y2, 6, 0, Math.PI * 2);
          ctx.fill();

          // Label en el centro
          const [cx, cy] = transform(
            (access.gate.x1 + access.gate.x2) / 2,
            (access.gate.y1 + access.gate.y2) / 2
          );

          ctx.fillStyle = '#000000';
          ctx.font = 'bold 14px Arial';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';

          // Fondo blanco para el texto
          const textWidth = ctx.measureText(access.cardinal_official || access.cardinal).width;
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(cx - textWidth / 2 - 4, cy - 10, textWidth + 8, 20);

          ctx.fillStyle = '#000000';
          ctx.fillText(access.cardinal_official || access.cardinal, cx, cy);

          ctx.fillStyle = '#ecf0f1';
          ctx.font = 'bold 12px Arial';
          ctx.fillText(access.display_name, cx, cy + 25);
        } else {
          // Punto simple (legacy)
          if (isNaN(access.x) || isNaN(access.y)) return;
          const [x, y] = transform(access.x, access.y);

          ctx.beginPath();
          ctx.arc(x, y, 20, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
          ctx.strokeStyle = '#ecf0f1';
          ctx.lineWidth = 3;
          ctx.stroke();

          ctx.fillStyle = '#000000';
          ctx.font = 'bold 16px Arial';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(access.cardinal_official || access.cardinal, x, y);

          ctx.fillStyle = '#ecf0f1';
          ctx.font = 'bold 12px Arial';
          ctx.fillText(access.display_name, x, y + 35);
        }
      });
    }
  }, [
    tracks,
    accesses,
    transform,
    backgroundColor,
    colorMode,
    lineWidth,
    opacity,
    showAccessPoints,
    highlightedTrackIds,
  ]);

  // Redibujar cuando cambien las dependencias
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  // Fit to view inicial
  useEffect(() => {
    if (tracks.length > 0 && !initialView) {
      fitToView();
    }
  }, [tracks.length, initialView]);

  // Manejo de eventos de mouse (pan/zoom)
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!panZoomEnabled) return;
    setIsPanning(true);
    setPanStart({ x: e.clientX - viewState.x, y: e.clientY - viewState.y });
  }, [panZoomEnabled, viewState]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isPanning || !panStart) return;
    const newView = {
      ...viewState,
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y,
    };
    setViewState(newView);
    onViewChange?.(newView);
  }, [isPanning, panStart, viewState, onViewChange]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
    setPanStart(null);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    if (!panZoomEnabled) return;
    e.preventDefault();

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    zoom(e.deltaY > 0 ? -1 : 1, mouseX, mouseY);
  }, [panZoomEnabled, zoom]);

  // Atajos de teclado
  useEffect(() => {
    if (!panZoomEnabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'f' || e.key === 'F') {
        fitToView();
      } else if (e.key === '0') {
        resetView();
      } else if (e.key === '+' || e.key === '=') {
        zoom(1);
      } else if (e.key === '-' || e.key === '_') {
        zoom(-1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [panZoomEnabled, fitToView, resetView, zoom]);

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{
          cursor: isPanning ? 'grabbing' : panZoomEnabled ? 'grab' : 'default',
          maxWidth: '100%',
          height: 'auto',
          borderRadius: '4px',
          border: '2px solid #2c3e50',
        }}
      />

      {panZoomEnabled && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            display: 'flex',
            gap: '8px',
            flexDirection: 'column',
          }}
        >
          <button
            onClick={fitToView}
            title="Fit to view (F)"
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.9)',
              color: '#2c3e50',
              border: '2px solid #3498db',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            🔍 Fit (F)
          </button>
          <button
            onClick={() => zoom(1)}
            title="Zoom in (+)"
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.9)',
              color: '#2c3e50',
              border: '2px solid #3498db',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            ➕ Zoom (+)
          </button>
          <button
            onClick={() => zoom(-1)}
            title="Zoom out (-)"
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.9)',
              color: '#2c3e50',
              border: '2px solid #3498db',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            ➖ Zoom (-)
          </button>
          <button
            onClick={resetView}
            title="Reset view (0)"
            style={{
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.9)',
              color: '#2c3e50',
              border: '2px solid #3498db',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            🔄 Reset (0)
          </button>
        </div>
      )}

      {panZoomEnabled && (
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            padding: '8px 12px',
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            borderRadius: '6px',
            fontSize: '11px',
            fontFamily: 'monospace',
          }}
        >
          Zoom: {(viewState.scale * 100).toFixed(0)}% | Pan: ({viewState.x.toFixed(0)}, {viewState.y.toFixed(0)})
        </div>
      )}
    </div>
  );
}
