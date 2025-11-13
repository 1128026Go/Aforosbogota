# Sistema de Aforo en Vivo

Sistema de conteo en tiempo real de trayectorias vehiculares y peatonales con agregación automática en bloques de 15 minutos.

## 📋 Características

- **Conteo por trayectoria**: Cada track_id cuenta UNA vez (idempotencia)
- **Agregación 15 min**: Buckets automáticos en :00, :15, :30, :45
- **Clasificación RILSA**: Movimientos 1-10 según origen→destino
- **Panel en vivo**: Tabla interactiva con conteos por movimiento y clase
- **Exportación CSV**: Descarga del bucket activo
- **Persistencia**: LocalStorage automático

## 🏗️ Arquitectura

```
src/
├── types/
│   └── aforo.ts           # Tipos TypeScript
├── lib/
│   ├── aforoBus.ts        # Event bus pub/sub
│   ├── rilsa.ts           # Mapeo movimientos RILSA
│   ├── aforoIntegration.ts # Integración store ↔ bus
│   └── trajectoryEmitter.example.ts # Ejemplos de uso
├── store/
│   └── aforoLive.ts       # Zustand store con persistencia
└── components/
    └── AforoLivePanel.tsx # Panel UI
```

## 🚀 Uso

### 1. Inicializar en la aplicación

En `main.tsx` o punto de entrada:

```typescript
import { initAforoIntegration } from './lib/aforoIntegration';
import AforoLivePanel from './components/AforoLivePanel';

// Inicializar integración
initAforoIntegration();

// Renderizar panel
function App() {
  return (
    <>
      {/* Tu mapa/visualización */}
      <AforoLivePanel />
    </>
  );
}
```

### 2. Emitir eventos de trayectorias

Donde detectes que una trayectoria termina:

```typescript
import { aforoBus } from './lib/aforoBus';
import { mapRilsa } from './lib/rilsa';

function onTrajectoryCompleted(track) {
  aforoBus.publish({
    track_id: track.id,
    clase: track.vehicleType, // 'car', 'truck', 'bus', etc.
    t_exit_iso: new Date().toISOString(),
    origin_cardinal: track.origin, // 'N', 'S', 'E', 'O'
    dest_cardinal: track.dest,
    mov_rilsa: mapRilsa(track.origin, track.dest),
    ramal: track.origin,
    v_kmh_mediana: track.medianSpeed,
  });
}
```

### 3. Ver resultados en vivo

El panel `AforoLivePanel` se actualiza automáticamente mostrando:

- **Tabla de conteos**: Filas = movimientos RILSA (1-10), Columnas = clases vehiculares
- **Totales**: Por movimiento, por clase, y total general
- **Meta información**: Intervalo actual, periodo (mañana/tarde), ramal
- **Selector de bucket**: Navegar entre bloques de 15 min anteriores

## 📊 Estructura de datos

### Evento de trayectoria completada

```typescript
interface TrajectoryCompletedEvent {
  track_id: string;              // ID único
  clase: ClaseMovil;             // 'car'|'truck'|'bus'|'motorcycle'|'bicycle'|'person'
  t_exit_iso: string;            // ISO 8601 timestamp
  origin_cardinal: Cardinal;     // 'N'|'S'|'E'|'O'
  dest_cardinal: Cardinal;       // 'N'|'S'|'E'|'O'
  mov_rilsa: number;             // 1-10
  ramal: Cardinal;               // origin_cardinal
  v_kmh_mediana?: number;        // Opcional
}
```

### Mapeo RILSA

| Origen→Destino | Movimiento | Tipo |
|---------------|-----------|------|
| N→E, E→S, S→O, O→N | 1-3 | Giro derecha |
| N→S, E→O, S→N, O→E | 4-6 | De frente |
| N→O, E→N, S→E, O→S | 7-9 | Giro izquierda |
| X→X | 10 | Retorno |

## 🔧 API del Store

```typescript
import { useAforoLive } from './store/aforoLive';

// En componente React
function MyComponent() {
  const total = useAforoLive(s => s.getCurrentBucketData()?.total);
  const reset = useAforoLive(s => s.reset);
  const exportCSV = useAforoLive(s => s.exportBucketToCSV);

  // ...
}

// Fuera de React
const { upsert, reset } = useAforoLive.getState();
upsert(event);
```

## 📤 Exportación CSV

Formato del archivo exportado:

```csv
timestamp_inicio,periodo,ramal,movimiento_rilsa,clase,conteo
2025-11-07T14:00:00.000Z,mañana,N,4,car,125
2025-11-07T14:00:00.000Z,mañana,N,4,motorcycle,89
...
```

## ✅ Validaciones

- **Idempotencia**: Mismo track_id no se cuenta dos veces
- **Cuadres**: Total por clase + Total por movimiento = Total general
- **Timestamp correcto**: Bucket de 15 min calculado desde t_exit
- **Persistencia**: Datos guardados en localStorage sobreviven recargas

## 🎨 Personalización

### Cambiar colores del panel

Edita el `<style>` en `AforoLivePanel.tsx`:

```css
.aforo-panel {
  background: white; /* Fondo del panel */
}

.cell-active {
  background: #f0fdf4; /* Celdas con conteo */
  color: #166534;
}
```

### Ajustar mapeo RILSA

Edita `lib/rilsa.ts`:

```typescript
const RILSA_MAP: Record<string, number> = {
  'N->E': 1,  // Modificar según tu convención
  // ...
};
```

## 🐛 Debugging

```typescript
// Ver estado actual
console.log(useAforoLive.getState());

// Ver suscriptores activos
console.log(aforoBus.subscriberCount);

// Probar evento manual
aforoBus.publish({
  track_id: 'test-123',
  clase: 'car',
  t_exit_iso: new Date().toISOString(),
  origin_cardinal: 'N',
  dest_cardinal: 'S',
  mov_rilsa: 4,
  ramal: 'N',
});
```

## 📦 Dependencias

```json
{
  "zustand": "^4.4.0",
  "react": "^18.2.0"
}
```

## 🚦 Flujo completo

1. Usuario completa trayectoria en el mapa
2. Motor de trayectorias detecta salida
3. Se emite evento via `aforoBus.publish()`
4. Store Zustand recibe evento y actualiza conteos
5. Panel React se re-renderiza automáticamente
6. Usuario ve incremento en tabla en tiempo real
7. Usuario exporta CSV del bucket actual

## 📝 Notas

- El panel es **flotante** (position: fixed) sobre el mapa
- Los conteos se **persisten** en localStorage
- El sistema es **agnóstico** del motor de trayectorias
- **No** se cuenta por frame, solo por trayectoria completa
- El timestamp de conteo es `t_exit`, no `t_start`
