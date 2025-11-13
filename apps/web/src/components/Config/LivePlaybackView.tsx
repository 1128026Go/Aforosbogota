/**
 * Reproductor de Aforo en Vivo
 * Paso 3: Reproducción en tiempo real con conteo dinámico por intervalos de 15 minutos
 */

import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
// import { AforoMovimientosTabs } from '../aforos/AforoMovimientosTabs';
import { procesarEventosHastaFrame } from '@/lib/procesarAforoEnVivo';
import { API_BASE_URL } from '@/config/api';
import { isPersona } from '@/lib/movimientos';
import TrajectoryEditModal from './TrajectoryEditModal';

interface PlaybackEvent {
  track_id: string;
  class: string;
  frame_entry: number;
  frame_exit: number;
  timestamp_entry: string;
  timestamp_exit: string;
  origin_access: string;
  dest_access: string;
  origin_cardinal: string;
  dest_cardinal: string;
  // Algunos datasets antiguos usan destination_cardinal
  destination_cardinal?: string;
  mov_rilsa: number;
  positions: [number, number][];
  confidence: number;
  hide_in_pdf?: boolean;
}

interface PlaybackData {
  events: PlaybackEvent[];
  metadata: {
    dataset_id: string;
    total_tracks: number;
    total_events: number;
    fps: number;
    total_frames: number;
  };
}

const CLASE_EMOJIS: Record<string, string> = {
  car: '🚗',
  motorcycle: '🏍️',
  bus: '🚌',
  truck: '🚚',
  bicycle: '🚲',
  person: '🚶',
};

const CLASE_LABELS: Record<string, string> = {
  car: 'Auto',
  motorcycle: 'Moto',
  bus: 'Bus',
  truck: 'Camión',
  bicycle: 'Bici',
  person: 'Peatón',
};

const CLASE_COLORS: Record<string, string> = {
  car: '#3498db',           // Azul
  motorcycle: '#e74c3c',    // Rojo
  bus: '#f39c12',           // Naranja
  truck: '#9b59b6',         // Morado
  bicycle: '#2ecc71',       // Verde
  person: '#1abc9c',        // Turquesa
};

// Nota: CLASES y RILSA_CODES no se usan directamente en este componente

interface AccessPoint {
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
  polygon?: Array<{ x: number; y: number }>;
}

// Función helper para convertir hex a rgba
function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function formatRilsaCode(code: number): string {
  if (code >= 91 && code <= 94) return `R9.${code - 90}`;
  if (code >= 101 && code <= 104) return `R10.${code - 100}`;
  return `R${code}`;
}

// Agrupar eventos por intervalos de 15 minutos
function groupEventsByInterval(events: PlaybackEvent[]): Map<string, Map<string, number>> {
  const intervalMap = new Map<string, Map<string, number>>();

  events.forEach((event) => {
    const exitDate = new Date(event.timestamp_exit);
    const intervalStart = new Date(exitDate);
    intervalStart.setMinutes(Math.floor(intervalStart.getMinutes() / 15) * 15, 0, 0);
    // Formato: solo HH:MM (tiempo relativo)
    const intervalKey = intervalStart.toISOString().substring(11, 16); // "HH:MM"

    if (!intervalMap.has(intervalKey)) {
      intervalMap.set(intervalKey, new Map());
    }

    const counts = intervalMap.get(intervalKey)!;
    const simpleKey = `${event.mov_rilsa}_${event.class}`;
    counts.set(simpleKey, (counts.get(simpleKey) || 0) + 1);
  });

  return intervalMap;
}

