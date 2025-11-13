/**
 * TrajectoryCanvas - Versión con trayectorias conectadas
 * Muestra todas las trayectorias como líneas y permite marcar puntos cardinales
 */

import React, { useRef, useEffect, useState } from 'react';
import type { AccessPoint } from '@/store/setup';
import AccessDrawer from '@/components/Cardinals/AccessDrawer';
import { API_BASE_URL } from '@/config/api';

interface TrajectoryCanvasProps {
  accesses: AccessPoint[];
  mode: 'select' | 'mark_access' | 'draw_polygon';
  onModeChange: (mode: 'select' | 'mark_access' | 'draw_polygon') => void;
  onAccessClick: (x: number, y: number, polygon?: { x: number; y: number }[]) => void;
  onAccessMove: (id: string, x: number, y: number) => void;
  onAccessEdit: (access: AccessPoint) => void;
  onAccessDelete: (id: string) => void;
  onSave: () => void;
  onPolygonComplete?: (accessId: string, polygon: { x: number; y: number }[]) => void;
  datasetId: string;
}

interface TrajectoryPoint {
  x: number;
  y: number;
  frame: number;
}

interface TrajectoriesData {
  trajectories: Record<string, TrajectoryPoint[][]>;
  bounds: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
  };
  total_tracks: number;
  classes: string[];
}

const CLASS_COLORS: Record<string, string> = {
  car: '#3b82f6',
  motorcycle: '#ef4444',
  bus: '#10b981',
  truck_c1: '#f59e0b',
  truck_c2: '#8b5cf6',
  truck_c3: '#ec4899',
  bicycle: '#14b8a6',
  person: '#f97316',
};

const CARDINAL_COLORS: Record<string, string> = {
  N: '#3b82f6',
  S: '#10b981',
  E: '#f59e0b',
  O: '#ef4444',
};

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 700;
const MARGIN = 60;

