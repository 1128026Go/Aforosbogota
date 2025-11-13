/**
 * Editor de Zonas Poligonales para Puntos Cardinales
 * Permite dibujar polígonos completos para definir áreas de acceso N/S/E/O
 */

import React, { useRef, useEffect, useState } from 'react';

interface Point {
  x: number;
  y: number;
}

interface CardinalZone {
  id: string;
  cardinal: 'N' | 'S' | 'E' | 'O';
  display_name: string;
  polygon: Point[]; // Array de puntos del polígono
  color: string;
}

interface CardinalZoneEditorProps {
  videoSrc: string;
  zones: CardinalZone[];
  onZonesChange: (zones: CardinalZone[]) => void;
  videoWidth?: number;
  videoHeight?: number;
}

export const CardinalZoneEditor: React.FC<CardinalZoneEditorProps> = ({
  videoSrc,
  zones,
  onZonesChange,
  videoWidth = 1280,
  videoHeight = 720,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [selectedCardinal, setSelectedCardinal] = useState<'N' | 'S' | 'E' | 'O' | null>('N');
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPolygon, setCurrentPolygon] = useState<Point[]>([]);
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  const cardinalColors = {
    N: '#3b82f6',  // Azul
    S: '#ef4444',  // Rojo
    E: '#10b981',  // Verde
    O: '#f59e0b',  // Naranja
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      redrawCanvas();
    };

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    return () => video.removeEventListener('loadedmetadata', handleLoadedMetadata);
  }, []);

  useEffect(() => {
    redrawCanvas();
  }, [zones, currentPolygon, hoveredPoint]);

  const redrawCanvas = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Dibujar frame del video
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Dibujar zonas guardadas
    zones.forEach((zone) => {
      if (zone.polygon.length < 2) return;

      ctx.strokeStyle = zone.color;
      ctx.fillStyle = zone.color + '40'; // Transparencia
      ctx.lineWidth = 3;

      ctx.beginPath();
      zone.polygon.forEach((point, i) => {
        if (i === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Dibujar puntos
      zone.polygon.forEach((point, i) => {
        ctx.fillStyle = zone.color;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
        ctx.fill();
      });

      // Etiqueta
      if (zone.polygon.length > 0) {
        const centerX = zone.polygon.reduce((sum, p) => sum + p.x, 0) / zone.polygon.length;
        const centerY = zone.polygon.reduce((sum, p) => sum + p.y, 0) / zone.polygon.length;

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px Arial';
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 3;
        ctx.strokeText(zone.cardinal, centerX, centerY);
        ctx.fillText(zone.cardinal, centerX, centerY);
      }
    });

    // Dibujar polígono en construcción
    if (currentPolygon.length > 0 && selectedCardinal) {
      const color = cardinalColors[selectedCardinal];
      ctx.strokeStyle = color;
      ctx.fillStyle = color + '40';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);

      ctx.beginPath();
      currentPolygon.forEach((point, i) => {
        if (i === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.stroke();
      ctx.setLineDash([]);

      // Dibujar puntos
      currentPolygon.forEach((point, i) => {
        ctx.fillStyle = hoveredPoint === i ? '#ffff00' : color;
        ctx.beginPath();
        ctx.arc(point.x, point.y, 7, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
      });
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!selectedCardinal) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // Verificar si se hizo click cerca del primer punto (cerrar polígono)
    if (currentPolygon.length >= 3) {
      const firstPoint = currentPolygon[0];
      const dist = Math.sqrt((x - firstPoint.x) ** 2 + (y - firstPoint.y) ** 2);

      if (dist < 15) {
        // Cerrar polígono y guardarlo
        finishPolygon();
        return;
      }
    }

    // Agregar nuevo punto
    setCurrentPolygon([...currentPolygon, { x, y }]);
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (currentPolygon.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // Verificar si está cerca de algún punto
    const hovered = currentPolygon.findIndex((point) => {
      const dist = Math.sqrt((x - point.x) ** 2 + (y - point.y) ** 2);
      return dist < 15;
    });

    setHoveredPoint(hovered >= 0 ? hovered : null);
  };

  const finishPolygon = () => {
    if (!selectedCardinal || currentPolygon.length < 3) return;

    const existingZoneIndex = zones.findIndex(z => z.cardinal === selectedCardinal);
    const newZone: CardinalZone = {
      id: `zone_${selectedCardinal}_${Date.now()}`,
      cardinal: selectedCardinal,
      display_name: getCardinalName(selectedCardinal),
      polygon: [...currentPolygon],
      color: cardinalColors[selectedCardinal],
    };

    if (existingZoneIndex >= 0) {
      // Reemplazar zona existente
      const newZones = [...zones];
      newZones[existingZoneIndex] = newZone;
      onZonesChange(newZones);
    } else {
      // Agregar nueva zona
      onZonesChange([...zones, newZone]);
    }

    setCurrentPolygon([]);
  };

  const cancelPolygon = () => {
    setCurrentPolygon([]);
  };

  const deleteZone = (cardinal: 'N' | 'S' | 'E' | 'O') => {
    onZonesChange(zones.filter(z => z.cardinal !== cardinal));
  };

  const getCardinalName = (cardinal: 'N' | 'S' | 'E' | 'O') => {
    const names = { N: 'Norte', S: 'Sur', E: 'Este', O: 'Oeste' };
    return names[cardinal];
  };

  return (
    <div style={{ display: 'flex', gap: '20px' }}>
      {/* Panel de controles */}
      <div style={{ width: '250px' }}>
        <h3 style={{ marginBottom: '16px' }}>Editor de Zonas Cardinales</h3>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Seleccionar Cardinal:
          </label>
          {(['N', 'S', 'E', 'O'] as const).map((cardinal) => {
            const hasZone = zones.some(z => z.cardinal === cardinal);
            return (
              <button
                key={cardinal}
                onClick={() => setSelectedCardinal(cardinal)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '10px',
                  marginBottom: '8px',
                  backgroundColor: selectedCardinal === cardinal ? cardinalColors[cardinal] : '#f3f4f6',
                  color: selectedCardinal === cardinal ? 'white' : '#000',
                  border: `2px solid ${cardinalColors[cardinal]}`,
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
              >
                {cardinal} - {getCardinalName(cardinal)} {hasZone && '✓'}
              </button>
            );
          })}
        </div>

        <div style={{
          padding: '12px',
          background: '#e0f2fe',
          borderRadius: '6px',
          marginBottom: '16px',
          fontSize: '13px',
        }}>
          <strong>Instrucciones:</strong>
          <ol style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
            <li>Selecciona un cardinal (N/S/E/O)</li>
            <li>Haz click en el canvas para crear puntos</li>
            <li>Click en el primer punto para cerrar</li>
            <li>El polígono define el área de ese acceso</li>
          </ol>
        </div>

        {currentPolygon.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <p style={{ marginBottom: '8px' }}>
              Puntos: {currentPolygon.length} {currentPolygon.length >= 3 && '(Click en el primer punto para cerrar)'}
            </p>
            <button
              onClick={cancelPolygon}
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Cancelar Polígono
            </button>
          </div>
        )}

        <div>
          <strong>Zonas Definidas:</strong>
          {zones.length === 0 ? (
            <p style={{ color: '#6b7280', fontSize: '13px', marginTop: '8px' }}>
              Ninguna zona definida aún
            </p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, marginTop: '8px' }}>
              {zones.map((zone) => (
                <li key={zone.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px',
                  marginBottom: '4px',
                  background: '#f9fafb',
                  borderRadius: '4px',
                }}>
                  <span>
                    <span style={{
                      display: 'inline-block',
                      width: '20px',
                      height: '20px',
                      backgroundColor: zone.color,
                      marginRight: '8px',
                      borderRadius: '3px',
                    }} />
                    {zone.cardinal} - {zone.polygon.length} puntos
                  </span>
                  <button
                    onClick={() => deleteZone(zone.cardinal)}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px',
                    }}
                  >
                    Borrar
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Canvas de dibujo */}
      <div>
        <video
          ref={videoRef}
          src={videoSrc}
          style={{ display: 'none' }}
          muted
        />
        <canvas
          ref={canvasRef}
          width={videoWidth}
          height={videoHeight}
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          style={{
            border: '2px solid #d1d5db',
            borderRadius: '8px',
            cursor: 'crosshair',
            maxWidth: '100%',
            height: 'auto',
          }}
        />
      </div>
    </div>
  );
};
