# 📚 Casos de Uso y Ejemplos

## 🎯 Caso 1: Integración con WebWorker

Si el procesamiento de trayectorias está en un Web Worker:

```typescript
// En el Worker (trajectory.worker.ts)
self.addEventListener('message', (e) => {
  if (e.data.type === 'TRACK_EXIT') {
    const track = e.data.payload;

    // Enviar al thread principal
    self.postMessage({
      type: 'AFORO_EVENT',
      event: {
        track_id: track.id,
        clase: track.vehicleType,
        t_exit_iso: new Date(track.exitTimestamp).toISOString(),
        origin_cardinal: track.origin,
        dest_cardinal: track.dest,
        mov_rilsa: calculateRilsa(track.origin, track.dest),
        ramal: track.origin,
        v_kmh_mediana: track.medianSpeed,
      },
    });
  }
});

// En el thread principal (main.tsx)
worker.onmessage = (e) => {
  if (e.data.type === 'AFORO_EVENT') {
    aforoBus.publish(e.data.event);
  }
};
```

---

## 🎯 Caso 2: Múltiples Ramales Simultáneos

Para intersecciones con 4 ramales activos:

```typescript
// El sistema ya soporta múltiples ramales automáticamente
// Cada evento especifica su ramal:

aforoBus.publish({
  track_id: 'track-norte-123',
  ramal: 'N',  // ← Ramal Norte
  // ...
});

aforoBus.publish({
  track_id: 'track-sur-456',
  ramal: 'S',  // ← Ramal Sur
  // ...
});

// El panel agregará por separado
```

Para ver todos los ramales a la vez, modifica `AforoLivePanel.tsx`:

```typescript
// Mostrar múltiples buckets (uno por ramal)
const allRamales = ['N', 'S', 'E', 'O'];
return (
  <>
    {allRamales.map(ramal => (
      <AforoLivePanel key={ramal} ramal={ramal} />
    ))}
  </>
);
```

---

## 🎯 Caso 3: Exportación Automática cada 15 min

```typescript
import { useAforoLive } from '@/store/aforoLive';

function AutoExport() {
  React.useEffect(() => {
    const interval = setInterval(() => {
      const { getCurrentBucketData, exportBucketToCSV } = useAforoLive.getState();
      const bucket = getCurrentBucketData();

      if (bucket) {
        const csv = exportBucketToCSV(bucket.key.bucket_iso);

        // Enviar a servidor
        fetch('/api/aforo/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'text/csv' },
          body: csv,
        });

        console.log(`📤 Bucket ${bucket.key.bucket_iso} exportado`);
      }
    }, 15 * 60 * 1000); // Cada 15 minutos

    return () => clearInterval(interval);
  }, []);

  return null;
}
```

---

## 🎯 Caso 4: Alertas de Congestión en Tiempo Real

```typescript
function CongestionAlert() {
  const bucketData = useAforoLive(s => s.getCurrentBucketData());
  const [showAlert, setShowAlert] = React.useState(false);

  React.useEffect(() => {
    if (bucketData && bucketData.total > 100) {
      setShowAlert(true);
      // Enviar notificación
      new Notification('⚠️ Congestión Detectada', {
        body: `${bucketData.total} vehículos en 15 min`,
      });
    }
  }, [bucketData]);

  if (!showAlert) return null;

  return (
    <div className="congestion-alert">
      🚨 Alta demanda: {bucketData?.total} trayectorias en el último bloque
    </div>
  );
}
```

---

## 🎯 Caso 5: Gráfico de Serie Temporal

```typescript
import { useAforoLive } from '@/store/aforoLive';

function TimeSeriesChart() {
  const allBuckets = useAforoLive(s => s.getAllBuckets());
  const totales = useAforoLive(s => s.totalesRamal);

  const data = allBuckets.map(bucket => {
    const key = JSON.parse(bucket);
    return {
      time: new Date(key.bucket_iso),
      count: totales.get(bucket) || 0,
    };
  });

  // Renderizar con Chart.js, Recharts, etc.
  return <LineChart data={data} />;
}
```

---

## 🎯 Caso 6: Filtrar Clases Específicas

```typescript
// Ver solo vehículos motorizados (sin peatones/bicis)
function VehicleOnlyPanel() {
  const bucketData = useAforoLive(s => s.getCurrentBucketData());

  const filtered = useMemo(() => {
    if (!bucketData) return null;

    const vehicleCounts: Record<string, number> = {};

    Object.entries(bucketData.counts).forEach(([key, count]) => {
      const parsed: CountKey = JSON.parse(key);

      if (['car', 'truck', 'bus', 'motorcycle'].includes(parsed.clase)) {
        vehicleCounts[key] = count;
      }
    });

    return { ...bucketData, counts: vehicleCounts };
  }, [bucketData]);

  // Renderizar tabla filtrada
}
```