export default function LivePlaybackView({ datasetId }: { datasetId: string }) {
  const [playbackData, setPlaybackData] = useState<PlaybackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // Multiplier (1x, 2x, 5x, 10x, 100x, 300x)
  const baseFps = 30; // FPS base del video
  const [activeEvents, setActiveEvents] = useState<PlaybackEvent[]>([]);
  const [accesses, setAccesses] = useState<AccessPoint[]>([]);
  const [selectedInterval, setSelectedInterval] = useState<string>('');
  const [selectedClass, setSelectedClass] = useState<string | null>(null); // Filtro por clase
  const [selectedMovimiento, setSelectedMovimiento] = useState<number | null>(null); // Filtro por movimiento RILSA
  const [_showDirectAforo, setShowDirectAforo] = useState(false); // Mostrar aforo directo (valor no usado)
  const [showInteractiveOverlay, setShowInteractiveOverlay] = useState(false);

  // Estados para modal de edición
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedTrajectory, setSelectedTrajectory] = useState<PlaybackEvent | null>(null);
  const [corrections, setCorrections] = useState<Record<string, any>>({});

  // Compatible con browser y Node - usar ReturnType para evitar conflictos de tipos
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const backgroundCanvasRef = useRef<HTMLCanvasElement | null>(null); // Canvas para trayectorias de fondo

  // Precalcular mapas de accesos por cardinal oficial
  const accessesByCardinal = useMemo(() => {
    const map = new Map<string, AccessPoint>();
    accesses.forEach((acc) => {
      if (acc.cardinal_official) {
        map.set(acc.cardinal_official, acc);
      }
    });
    return map;
  }, [accesses]);

  const isPointInsidePolygon = (point: { x: number; y: number }, polygon: Array<{ x: number; y: number }>) => {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].x;
      const yi = polygon[i].y;
      const xj = polygon[j].x;
      const yj = polygon[j].y;

      const intersect =
        (yi > point.y) !== (yj > point.y) &&
        point.x <
          ((xj - xi) * (point.y - yi)) / (yj - yi + (yj === yi ? 1e-9 : 0)) +
            xi;
      if (intersect) inside = !inside;
    }
    return inside;
  };

  // Adaptar accesos al tipo esperado por AforoMovimientosTabs (gate obligatorio)
  const cardinalsForTabs = useMemo(() => {
    return accesses
      .filter((a) => !!a.gate)
      .map((a) => ({
        id: a.id,
        display_name: a.display_name,
        cardinal_official: a.cardinal_official,
        gate: a.gate!,
      }));
  }, [accesses]);

  const eventMatchesFiltro = useCallback(
    (event: PlaybackEvent) => {
      if (selectedClass && event.class !== selectedClass) {
        return false;
      }
      if (selectedMovimiento !== null) {
        if (Number(event.mov_rilsa) !== Number(selectedMovimiento)) {
          return false;
        }
      }

      const eventOrigin = event.origin_cardinal;
      const eventDest = event.dest_cardinal || event.destination_cardinal;
      const originAccess = eventOrigin ? accessesByCardinal.get(eventOrigin) : undefined;
      const destAccess = eventDest ? accessesByCardinal.get(eventDest) : undefined;

      if (originAccess && originAccess.polygon && originAccess.polygon.length >= 3) {
        const entryPoint = event.positions[0];
        if (!isPointInsidePolygon({ x: entryPoint[0], y: entryPoint[1] }, originAccess.polygon)) {
          return false;
        }
      }
      if (destAccess && destAccess.polygon && destAccess.polygon.length >= 3) {
        const exitPoint = event.positions[event.positions.length - 1];
        if (!isPointInsidePolygon({ x: exitPoint[0], y: exitPoint[1] }, destAccess.polygon)) {
          return false;
        }
      }
      return true;
    },
    [selectedClass, selectedMovimiento, accessesByCardinal]
  );

  // Definimos eventsForDisplay como función para evitar depender de orden de hooks y minimizar riesgo de TDZ en bundle minificado
  const getEventsForDisplay = useCallback((): PlaybackEvent[] => {
    if (!playbackData) return [];
    return playbackData.events.filter(
      (event) => !event.hide_in_pdf && eventMatchesFiltro(event)
    );
  }, [playbackData, eventMatchesFiltro]);

  // Memo del resultado final (mantiene semántica previa)
  const eventsForDisplay = useMemo(() => getEventsForDisplay(), [getEventsForDisplay]);

  const dataBounds = useMemo(() => {
    if (!playbackData || playbackData.events.length === 0) {
      return null;
    }

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;

    accesses.forEach((acc) => {
      minX = Math.min(minX, acc.x ?? 0);
      maxX = Math.max(maxX, acc.x ?? 0);
      minY = Math.min(minY, acc.y ?? 0);
      maxY = Math.max(maxY, acc.y ?? 0);
      if (acc.polygon) {
        acc.polygon.forEach((point) => {
          minX = Math.min(minX, point.x);
          maxX = Math.max(maxX, point.x);
          minY = Math.min(minY, point.y);
          maxY = Math.max(maxY, point.y);
        });
      }
      if (acc.gate) {
        minX = Math.min(minX, acc.gate.x1, acc.gate.x2);
        maxX = Math.max(maxX, acc.gate.x1, acc.gate.x2);
        minY = Math.min(minY, acc.gate.y1, acc.gate.y2);
        maxY = Math.max(maxY, acc.gate.y1, acc.gate.y2);
      }
    });

  const currentDisplayEvents = eventsForDisplay;
  const sourceEvents = currentDisplayEvents.length > 0 ? currentDisplayEvents : playbackData.events;

    sourceEvents.forEach((event) => {
      event.positions.forEach(([x, y]) => {
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
      });
    });

    if (!Number.isFinite(minX) || !Number.isFinite(maxX) || !Number.isFinite(minY) || !Number.isFinite(maxY)) {
      return null;
    }

    return { minX, maxX, minY, maxY };
  }, [playbackData, accesses, eventsForDisplay]);

  // Obtener lista de movimientos RILSA únicos
  const movimientosUnicos = useMemo(() => {
    if (!playbackData) return [];
    const movSet = new Set<number>();
    playbackData.events.forEach(event => movSet.add(event.mov_rilsa));
    return Array.from(movSet).sort((a, b) => a - b);
  }, [playbackData]);

  // Cargar datos de playback y accesos
  useEffect(() => {
    const load = async () => {
      await loadAccesses();
      await loadPlaybackData();
    };
    load();
  }, [datasetId]);

  // Reproducción automática
  useEffect(() => {
    if (isPlaying && playbackData) {
      intervalRef.current = setInterval(() => {
        setCurrentFrame((prev) => {
          const next = prev + playbackSpeed; // Avanzar según multiplicador
          if (next >= playbackData.metadata.total_frames) {
            setIsPlaying(false);
            return playbackData.metadata.total_frames - 1;
          }
          return next;
        });
      }, 1000 / baseFps); // Velocidad base constante
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, playbackSpeed, playbackData, baseFps]);

  // Actualizar eventos activos según frame actual
  useEffect(() => {
    if (!playbackData) return;

  const active: PlaybackEvent[] = eventsForDisplay.filter(
      (event) =>
        currentFrame >= event.frame_entry &&
        currentFrame <= event.frame_exit &&
        !event.hide_in_pdf
    );
    setActiveEvents(active);

    // Calcular intervalo actual (15 minutos)
    const timestamp = new Date(Date.now() + (currentFrame / playbackData.metadata.fps) * 1000);
    const intervalStart = new Date(timestamp);
    intervalStart.setMinutes(Math.floor(intervalStart.getMinutes() / 15) * 15, 0, 0);
    // Formato: solo HH:MM (tiempo relativo)
    const intervalKey = intervalStart.toISOString().substring(11, 16); // "HH:MM"
    setSelectedInterval(intervalKey);
  }, [currentFrame, playbackData, eventsForDisplay]);

  async function loadPlaybackData() {
    try {
      setLoading(true);
      // Cache-busting: agregar timestamp para forzar carga de datos más recientes
      const timestamp = new Date().getTime();
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/playback-events?t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });

      if (res.status === 404) {
        setProcessing(true);
        return;
      }

      if (!res.ok) throw new Error('Error cargando playback');

      const data = await res.json();

      // Aplicar regla: Norte es solo entrada (remover salidas de vehículos desde N)
      const filteredEvents = data.events.filter((event: PlaybackEvent) => {
        if (event.origin_cardinal === 'N' && !isPersona(event.class)) {
          return false;
        }
        return true;
      });

      if (filteredEvents.length !== data.events.length) {
        console.warn(
          `Regla aplicada: eliminados ${data.events.length - filteredEvents.length} eventos con origen Norte`
        );
      }

      data.events = filteredEvents;
      data.metadata.total_events = filteredEvents.length;

      // Verificar filtrado de eventos desde Norte
      const fromNorth = data.events.filter((e: any) => e.origin_cardinal === 'N');
      console.log('Playback data loaded:', {
        events: data.events.length,
        metadata: data.metadata,
        firstEvent: data.events[0],
        fromNorth: fromNorth.length,
        fromNorthVehicles: fromNorth.filter((e: any) => !['person', 'pedestrian', 'peaton'].includes(e.class)).length
      });

      setPlaybackData(data);
      setProcessing(false);

      // Cargar correcciones existentes de forma segura
      try {
        const correctionsRes = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/trajectory-corrections?t=${timestamp}`);
        if (correctionsRes.ok) {
          const correctionsData = await correctionsRes.json();
          console.log('✓ Correcciones cargadas:', Object.keys(correctionsData.corrections || {}).length);
          setCorrections(correctionsData.corrections || {});
        } else {
          // Si el endpoint falla (e.g., 404, 500), no es un error crítico.
          // Se asume que no hay correcciones y se continúa.
          console.warn(`No se pudieron cargar las correcciones (status: ${correctionsRes.status}). Se continuará sin ellas.`);
          setCorrections({});
        }
      } catch (error) {
        console.error('Error de red cargando correcciones. Se continuará sin ellas:', error);
        setCorrections({});
      }

      // Seleccionar primer intervalo automáticamente
      if (data.events.length > 0) {
        const intervalCounts = groupEventsByInterval(data.events);
        const firstInterval = Array.from(intervalCounts.keys()).sort()[0];
        if (firstInterval) {
          setSelectedInterval(firstInterval);
          console.log('First interval selected:', firstInterval);
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setProcessing(true);
    } finally {
      setLoading(false);
    }
  }

  async function loadAccesses() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/cardinals`);
      if (!res.ok) return;
      const data = await res.json();

      // Cargar accesos tal cual vienen del backend
      // Las gates están en coordenadas de DATOS (mismo espacio que trayectorias)
      // y serán transformadas al dibujar en canvas
      const accessesWithCoords = (data.accesses || []).map((acc: any) => ({
        ...acc,
        // Mantener x,y solo para compatibilidad legacy
        x: acc.x ?? 0,
        y: acc.y ?? 0,
      }));

      console.log('✓ Accesses cargados:', accessesWithCoords.length);
      console.log('✓ Ejemplo de gate (espacio de datos):', accessesWithCoords[0]?.gate);
      console.log('✓ Polígonos cargados:');
      accessesWithCoords.forEach((acc: any) => {
        if (acc.polygon && acc.polygon.length > 0) {
          console.log(`  - ${acc.cardinal_official} (${acc.display_name}): ${acc.polygon.length} puntos`, acc.polygon);
        }
      });
      setAccesses(accessesWithCoords);
    } catch (error) {
      console.error('Error cargando accesos:', error);
    }
  }

  async function processPlayback() {
    try {
      setProcessing(true);
      const res = await fetch(`${API_BASE_URL}/api/datasets/${datasetId}/process-playback`, {
        method: 'POST',
      });

      if (!res.ok) throw new Error('Error procesando playback');

      await loadPlaybackData();
    } catch (error) {
      console.error('Error:', error);
      alert('Error procesando playback');
    } finally {
      setProcessing(false);
    }
  }

  // Calcular bounds una sola vez (memo)
  const { minX: boundsMinX, maxX: _boundsMaxX, minY: boundsMinY, maxY: _boundsMaxY, scale: boundsScale, offsetX: boundsOffsetX, offsetY: boundsOffsetY } = useMemo(() => {
    if (!playbackData || accesses.length === 0) {
      return { minX: 0, maxX: 1200, minY: 0, maxY: 600, scale: 1, offsetX: 60, offsetY: 60 };
    }

    const padding = 60;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    accesses.forEach((acc) => {
      minX = Math.min(minX, acc.x);
      maxX = Math.max(maxX, acc.x);
      minY = Math.min(minY, acc.y);
      maxY = Math.max(maxY, acc.y);
    });

    playbackData.events.forEach((ev) => {
      ev.positions.forEach(([x, y]) => {
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
      });
    });

    const dataWidth = maxX - minX;
    const dataHeight = maxY - minY;
    const canvasWidth = 1200 - 2 * padding;
    const canvasHeight = 600 - 2 * padding;
    const scale = Math.min(canvasWidth / dataWidth, canvasHeight / dataHeight);

    const offsetX = padding + (canvasWidth - dataWidth * scale) / 2;
    const offsetY = padding + (canvasHeight - dataHeight * scale) / 2;

    return { minX, maxX, minY, maxY, scale, offsetX, offsetY };
  }, [playbackData, accesses]);

  // Manejar click en canvas para seleccionar trayectoria
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    console.log('🖱️ Canvas clicked!', e.clientX, e.clientY);
    const canvas = canvasRef.current;
    if (!canvas || !playbackData) {
      console.log('❌ No canvas or playback data');
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Buscar trayectoria más cercana al click (dentro de un radio)
    const CLICK_RADIUS = 20; // Aumentado para mejor UX
    let closestEvent: PlaybackEvent | null = null;
    let minDistance = CLICK_RADIUS;

    for (const event of playbackData.events) {
      if (!event.positions || event.positions.length === 0) continue;

      // Usar bounds pre-calculados
      for (const [dataX, dataY] of event.positions) {
        const canvasX = boundsOffsetX + (dataX - boundsMinX) * boundsScale;
        const canvasY = boundsOffsetY + (dataY - boundsMinY) * boundsScale;

        const distance = Math.sqrt(
          Math.pow(clickX - canvasX, 2) + Math.pow(clickY - canvasY, 2)
        );

        if (distance < minDistance) {
          minDistance = distance;
          closestEvent = event;
        }
      }
    }

    if (closestEvent) {
      console.log('✅ Found trajectory:', closestEvent.track_id, closestEvent.class);
      setSelectedTrajectory(closestEvent);
      setEditModalOpen(true);
      console.log('📝 Modal opened');
    } else {
      console.log('❌ No trajectory found near click');
    }
  }, [playbackData, boundsMinX, boundsMinY, boundsScale, boundsOffsetX, boundsOffsetY]);

  // Guardar corrección de trayectoria
  const handleSaveCorrection = async (
    trackId: string,
    newOrigin: string,
    newDest: string,
    newClass: string,
    discard: boolean,
    hideInPdf: boolean
  ) => {
    console.log('💾 Guardando corrección:', { trackId, newOrigin, newDest, newClass, discard, hideInPdf });
    try {
      const url = `${API_BASE_URL}/api/datasets/${datasetId}/trajectory-corrections`;
      console.log('📡 URL:', url);

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track_id: trackId,
          new_origin: newOrigin,
          new_dest: newDest,
          new_class: newClass,
          discard,
          hide_in_pdf: hideInPdf,
        }),
      });

      console.log('📥 Response status:', res.status);

      if (!res.ok) {
        const errorText = await res.text();
        console.error('❌ Error response:', errorText);
        throw new Error('Error guardando corrección: ' + errorText);
      }

      const data = await res.json();
      console.log('✅ Corrección guardada:', data);

      // Actualizar correcciones localmente para reflejar cambios inmediatos
      setCorrections(prev => ({
        ...prev,
        [trackId]: {
          new_origin: newOrigin,
          new_dest: newDest,
          new_class: newClass,
          discard,
          hide_in_pdf: hideInPdf,
        }
      }));

      // Recargar datos para reflejar los cambios inmediatamente
      console.log('🔄 Recargando datos de playback...');
      await loadPlaybackData();

      alert(`✅ Corrección guardada y aplicada!\n\nTotal correcciones: ${data.total_corrections}`);
    } catch (error) {
      console.error('❌ Error completo:', error);
      alert('❌ Error guardando corrección: ' + (error instanceof Error ? error.message : String(error)));
    }
  };

  // Dibujar capa de fondo estática (trayectorias + accesos)
  const drawBackgroundLayer = useCallback(() => {
    const bgCanvas = backgroundCanvasRef.current;
    const mainCanvas = canvasRef.current;

    if (!bgCanvas || !mainCanvas || !playbackData || !dataBounds) {
      return;
    }

    // Configurar tamaño del background canvas igual al principal
    bgCanvas.width = mainCanvas.width;
    bgCanvas.height = mainCanvas.height;

    const ctx = bgCanvas.getContext('2d');
    if (!ctx) return;

    // Fondo negro
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);

    // Calcular bounds usando TODOS los eventos
    const padding = 60;
    const { minX, maxX, minY, maxY } = dataBounds;

    const dataWidth = maxX - minX || 1;
    const dataHeight = maxY - minY || 1;
    const scaleX = (bgCanvas.width - padding * 2) / dataWidth;
    const scaleY = (bgCanvas.height - padding * 2) / dataHeight;
    const scale = Math.min(scaleX, scaleY);

    const offsetX = padding + (bgCanvas.width - padding * 2 - dataWidth * scale) / 2;
    const offsetY = padding + (bgCanvas.height - padding * 2 - dataHeight * scale) / 2;

    function transform(x: number, y: number): [number, number] {
      return [
        offsetX + (x - minX) * scale,
        offsetY + (y - minY) * scale,
      ];
    }

    // 1. Dibujar TODAS las trayectorias de fondo (con filtros opcionales)
    eventsForDisplay.forEach((event) => {
      const color = CLASE_COLORS[event.class] || '#95a5a6';
      ctx.strokeStyle = hexToRgba(color, 0.15);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      event.positions.forEach(([px, py], i) => {
        const [x, y] = transform(px, py);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
    });

    // 2. Dibujar accesos cardinales con zonas estéticas
    const cardinalColors: Record<string, string> = {
      'N': '#3b82f6',  // Azul
      'S': '#10b981',  // Verde
      'E': '#f59e0b',  // Naranja
      'O': '#ef4444',  // Rojo
    };

    accesses.forEach((access) => {
      const cardinal = access.cardinal_official || access.cardinal;
      const color = cardinalColors[cardinal] || '#6b7280';
      let centerX = 0;
      let centerY = 0;

      // Dibujar polígono si existe (PRIORIDAD - más estético)
      if (access.polygon && access.polygon.length >= 3) {
        // Zona rellena semitransparente
        ctx.fillStyle = hexToRgba(color, 0.2);
        ctx.beginPath();
        access.polygon.forEach((point, i) => {
          const [x, y] = transform(point.x, point.y);
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });
        ctx.closePath();
        ctx.fill();

        // Borde del polígono con efecto glow
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Calcular centro del polígono
        const sumX = access.polygon.reduce((sum, p) => sum + p.x, 0);
        const sumY = access.polygon.reduce((sum, p) => sum + p.y, 0);
        const avgX = sumX / access.polygon.length;
        const avgY = sumY / access.polygon.length;
        [centerX, centerY] = transform(avgX, avgY);
      }
      // Dibujar gate si NO hay polígono (fallback)
      else if (access.gate) {
        // Transformar coordenadas de gate
        const [x1, y1] = transform(access.gate.x1, access.gate.y1);
        const [x2, y2] = transform(access.gate.x2, access.gate.y2);

        // Línea de la gate
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.shadowBlur = 12;
        ctx.shadowColor = color;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.shadowBlur = 0;

        centerX = (x1 + x2) / 2;
        centerY = (y1 + y2) / 2;
      }

      // Etiqueta pequeña y sutil
      if (centerX !== 0 || centerY !== 0) {
        // Fondo semitransparente
        ctx.fillStyle = hexToRgba(color, 0.9);
        const labelWidth = 50;
        const labelHeight = 24;
        const radius = 6;

        // Rectángulo redondeado
        ctx.beginPath();
        ctx.moveTo(centerX - labelWidth/2 + radius, centerY - labelHeight/2);
        ctx.lineTo(centerX + labelWidth/2 - radius, centerY - labelHeight/2);
        ctx.quadraticCurveTo(centerX + labelWidth/2, centerY - labelHeight/2, centerX + labelWidth/2, centerY - labelHeight/2 + radius);
        ctx.lineTo(centerX + labelWidth/2, centerY + labelHeight/2 - radius);
        ctx.quadraticCurveTo(centerX + labelWidth/2, centerY + labelHeight/2, centerX + labelWidth/2 - radius, centerY + labelHeight/2);
        ctx.lineTo(centerX - labelWidth/2 + radius, centerY + labelHeight/2);
        ctx.quadraticCurveTo(centerX - labelWidth/2, centerY + labelHeight/2, centerX - labelWidth/2, centerY + labelHeight/2 - radius);
        ctx.lineTo(centerX - labelWidth/2, centerY - labelHeight/2 + radius);
        ctx.quadraticCurveTo(centerX - labelWidth/2, centerY - labelHeight/2, centerX - labelWidth/2 + radius, centerY - labelHeight/2);
        ctx.closePath();
        ctx.fill();

        // Texto cardinal
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(cardinal || '?', centerX, centerY);
      }
    });
  }, [playbackData, accesses, dataBounds, eventsForDisplay]);

  // Dibujar canvas con trayectorias activas (capa animada)
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const bgCanvas = backgroundCanvasRef.current;

    if (!canvas || !playbackData || !dataBounds) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Copiar el background estático (optimización de rendimiento)
    if (bgCanvas) {
      ctx.drawImage(bgCanvas, 0, 0);
    } else {
      // Fallback: fondo negro si no hay background canvas
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    if (!showInteractiveOverlay) {
      return;
    }

    // Calcular transformación (debe coincidir con drawBackgroundLayer)
    const padding = 60;
    const { minX, maxX, minY, maxY } = dataBounds;

    const dataWidth = maxX - minX || 1;
    const dataHeight = maxY - minY || 1;
    const scaleX = (canvas.width - padding * 2) / dataWidth;
    const scaleY = (canvas.height - padding * 2) / dataHeight;
    const scale = Math.min(scaleX, scaleY);

    const offsetX = padding + (canvas.width - padding * 2 - dataWidth * scale) / 2;
    const offsetY = padding + (canvas.height - padding * 2 - dataHeight * scale) / 2;

    function transform(x: number, y: number): [number, number] {
      return [
        offsetX + (x - minX) * scale,
        offsetY + (y - minY) * scale,
      ];
    }

    // 3. Dibujar trayectorias activas resaltadas (con filtros opcionales)
    activeEvents.forEach((event) => {
      // Aplicar filtro de clase si está activo
      if (selectedClass && event.class !== selectedClass) {
        return;
      }

      // Aplicar filtro de movimiento RILSA si está activo (comparación estricta)
      if (selectedMovimiento !== null) {
        // Asegurar que ambos son números antes de comparar
        const eventMov = Number(event.mov_rilsa);
        const selectedMov = Number(selectedMovimiento);

        if (eventMov !== selectedMov) {
          return;
        }
      }

      const totalFrames = Math.max(event.frame_exit - event.frame_entry, 1);
      const progress = Math.min(Math.max((currentFrame - event.frame_entry) / totalFrames, 0), 1);
      const positions = event.positions;
      const color = CLASE_COLORS[event.class] || '#95a5a6';

      // Trayectoria completa resaltada
      ctx.strokeStyle = hexToRgba(color, 0.6);
      ctx.lineWidth = 3;
      ctx.beginPath();
      positions.forEach(([px, py], i) => {
        const [x, y] = transform(px, py);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Posición actual
      const currentPosIndex = Math.floor(progress * (positions.length - 1));
      if (currentPosIndex >= 0 && currentPosIndex < positions.length) {
        const [px, py] = positions[currentPosIndex];
        const [x, y] = transform(px, py);

        // Parte recorrida brillante
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.beginPath();
        for (let i = 0; i <= currentPosIndex; i++) {
          const [px, py] = positions[i];
          const [x, y] = transform(px, py);
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Marcador circular del vehículo
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();

        // Etiqueta RILSA discreta
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(formatRilsaCode(event.mov_rilsa), x, y + 16);
      }
    });
  }, [currentFrame, activeEvents, playbackData, selectedClass, selectedMovimiento, dataBounds, showInteractiveOverlay]);

  // Redibujar capas cuando cambien datos o filtros relevantes
  useEffect(() => {
    if (!playbackData || !dataBounds) {
      return;
    }
    drawBackgroundLayer();
    drawCanvas();
  }, [playbackData, dataBounds, drawBackgroundLayer, drawCanvas]);

  useEffect(() => {
    if (dataBounds) { // Solo dibujar si hay bounds
      drawCanvas();
    }
  }, [drawCanvas, eventsForDisplay]);

  if (loading) {
    return (
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '60px', textAlign: 'center' }}>
        <div style={{ fontSize: '64px', marginBottom: '24px' }}>⏳</div>
        <p style={{ color: '#7f8c8d' }}>Cargando reproductor...</p>
      </div>
    );
  }

  if (processing || !playbackData) {
    return (
      <div
        style={{
          maxWidth: '800px',
          margin: '0 auto',
          padding: '60px',
          textAlign: 'center',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ fontSize: '64px', marginBottom: '24px' }}>🎬</div>
        <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '16px' }}>
          Procesar Playback en Vivo
        </h2>
        <p style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '32px' }}>
          El sistema construirá trayectorias desde las detecciones y detectará cruces automáticamente.
        </p>
        <button
          onClick={processPlayback}
          disabled={processing}
          style={{
            padding: '16px 32px',
            background: processing ? '#95a5a6' : '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: '600',
            cursor: processing ? 'not-allowed' : 'pointer',
          }}
        >
          {processing ? '⏳ Procesando...' : '▶️ Procesar Playback'}
        </button>
      </div>
    );
  }

  const fps = playbackData.metadata.fps || baseFps;
  const progress = (currentFrame / playbackData.metadata.total_frames) * 100;
  const currentSeconds = currentFrame / fps;
  const totalSeconds = (playbackData.metadata.total_frames - 1) / fps;
  const formatTimeHM = useCallback((seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }, []);

  const handleTogglePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    setShowInteractiveOverlay(true);
    setIsPlaying(true);
  };

  // Calcular conteos acumulados hasta el frame actual (si se requiere mostrar luego)
  // const accumulatedCounts = getAccumulatedCounts(eventsForDisplay.length > 0 ? eventsForDisplay : playbackData.events, currentFrame);

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto' }}>
      {/* Controles de reproducción */}
      <div
        style={{
          background: 'white',
          borderRadius: '12px',
          padding: '32px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>📹</div>
            <h2 style={{ fontSize: '24px', color: '#2c3e50', marginBottom: '8px' }}>
              Aforo en Vivo - Reproducción
            </h2>
            <p style={{ fontSize: '14px', color: '#7f8c8d' }}>
              {playbackData.metadata.total_events} trayectorias detectadas
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '4px' }}>Intervalo Actual</div>
            <div style={{ fontSize: '16px', color: '#2c3e50', fontWeight: '600' }}>{selectedInterval}</div>
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
            <button
              onClick={handleTogglePlay}
              style={{
                padding: '12px 24px',
                background: isPlaying ? '#e74c3c' : '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              {isPlaying ? '⏸️ Pausar' : '▶️ Reproducir'}
            </button>

            <button
              onClick={() => setCurrentFrame(0)}
              disabled={isPlaying}
              style={{
                padding: '12px 24px',
                background: isPlaying ? '#95a5a6' : '#34495e',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: isPlaying ? 'not-allowed' : 'pointer',
              }}
            >
              ⏮️ Reiniciar
            </button>

            <button
              onClick={() => {
                setShowDirectAforo(true);
                setCurrentFrame(playbackData.metadata.total_frames - 1);
                setIsPlaying(false);
              }}
              disabled={isPlaying}
              style={{
                padding: '12px 24px',
                background: isPlaying ? '#95a5a6' : '#9b59b6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: isPlaying ? 'not-allowed' : 'pointer',
              }}
            >
              ⚡ Generar Aforo Directo
            </button>

            <div style={{ marginLeft: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '14px', color: '#7f8c8d' }}>Velocidad:</span>
              {[1, 2, 5, 10, 100, 300].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  style={{
                    padding: '8px 16px',
                    background: playbackSpeed === speed ? '#3498db' : '#ecf0f1',
                    color: playbackSpeed === speed ? 'white' : '#2c3e50',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  {speed}x
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowInteractiveOverlay((prev) => !prev)}
              style={{
                padding: '12px 24px',
                background: showInteractiveOverlay ? '#8e44ad' : '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              {showInteractiveOverlay ? '🎯 Ocultar gráfico interactivo' : '🎯 Activar gráfico interactivo'}
            </button>
          </div>

          {/* Slider de tiempo */}
          <div style={{ marginBottom: '12px' }}>
            <input
              type="range"
              min="0"
              max={playbackData.metadata.total_frames - 1}
              value={currentFrame}
              onChange={(e) => setCurrentFrame(parseInt(e.target.value))}
              style={{
                width: '100%',
                height: '8px',
                borderRadius: '4px',
                outline: 'none',
                background: `linear-gradient(to right, #3498db 0%, #3498db ${progress}%, #ecf0f1 ${progress}%, #ecf0f1 100%)`,
                cursor: 'pointer',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#7f8c8d', marginBottom: '8px' }}>
            <span>Frame {currentFrame.toLocaleString()} / {playbackData.metadata.total_frames.toLocaleString()}</span>
            <span>{progress.toFixed(1)}% - {formatTimeHM(currentSeconds)} / {formatTimeHM(totalSeconds)}</span>
          </div>
        </div>
      </div>

      {/* Info de depuración */}
      <div style={{ background: '#f0f9ff', border: '2px solid #3b82f6', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ fontSize: '12px', color: '#1e40af', fontWeight: '600', marginBottom: '8px' }}>🔍 Debug Info:</div>
        <div style={{ fontSize: '11px', color: '#1e3a8a', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
          <div>✓ Playback Data: {playbackData ? 'Loaded' : 'Missing'}</div>
          <div>✓ Events: {playbackData?.events.length || 0}</div>
          <div>✓ Accesses: {accesses.length}</div>
          <div>✓ Current Frame: {currentFrame}</div>
          <div>✓ Active Events: {activeEvents.length}</div>
          <div>✓ Selected Interval: {selectedInterval || 'None'}</div>
        </div>
      </div>

      {/* Canvas de visualización */}
      <div
        style={{
          background: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '24px',
        }}
      >
        <h3 style={{ fontSize: '18px', color: '#2c3e50', marginBottom: '16px', fontWeight: '600' }}>
          🎬 Visualización en Vivo
        </h3>
        <div
          style={{
            background: '#000000',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
          }}
        >
          {/* Background canvas (hidden, used as buffer) */}
          <canvas
            ref={backgroundCanvasRef}
            width={1200}
            height={600}
            style={{ display: 'none' }}
          />
          {/* Main canvas (visible) */}
          <canvas
            ref={canvasRef}
            width={1200}
            height={600}
            onClick={handleCanvasClick}
            style={{
              maxWidth: '100%',
              height: 'auto',
              borderRadius: '4px',
              border: '2px solid #2c3e50',
              cursor: 'pointer',
            }}
          />
        </div>
        <div style={{ marginTop: '12px', fontSize: '13px', color: '#6b7280', textAlign: 'center' }}>
          {showInteractiveOverlay
            ? '🎬 Trayectorias en crudo + resaltado interactivo activo (colores/emojis).'
            : '👁️ Visualización cruda: todas las trayectorias en gris (activa el gráfico interactivo para resaltar).'}
        </div>

        {/* Leyenda de colores - Filtros clickeables */}
        <div style={{ marginTop: '20px' }}>
          <p style={{ fontSize: '13px', color: '#6b7280', textAlign: 'center', marginBottom: '12px' }}>
            👆 Click en un tipo de vehículo para filtrar trayectorias
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
            {Object.entries(CLASE_COLORS).map(([clase, color]) => {
              const isSelected = selectedClass === clase;
              return (
                <button
                  key={clase}
                  onClick={() => {
                    const nextValue = isSelected ? null : clase;
                    setSelectedClass(nextValue);
                    if (nextValue !== null) {
                      setShowInteractiveOverlay(true);
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    background: isSelected ? color : '#f8f9fa',
                    borderRadius: '8px',
                    border: `3px solid ${color}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    transform: isSelected ? 'scale(1.1)' : 'scale(1)',
                    boxShadow: isSelected ? `0 4px 12px ${color}` : 'none',
                  }}
                >
                  <div
                    style={{
                      width: '20px',
                      height: '20px',
                      background: isSelected ? 'white' : color,
                      borderRadius: '4px',
                      boxShadow: `0 0 8px ${color}`,
                    }}
                  />
                  <span style={{ fontSize: '24px' }}>{CLASE_EMOJIS[clase]}</span>
                  <span style={{
                    fontSize: '13px',
                    color: isSelected ? 'white' : '#2c3e50',
                    fontWeight: '600'
                  }}>
                    {CLASE_LABELS[clase]}
                  </span>
                  {isSelected && <span style={{ fontSize: '16px', color: 'white' }}>✓</span>}
                </button>
              );
            })}

            {/* Separador visual */}
            <div style={{
              width: '2px',
              height: '40px',
              background: '#d1d5db',
              margin: '0 8px'
            }} />

            {/* Dropdown de Movimientos RILSA */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              background: '#f8f9fa',
              borderRadius: '8px',
              border: '3px solid #667eea',
            }}>
              <span style={{ fontSize: '14px', color: '#2c3e50', fontWeight: '600' }}>
                🔀 Movimiento:
              </span>
              <select
                value={selectedMovimiento === null ? '' : selectedMovimiento}
                onChange={(e) => {
                  const value = e.target.value === '' ? null : Number(e.target.value);
                  setSelectedMovimiento(value);
                  if (value !== null) {
                    setShowInteractiveOverlay(true);
                  }
                }}
                style={{
                  padding: '6px 12px',
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#2c3e50',
                  background: 'white',
                  border: '2px solid #667eea',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="">Todos los movimientos</option>
                {movimientosUnicos.map((mov) => (
                  <option key={mov} value={mov}>
                    {formatRilsaCode(mov)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Sección de Aforo por Movimientos RILSA */}
      {playbackData && playbackData.events.length > 0 && (() => {
        const datosAforo = procesarEventosHastaFrame(
          playbackData.events,
          currentFrame,
          {
            ubicacion: `Dataset: ${datasetId}`,
            fecha: new Date().toLocaleDateString('es-CO', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            }),
          }
        );

        return (
          <div style={{ marginTop: '32px' }}>
            <h2
              style={{
                fontSize: '24px',
                fontWeight: '700',
                color: '#2c3e50',
                marginBottom: '8px',
                textAlign: 'center',
              }}
            >
              📊 Aforo por Movimientos RILSA
            </h2>
            <p
              style={{
                fontSize: '14px',
                color: '#7f8c8d',
                marginBottom: '24px',
                textAlign: 'center',
              }}
            >
              Datos acumulados hasta el frame actual ({currentFrame.toLocaleString()}) • Se actualiza en tiempo real
            </p>
            {/* 
            <AforoMovimientosTabs
              datos={datosAforo}
              playbackEvents={playbackData.events}
              cardinals={cardinalsForTabs}
            />
            */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                padding: '24px',
                marginBottom: '24px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                textAlign: 'center',
              }}
            >
              <h3 style={{ color: '#e67e22', marginBottom: '16px' }}>
                🚧 Componente en Desarrollo
              </h3>
              <p style={{ color: '#7f8c8d', fontSize: '14px' }}>
                La tabla de aforos por movimientos RILSA está siendo desarrollada.
                <br />
                Los datos se están procesando correctamente en tiempo real.
              </p>
            </div>
          </div>
        );
      })()}

      {/* Modal de edición de trayectorias */}
      <TrajectoryEditModal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        trajectory={selectedTrajectory}
        onSave={handleSaveCorrection}
        availableCardinals={Array.from(new Set(accesses.map(a => a.cardinal_official || 'N')))}
        existingCorrection={selectedTrajectory ? corrections[selectedTrajectory.track_id] : null}
      />
    </div>
  );
}
