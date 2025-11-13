/**
 * Utilidad de debug para visualizar zonas de acceso cardinal
 * Muestra todas las trayectorias y los gates cardinales
 */

interface PlaybackEvent {
  track_id: string;
  class: string;
  origin_cardinal: string;
  dest_cardinal: string;
  mov_rilsa: number;
  positions: [number, number][];
}

interface CardinalAccess {
  id: string;
  display_name: string;
  cardinal_official: string;
  gate: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
}

export function createCardinalZonesDebugCanvas(
  eventos: PlaybackEvent[],
  cardinals: CardinalAccess[]
): string {
  const canvas = document.createElement('canvas');
  canvas.width = 1400;
  canvas.height = 800;
  const ctx = canvas.getContext('2d')!;

  // Fondo blanco
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Título
  ctx.fillStyle = '#000000';
  ctx.font = 'bold 24px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('Debug: Zonas de Acceso Cardinal', canvas.width / 2, 30);

  // Calcular bounds de todas las trayectorias
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

  eventos.forEach(event => {
    event.positions.forEach(([x, y]) => {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    });
  });

  // Agregar padding
  const padding = 80;
  const dataWidth = maxX - minX || 1;
  const dataHeight = maxY - minY || 1;

  const availableWidth = canvas.width - padding * 2;
  const availableHeight = canvas.height - padding * 2 - 60; // Espacio para título y leyenda

  const scaleX = availableWidth / dataWidth;
  const scaleY = availableHeight / dataHeight;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = padding + (availableWidth - dataWidth * scale) / 2;
  const offsetY = padding + 50 + (availableHeight - dataHeight * scale) / 2;

  function transform(x: number, y: number): [number, number] {
    return [
      offsetX + (x - minX) * scale,
      offsetY + (y - minY) * scale,
    ];
  }

  // Dibujar TODAS las trayectorias en gris muy claro
  ctx.strokeStyle = '#e0e0e0';
  ctx.lineWidth = 1;
  eventos.forEach(event => {
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

  // Colores para cada cardinal
  const cardinalColors: Record<string, string> = {
    'N': '#3b82f6',  // Azul
    'S': '#ef4444',  // Rojo
    'E': '#10b981',  // Verde
    'O': '#f59e0b',  // Naranja
  };

  // Dibujar gates/accesos cardinales con grosor y transparencia
  cardinals.forEach(access => {
    const color = cardinalColors[access.cardinal_official] || '#9ca3af';
    const [x1, y1] = transform(access.gate.x1, access.gate.y1);
    const [x2, y2] = transform(access.gate.x2, access.gate.y2);

    // Línea gruesa del gate
    ctx.strokeStyle = color;
    ctx.lineWidth = 8;
    ctx.globalAlpha = 0.8;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.globalAlpha = 1.0;

    // Etiqueta del gate
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;

    ctx.fillStyle = color;
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Fondo blanco para el texto
    const label = `${access.cardinal_official} (${access.display_name})`;
    const metrics = ctx.measureText(label);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillRect(midX - metrics.width / 2 - 4, midY - 10, metrics.width + 8, 20);

    ctx.fillStyle = color;
    ctx.fillText(label, midX, midY);
  });

  // Dibujar puntos de inicio (verde) y fin (rojo) de cada trayectoria
  eventos.forEach(event => {
    if (event.positions.length === 0) return;

    // Punto de inicio (verde)
    const [startX, startY] = transform(event.positions[0][0], event.positions[0][1]);
    ctx.fillStyle = '#00ff00';
    ctx.beginPath();
    ctx.arc(startX, startY, 3, 0, 2 * Math.PI);
    ctx.fill();

    // Punto de fin (rojo)
    const lastIdx = event.positions.length - 1;
    const [endX, endY] = transform(event.positions[lastIdx][0], event.positions[lastIdx][1]);
    ctx.fillStyle = '#ff0000';
    ctx.beginPath();
    ctx.arc(endX, endY, 3, 0, 2 * Math.PI);
    ctx.fill();
  });

  // Dibujar leyenda
  const legendY = canvas.height - 50;
  let legendX = 50;

  ctx.font = 'bold 14px Arial';
  ctx.fillStyle = '#000000';
  ctx.textAlign = 'left';

  // Leyenda de gates
  Object.entries(cardinalColors).forEach(([cardinal, color]) => {
    ctx.fillStyle = color;
    ctx.fillRect(legendX, legendY - 8, 30, 16);
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY - 8, 30, 16);

    ctx.fillStyle = '#000000';
    ctx.font = '12px Arial';
    ctx.fillText(`${cardinal}`, legendX + 40, legendY);

    legendX += 80;
  });

  // Separador
  legendX += 20;

  // Leyenda de puntos
  ctx.fillStyle = '#00ff00';
  ctx.beginPath();
  ctx.arc(legendX, legendY, 5, 0, 2 * Math.PI);
  ctx.fill();
  ctx.fillStyle = '#000000';
  ctx.font = '12px Arial';
  ctx.fillText('Inicio', legendX + 10, legendY);

  legendX += 70;

  ctx.fillStyle = '#ff0000';
  ctx.beginPath();
  ctx.arc(legendX, legendY, 5, 0, 2 * Math.PI);
  ctx.fill();
  ctx.fillStyle = '#000000';
  ctx.fillText('Fin', legendX + 10, legendY);

  // Info de totales
  ctx.font = '12px Arial';
  ctx.fillStyle = '#666666';
  ctx.textAlign = 'right';
  ctx.fillText(`Total trayectorias: ${eventos.length}`, canvas.width - 50, legendY);

  return canvas.toDataURL('image/png');
}

/**
 * Crear mapa de calor por movimiento RILSA
 */
export function createMovementHeatmap(
  eventos: PlaybackEvent[],
  movimiento: number
): string {
  const canvas = document.createElement('canvas');
  canvas.width = 1400;
  canvas.height = 800;
  const ctx = canvas.getContext('2d')!;

  // Fondo negro
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const eventosFiltrados = eventos.filter(e => e.mov_rilsa === movimiento);

  if (eventosFiltrados.length === 0) {
    ctx.fillStyle = '#ffffff';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`No hay trayectorias para movimiento ${movimiento}`, canvas.width / 2, canvas.height / 2);
    return canvas.toDataURL('image/png');
  }

  // Título
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px Arial';
  ctx.textAlign = 'center';

  const primeraTrajectoria = eventosFiltrados[0];
  const titulo = `Movimiento ${movimiento}: ${primeraTrajectoria.origin_cardinal} → ${primeraTrajectoria.dest_cardinal}`;
  ctx.fillText(titulo, canvas.width / 2, 30);

  // Calcular bounds
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

  eventosFiltrados.forEach(event => {
    event.positions.forEach(([x, y]) => {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    });
  });

  const padding = 80;
  const dataWidth = maxX - minX || 1;
  const dataHeight = maxY - minY || 1;

  const availableWidth = canvas.width - padding * 2;
  const availableHeight = canvas.height - padding * 2 - 60;

  const scaleX = availableWidth / dataWidth;
  const scaleY = availableHeight / dataHeight;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = padding + (availableWidth - dataWidth * scale) / 2;
  const offsetY = padding + 50 + (availableHeight - dataHeight * scale) / 2;

  function transform(x: number, y: number): [number, number] {
    return [
      offsetX + (x - minX) * scale,
      offsetY + (y - minY) * scale,
    ];
  }

  // Dibujar trayectorias con colores por clase
  const CLASE_COLORS: Record<string, string> = {
    car: '#3b82f6',
    motorcycle: '#e74c3c',
    bus: '#f39c12',
    truck: '#9b59b6',
    bicycle: '#2ecc71',
    person: '#1abc9c',
  };

  eventosFiltrados.forEach(event => {
    const color = CLASE_COLORS[event.class] || '#95a5a6';

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowBlur = 4;
    ctx.shadowColor = color;
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
    ctx.shadowBlur = 0;

    // Puntos de inicio y fin
    const [startX, startY] = transform(event.positions[0][0], event.positions[0][1]);
    ctx.fillStyle = '#00ff00';
    ctx.beginPath();
    ctx.arc(startX, startY, 4, 0, 2 * Math.PI);
    ctx.fill();

    const lastIdx = event.positions.length - 1;
    const [endX, endY] = transform(event.positions[lastIdx][0], event.positions[lastIdx][1]);
    ctx.fillStyle = '#ff0000';
    ctx.beginPath();
    ctx.arc(endX, endY, 4, 0, 2 * Math.PI);
    ctx.fill();
  });

  // Info
  ctx.font = '14px Arial';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.fillText(`Total: ${eventosFiltrados.length} trayectorias`, 50, canvas.height - 30);

  return canvas.toDataURL('image/png');
}