export default function TrajectoryCanvas({
  accesses,
  mode,
  onModeChange,
  onAccessClick,
  onAccessMove,
  onAccessEdit,
  onAccessDelete,
  onSave,
  onPolygonComplete,
  datasetId,
}: TrajectoryCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [trajectoriesData, setTrajectoriesData] = useState<TrajectoriesData | null>(null);
  const [draggedAccess, setDraggedAccess] = useState<string | null>(null);
  const [showDetections, setShowDetections] = useState(true);
  const [selectedAccessForPolygon, setSelectedAccessForPolygon] = useState<string | null>(null);
  const [currentPolygon, setCurrentPolygon] = useState<{ x: number; y: number }[]>([]);
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  // Guardar funciones de transformación para convertir entre canvas y espacio de datos
  const transformRef = useRef<{
    canvasToData: (x: number, y: number) => { x: number; y: number };
    dataToCanvas: (x: number, y: number) => { x: number; y: number };
  } | null>(null);

  // Cargar trayectorias
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const res = await fetch(
          `${API_BASE_URL}/api/datasets/${datasetId}/trajectories?max_tracks=2000&sample_size=50000`
        );
        if (!res.ok) throw new Error('Error loading trajectories');

        const data: TrajectoriesData = await res.json();
        console.log('✓ Datos cargados:', data.total_tracks, 'trayectorias');
        setTrajectoriesData(data);
      } catch (err) {
        console.error('Error cargando datos:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [datasetId]);

  // Renderizar canvas
  useEffect(() => {
    if (loading || !canvasRef.current || !trajectoriesData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Configurar canvas
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = CANVAS_WIDTH * dpr;
    canvas.height = CANVAS_HEIGHT * dpr;
    canvas.style.width = `${CANVAS_WIDTH}px`;
    canvas.style.height = `${CANVAS_HEIGHT}px`;
    ctx.scale(dpr, dpr);

    // Limpiar
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Calcular bounds incluyendo trayectorias Y accesos (igual que LivePlaybackView)
    let minX = trajectoriesData.bounds.min_x;
    let maxX = trajectoriesData.bounds.max_x;
    let minY = trajectoriesData.bounds.min_y;
    let maxY = trajectoriesData.bounds.max_y;

    // Incluir accesos en los bounds
    accesses.forEach((acc) => {
      if (!isNaN(acc.x) && !isNaN(acc.y)) {
        minX = Math.min(minX, acc.x);
        maxX = Math.max(maxX, acc.x);
        minY = Math.min(minY, acc.y);
        maxY = Math.max(maxY, acc.y);
      }
    });

    const dataWidth = maxX - minX || 1;
    const dataHeight = maxY - minY || 1;

    // Calcular transformación (igual que LivePlaybackView)
    const scaleX = (CANVAS_WIDTH - MARGIN * 2) / dataWidth;
    const scaleY = (CANVAS_HEIGHT - MARGIN * 2) / dataHeight;
    const scale = Math.min(scaleX, scaleY);

    const offsetX = MARGIN + (CANVAS_WIDTH - MARGIN * 2 - dataWidth * scale) / 2;
    const offsetY = MARGIN + (CANVAS_HEIGHT - MARGIN * 2 - dataHeight * scale) / 2;

    const transformX = (x: number) => offsetX + (x - minX) * scale;
    const transformY = (y: number) => offsetY + (y - minY) * scale;

    // Guardar funciones de transformación inversas para convertir clicks
    transformRef.current = {
      dataToCanvas: (x: number, y: number) => ({
        x: transformX(x),
        y: transformY(y)
      }),
      canvasToData: (x: number, y: number) => ({
        x: minX + (x - offsetX) / scale,
        y: minY + (y - offsetY) / scale
      })
    };

    // Dibujar visualización de accesos (puntos de entrada/salida)
    if (showDetections) {
      const entryPoints: Array<{ x: number; y: number; color: string }> = [];
      const exitPoints: Array<{ x: number; y: number; color: string }> = [];

      Object.entries(trajectoriesData.trajectories).forEach(([className, tracks]) => {
        const color = CLASS_COLORS[className] || '#6b7280';

        tracks.forEach((track) => {
          if (track.length === 0) return;

          // Punto de entrada (primer punto)
          const firstPt = track[0];
          entryPoints.push({
            x: transformX(firstPt.x),
            y: transformY(firstPt.y),
            color: color
          });

          // Punto de salida (último punto)
          if (track.length > 1) {
            const lastPt = track[track.length - 1];
            exitPoints.push({
              x: transformX(lastPt.x),
              y: transformY(lastPt.y),
              color: color
            });
          }
        });
      });

      // Dibujar puntos de entrada (círculos verdes)
      entryPoints.forEach(pt => {
        ctx.fillStyle = hexToRgba('#10b981', 0.4);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
        ctx.fill();
      });

      // Dibujar puntos de salida (círculos rojos)
      exitPoints.forEach(pt => {
        ctx.fillStyle = hexToRgba('#ef4444', 0.4);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
        ctx.fill();
      });

      console.log('✓ Visualización:', entryPoints.length, 'entradas,', exitPoints.length, 'salidas');
    }

    // Dibujar accesos con gates y polígonos
    accesses.forEach((access) => {
      const color = CARDINAL_COLORS[access.cardinal_official || access.cardinal] || '#6b7280';
      const cardinal = access.cardinal_official || access.cardinal;

      // Dibujar polígono si existe
      const polygon = (access as any).polygon;
      if (polygon && polygon.length >= 3) {
        ctx.strokeStyle = color;
        ctx.fillStyle = hexToRgba(color, 0.2);
        ctx.lineWidth = 3;

        ctx.beginPath();
        polygon.forEach((point: { x: number; y: number }, i: number) => {
          const canvasPos = transformRef.current?.dataToCanvas(point.x, point.y);
          if (!canvasPos) return;

          if (i === 0) {
            ctx.moveTo(canvasPos.x, canvasPos.y);
          } else {
            ctx.lineTo(canvasPos.x, canvasPos.y);
          }
        });
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Dibujar puntos del polígono
        polygon.forEach((point: { x: number; y: number }) => {
          const canvasPos = transformRef.current?.dataToCanvas(point.x, point.y);
          if (!canvasPos) return;

          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(canvasPos.x, canvasPos.y, 5, 0, 2 * Math.PI);
          ctx.fill();
        });
      }

      // Determinar gate (ya existente o generar desde x,y)
      const GATE_LENGTH = 100;
      let gate = access.gate;

      if (!gate) {
        // No hay gate guardada, generar desde x,y
        if (isNaN(access.x) || isNaN(access.y)) return;

        if (cardinal === 'N' || cardinal === 'S') {
          gate = {
            x1: access.x - GATE_LENGTH / 2,
            y1: access.y,
            x2: access.x + GATE_LENGTH / 2,
            y2: access.y,
          };
        } else {
          gate = {
            x1: access.x,
            y1: access.y - GATE_LENGTH / 2,
            x2: access.x,
            y2: access.y + GATE_LENGTH / 2,
          };
        }
      }

      // Dibujar gate (línea gruesa)
      const p1 = transformRef.current?.dataToCanvas(gate.x1, gate.y1);
      const p2 = transformRef.current?.dataToCanvas(gate.x2, gate.y2);
      if (!p1 || !p2) return;

      ctx.strokeStyle = color;
      ctx.lineWidth = 6;
      ctx.shadowBlur = 8;
      ctx.shadowColor = color;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Centro de la gate (para label)
      const centerX = (p1.x + p2.x) / 2;
      const centerY = (p1.y + p2.y) / 2;

      // Círculo en el centro
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(centerX, centerY, 12, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'white';
      ctx.beginPath();
      ctx.arc(centerX, centerY, 9, 0, Math.PI * 2);
      ctx.fill();

      // Letra cardinal
      ctx.fillStyle = color;
      ctx.font = 'bold 14px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(access.cardinal_official || access.cardinal, centerX, centerY);

      // Etiqueta con nombre
      ctx.fillStyle = '#2c3e50';
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText(access.display_name, centerX, centerY + 25);
    });

    // Dibujar polígono en construcción
    if (currentPolygon.length > 0) {
      // Determinar color: si es para un acceso específico, usar su color; si no, usar azul genérico
      let color = '#667eea';
      if (selectedAccessForPolygon) {
        const access = accesses.find(a => a.id === selectedAccessForPolygon);
        if (access) {
          color = CARDINAL_COLORS[access.cardinal_official || access.cardinal] || '#6b7280';
        }
      }

      ctx.strokeStyle = color;
      ctx.fillStyle = hexToRgba(color, 0.3);
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);

      ctx.beginPath();
      currentPolygon.forEach((point, i) => {
        const canvasPos = transformRef.current?.dataToCanvas(point.x, point.y);
        if (!canvasPos) return;

        if (i === 0) {
          ctx.moveTo(canvasPos.x, canvasPos.y);
        } else {
          ctx.lineTo(canvasPos.x, canvasPos.y);
        }
      });
      ctx.stroke();
      ctx.setLineDash([]);

      // Dibujar puntos
      currentPolygon.forEach((point, i) => {
        const canvasPos = transformRef.current?.dataToCanvas(point.x, point.y);
        if (!canvasPos) return;

        ctx.fillStyle = hoveredPoint === i ? '#ffff00' : color;
        ctx.beginPath();
        ctx.arc(canvasPos.x, canvasPos.y, 7, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
      });
    }

  }, [loading, trajectoriesData, accesses, showDetections, currentPolygon, selectedAccessForPolygon, hoveredPoint]);

  // Handlers
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !transformRef.current) return;

    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    // Convertir coordenadas de canvas a coordenadas de datos
    const dataCoords = transformRef.current.canvasToData(canvasX, canvasY);

    if (mode === 'mark_access') {
      // Modo marcar acceso: ahora dibuja polígono directamente

      // Verificar si se hizo click cerca del primer punto (cerrar polígono)
      if (currentPolygon.length >= 3) {
        const firstPoint = currentPolygon[0];
        const firstCanvas = transformRef.current.dataToCanvas(firstPoint.x, firstPoint.y);
        const dist = Math.sqrt((canvasX - firstCanvas.x) ** 2 + (canvasY - firstCanvas.y) ** 2);

        if (dist < 15) {
          // Cerrar polígono: calcular centro y abrir modal
          const centerX = currentPolygon.reduce((sum, p) => sum + p.x, 0) / currentPolygon.length;
          const centerY = currentPolygon.reduce((sum, p) => sum + p.y, 0) / currentPolygon.length;

          console.log('✓ Polígono cerrado. Centro:', { centerX, centerY });
          console.log('✓ Polígono:', currentPolygon);

          // Llamar callback pasando centro y polígono
          onAccessClick(centerX, centerY, [...currentPolygon]);

          // Limpiar polígono
          setCurrentPolygon([]);
          return;
        }
      }

      // Agregar nuevo punto al polígono
      setCurrentPolygon([...currentPolygon, dataCoords]);

    } else if (mode === 'draw_polygon') {
      // Modo de dibujar polígono para acceso existente
      if (!selectedAccessForPolygon) return;

      // Verificar si se hizo click cerca del primer punto (cerrar polígono)
      if (currentPolygon.length >= 3) {
        const firstPoint = currentPolygon[0];
        const firstCanvas = transformRef.current.dataToCanvas(firstPoint.x, firstPoint.y);
        const dist = Math.sqrt((canvasX - firstCanvas.x) ** 2 + (canvasY - firstCanvas.y) ** 2);

        if (dist < 15) {
          // Cerrar polígono y guardarlo
          if (onPolygonComplete) {
            onPolygonComplete(selectedAccessForPolygon, [...currentPolygon]);
          }
          setCurrentPolygon([]);
          setSelectedAccessForPolygon(null);
          onModeChange('select');
          return;
        }
      }

      // Agregar nuevo punto
      setCurrentPolygon([...currentPolygon, dataCoords]);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode !== 'select') return;
    const canvas = canvasRef.current;
    if (!canvas || !transformRef.current) return;

    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    // Buscar acceso clickeado (comparar en espacio canvas)
    const clicked = accesses.find((acc) => {
      if (isNaN(acc.x) || isNaN(acc.y)) return false;

      // Convertir coordenadas de datos del acceso a canvas para comparar
      const canvasPos = transformRef.current?.dataToCanvas(acc.x, acc.y);
      if (!canvasPos) return false;

      const dx = canvasPos.x - canvasX;
      const dy = canvasPos.y - canvasY;
      return Math.sqrt(dx * dx + dy * dy) < 15;
    });

    if (clicked) setDraggedAccess(clicked.id);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !transformRef.current) return;

    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;

    // Convertir coordenadas de canvas a coordenadas de datos
    const dataCoords = transformRef.current.canvasToData(canvasX, canvasY);

    if (draggedAccess) {
      onAccessMove(draggedAccess, dataCoords.x, dataCoords.y);
    } else if (mode === 'draw_polygon' && currentPolygon.length > 0) {
      // Verificar si está cerca de algún punto del polígono
      const hovered = currentPolygon.findIndex((point) => {
        const canvasPos = transformRef.current?.dataToCanvas(point.x, point.y);
        if (!canvasPos) return false;
        const dist = Math.sqrt((canvasX - canvasPos.x) ** 2 + (canvasY - canvasPos.y) ** 2);
        return dist < 15;
      });

      setHoveredPoint(hovered >= 0 ? hovered : null);
    }
  };

  const handleMouseUp = () => setDraggedAccess(null);

  return (
    <div style={{ display: 'flex', gap: '0' }}>
      <div style={{ flex: 1 }}>
        {/* Toolbar */}
        <div
          style={{
            padding: '16px',
            background: 'white',
            borderRadius: '8px',
            marginBottom: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: mode === 'draw_polygon' ? '12px' : '0' }}>
            <button
              onClick={() => {
                onModeChange('select');
                setCurrentPolygon([]);
                setSelectedAccessForPolygon(null);
              }}
              style={{
                padding: '10px 20px',
                background: mode === 'select' ? '#667eea' : 'white',
                color: mode === 'select' ? 'white' : '#6b7280',
                border: `2px solid ${mode === 'select' ? '#667eea' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              👆 Seleccionar
            </button>
            <button
              onClick={() => {
                onModeChange('mark_access');
                setCurrentPolygon([]);
                setSelectedAccessForPolygon(null);
              }}
              style={{
                padding: '10px 20px',
                background: mode === 'mark_access' ? '#667eea' : 'white',
                color: mode === 'mark_access' ? 'white' : '#6b7280',
                border: `2px solid ${mode === 'mark_access' ? '#667eea' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              📍 Marcar Acceso
            </button>

            <div style={{ flex: 1 }} />

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showDetections}
                onChange={(e) => setShowDetections(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <span style={{ fontSize: '14px', color: '#2c3e50' }}>Mostrar Puntos de Acceso</span>
            </label>
          </div>

          {/* Instrucciones para modo mark_access */}
          {mode === 'mark_access' && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: '#e0f2fe',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#0c4a6e'
            }}>
              <strong>📍 Marcar nuevo acceso:</strong> Dibuja un polígono haciendo click en el canvas para delimitar la zona.
              {currentPolygon.length >= 3 && ' Click en el primer punto para cerrar y configurar el cardinal.'}
              {currentPolygon.length > 0 && (
                <>
                  {' '}
                  <button
                    onClick={() => {
                      setCurrentPolygon([]);
                      onModeChange('select');
                    }}
                    style={{
                      marginLeft: '8px',
                      padding: '4px 8px',
                      background: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '11px',
                      cursor: 'pointer',
                    }}
                  >
                    Cancelar
                  </button>
                </>
              )}
            </div>
          )}

          {/* Panel de selección de acceso para polígono */}
          {accesses.length > 0 && (
            <div style={{
              padding: '12px',
              background: '#f9fafb',
              borderRadius: '6px',
              marginTop: '12px'
            }}>
              <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '8px', color: '#2c3e50' }}>
                🔲 Dibujar Zona Poligonal:
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {accesses.map((access) => {
                  const color = CARDINAL_COLORS[access.cardinal_official || access.cardinal] || '#6b7280';
                  const hasPolygon = !!(access as any).polygon && (access as any).polygon.length >= 3;
                  const isSelected = selectedAccessForPolygon === access.id;

                  return (
                    <button
                      key={access.id}
                      onClick={() => {
                        if (selectedAccessForPolygon === access.id) {
                          // Cancelar
                          setSelectedAccessForPolygon(null);
                          setCurrentPolygon([]);
                          onModeChange('select');
                        } else {
                          // Seleccionar acceso y entrar en modo dibujo
                          setSelectedAccessForPolygon(access.id);
                          setCurrentPolygon([]);
                          onModeChange('draw_polygon');
                        }
                      }}
                      style={{
                        padding: '8px 12px',
                        background: isSelected ? color : 'white',
                        color: isSelected ? 'white' : '#2c3e50',
                        border: `2px solid ${color}`,
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      {access.cardinal_official || access.cardinal} - {access.display_name}
                      {hasPolygon && ' ✓'}
                    </button>
                  );
                })}
              </div>
              {mode === 'draw_polygon' && selectedAccessForPolygon && (
                <div style={{
                  marginTop: '8px',
                  padding: '8px',
                  background: '#e0f2fe',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#0c4a6e'
                }}>
                  <strong>Instrucciones:</strong> Haz click en el canvas para agregar puntos.
                  {currentPolygon.length >= 3 && ' Click en el primer punto para cerrar el polígono.'}
                  {currentPolygon.length > 0 && (
                    <>
                      {' '}
                      <button
                        onClick={() => {
                          setCurrentPolygon([]);
                        }}
                        style={{
                          marginLeft: '8px',
                          padding: '4px 8px',
                          background: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '11px',
                          cursor: 'pointer',
                        }}
                      >
                        Cancelar
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Canvas */}
        <div
          style={{
            background: 'white',
            borderRadius: '12px',
            padding: '20px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: `${CANVAS_HEIGHT + 40}px`,
          }}
        >
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>⏳</div>
              <p>Cargando trayectorias...</p>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              style={{
                display: 'block',
                cursor: mode === 'mark_access' || mode === 'draw_polygon' ? 'crosshair' : mode === 'select' ? 'grab' : 'default',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                backgroundColor: '#ffffff',
              }}
            />
          )}
        </div>

        {/* Leyenda */}
        {showDetections && trajectoriesData && !loading && (
          <div
            style={{
              marginTop: '16px',
              padding: '16px',
              background: 'white',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#2c3e50', marginBottom: '12px' }}>
              📍 Visualización de Accesos ({trajectoriesData.total_tracks} trayectorias)
            </div>
            <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '12px' }}>
              Esta visualización muestra los puntos de entrada y salida de los vehículos, lo que te ayudará a identificar y marcar los accesos de la intersección.
            </div>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    background: '#10b981',
                    borderRadius: '50%',
                  }}
                />
                <span style={{ fontSize: '13px', color: '#6b7280', fontWeight: '500' }}>
                  Entradas (donde aparecen los vehículos)
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    background: '#ef4444',
                    borderRadius: '50%',
                  }}
                />
                <span style={{ fontSize: '13px', color: '#6b7280', fontWeight: '500' }}>
                  Salidas (donde desaparecen los vehículos)
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Drawer */}
      <AccessDrawer
        accesses={accesses}
        onEdit={onAccessEdit}
        onDelete={onAccessDelete}
        canSave={accesses.length >= 2}
        onSave={onSave}
      />
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