---

## 🎯 Caso 7: Comparación Mañana vs Tarde

```typescript
function PeriodComparison() {
  const allBuckets = useAforoLive(s => s.getAllBuckets());
  const totales = useAforoLive(s => s.totalesRamal);

  const stats = allBuckets.reduce(
    (acc, bucket) => {
      const key = JSON.parse(bucket);
      const count = totales.get(bucket) || 0;

      if (key.periodo === 'mañana') {
        acc.mañana += count;
      } else {
        acc.tarde += count;
      }

      return acc;
    },
    { mañana: 0, tarde: 0 }
  );

  return (
    <div>
      <h3>Comparación de Periodos</h3>
      <p>🌅 Mañana: {stats.mañana} trayectorias</p>
      <p>🌆 Tarde: {stats.tarde} trayectorias</p>
      <p>📊 Diferencia: {Math.abs(stats.mañana - stats.tarde)}</p>
    </div>
  );
}
```

---

## 🎯 Caso 8: Persistencia en Backend

```typescript
// Hook para sincronizar con servidor
function useBackendSync() {
  const counts = useAforoLive(s => s.counts);

  React.useEffect(() => {
    const sync = async () => {
      const data = Array.from(counts.entries()).map(([bucket, counts]) => ({
        bucket: JSON.parse(bucket),
        counts,
      }));

      await fetch('/api/aforo/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    };

    // Sincronizar cada minuto
    const interval = setInterval(sync, 60 * 1000);
    return () => clearInterval(interval);
  }, [counts]);
}
```

---

## 🎯 Caso 9: Validación de Conteos

```typescript
function ValidationPanel() {
  const bucketData = useAforoLive(s => s.getCurrentBucketData());
  const seenTracks = useAforoLive(s => s.seenTracks);

  // Validar que no hay conteos duplicados
  const validation = useMemo(() => {
    if (!bucketData) return { valid: true };

    const totalCounted = Object.values(bucketData.counts).reduce((a, b) => a + b, 0);
    const expectedTotal = bucketData.total;

    return {
      valid: totalCounted === expectedTotal,
      totalCounted,
      expectedTotal,
      uniqueTracks: seenTracks.size,
    };
  }, [bucketData, seenTracks]);

  return (
    <div>
      <h4>Validación de Conteos</h4>
      <p>Estado: {validation.valid ? '✅ Válido' : '❌ Error'}</p>
      <p>Contados: {validation.totalCounted}</p>
      <p>Esperados: {validation.expectedTotal}</p>
      <p>Tracks únicos: {validation.uniqueTracks}</p>
    </div>
  );
}
```

---

## 🎯 Caso 10: Modo Histórico

```typescript
function HistoricalMode() {
  const allBuckets = useAforoLive(s => s.getAllBuckets());
  const setCurrentBucket = useAforoLive(s => s.setCurrentBucket);
  const [playing, setPlaying] = React.useState(false);
  const [index, setIndex] = React.useState(0);

  React.useEffect(() => {
    if (!playing) return;

    const interval = setInterval(() => {
      setIndex((i) => {
        const next = (i + 1) % allBuckets.length;
        setCurrentBucket(allBuckets[next]);
        return next;
      });
    }, 2000); // Cambiar bucket cada 2 segundos

    return () => clearInterval(interval);
  }, [playing, allBuckets]);

  return (
    <div>
      <button onClick={() => setPlaying(!playing)}>
        {playing ? '⏸️ Pausar' : '▶️ Reproducir'}
      </button>
      <p>Bucket {index + 1} / {allBuckets.length}</p>
    </div>
  );
}
```

---

## 📊 Fórmulas Útiles

### Vehículos Equivalentes
```typescript
const FACTORES = {
  car: 1.0,
  motorcycle: 0.5,
  bus: 2.0,
  truck: 2.0,
  bicycle: 0.3,
  person: 0.0,
};

function calcularVehiculosEquivalentes(counts: Record<string, number>) {
  return Object.entries(counts).reduce((total, [key, count]) => {
    const { clase } = JSON.parse(key);
    return total + count * FACTORES[clase];
  }, 0);
}
```

### Nivel de Servicio (LOS)
```typescript
function getNivelServicio(vehPorHora: number) {
  if (vehPorHora < 600) return 'A';
  if (vehPorHora < 1000) return 'B';
  if (vehPorHora < 1400) return 'C';
  if (vehPorHora < 1800) return 'D';
  if (vehPorHora < 2200) return 'E';
  return 'F';
}
```

---

**✨ Estos ejemplos cubren los casos de uso más comunes. Combínalos según tus necesidades.**
