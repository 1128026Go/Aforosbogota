# 🚀 Guía de Integración Rápida

## Objetivo

Conectar el motor de trayectorias existente con el sistema de aforo en vivo para que cada trayectoria completada incremente el conteo automáticamente.

---

## ⚡ 3 Pasos para Integrar

### 1️⃣ Instalar dependencias

```bash
cd apps/web
npm install
```

### 2️⃣ Iniciar desarrollo

```bash
npm run dev
```

Abre http://localhost:3000 y verás el panel de aforo con un botón de prueba.

### 3️⃣ Conectar con tu motor de trayectorias

En el código donde detectas que una trayectoria sale del área, agrega:

```typescript
import { aforoBus } from '@/lib/aforoBus';
import { mapRilsa } from '@/lib/rilsa';

// Cuando el emoji termina su recorrido:
function onEmojiFinished(trackData) {
  aforoBus.publish({
    track_id: trackData.id,
    clase: trackData.type,        // 'car', 'truck', 'bus', etc.
    t_exit_iso: new Date().toISOString(),
    origin_cardinal: trackData.from,  // 'N', 'S', 'E', 'O'
    dest_cardinal: trackData.to,
    mov_rilsa: mapRilsa(trackData.from, trackData.to),
    ramal: trackData.from,
    v_kmh_mediana: trackData.avgSpeed,
  });
}
```

**¡Listo!** El panel se actualiza automáticamente.

---

## 🔍 Ejemplo Completo

```typescript
// En tu motor de trayectorias:

class TrajectoryManager {
  onTrackExit(track) {
    // Calcular velocidad mediana
    const speeds = track.frames.map(f => f.speed);
    const sorted = speeds.sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];

    // Emitir evento
    aforoBus.publish({
      track_id: track.id,
      clase: this.mapYoloToClase(track.yoloClass),
      t_exit_iso: new Date(track.exitTime).toISOString(),
      origin_cardinal: track.entryZone,  // Ya asignado por JSON
      dest_cardinal: track.exitZone,
      mov_rilsa: mapRilsa(track.entryZone, track.exitZone),
      ramal: track.entryZone,
      v_kmh_mediana: median,
    });
  }

  mapYoloToClase(yoloClass) {
    const map = {
      'car': 'car',
      'truck': 'truck',
      'bus': 'bus',
      'motorcycle': 'motorcycle',
      'bicycle': 'bicycle',
      'person': 'person',
    };
    return map[yoloClass] || 'car';
  }
}
```

---

## 📊 Ver Resultados

1. **Panel en vivo**: Esquina superior derecha
2. **Tabla dinámica**: Filas = movimientos RILSA, Columnas = clases
3. **Exportar**: Botón "💾 Exportar CSV" descarga el bucket activo
4. **Selector**: Dropdown para ver bloques anteriores
5. **Reset**: Botón "🔄 Reset" limpia todos los conteos

---

## 🛠️ Personalizar Mapeo RILSA

Si tu convención de movimientos es diferente, edita `src/lib/rilsa.ts`:

```typescript
const RILSA_MAP: Record<string, number> = {
  'N->E': 1,  // ← Ajustar según tu sistema
  'N->S': 4,
  // ...
};
```

---

## 🐛 Probar sin Motor de Trayectorias

Usa el botón "🚗 Simular Trayectoria" en la UI para generar eventos aleatorios y validar que el sistema funciona.

---

## 📁 Estructura de Archivos

```
apps/web/src/
├── types/aforo.ts                      # ✅ Tipos TypeScript
├── lib/
│   ├── aforoBus.ts                     # ✅ Event bus
│   ├── rilsa.ts                        # ✅ Mapeo RILSA
│   ├── aforoIntegration.ts             # ✅ Conecta bus ↔ store
│   └── trajectoryEmitter.example.ts    # 📖 Ejemplos
├── store/aforoLive.ts                  # ✅ Zustand store
└── components/AforoLivePanel.tsx       # ✅ Panel UI
```

---

## ✅ Checklist de Integración

- [ ] Dependencias instaladas (`npm install`)
- [ ] Servidor dev corriendo (`npm run dev`)
- [ ] Panel visible en esquina superior derecha
- [ ] Evento emitido cuando trayectoria termina
- [ ] Conteo incrementa en tabla
- [ ] Mismo track_id no cuenta dos veces
- [ ] Exportación CSV funciona
- [ ] Buckets de 15 min correctos (:00, :15, :30, :45)

---

## 🚦 Flujo de Datos

```
Usuario → Emoji recorre trayectoria → Sale del área
                    ↓
          aforoBus.publish(event)
                    ↓
            useAforoLive.upsert()
                    ↓
           Bucket de 15 min calculado
                    ↓
          Conteo incrementado (+1)
                    ↓
     AforoLivePanel se re-renderiza
                    ↓
          Usuario ve tabla actualizada
```

---

## 📞 Soporte

Si el conteo no se incrementa:

1. Verifica que `aforoBus.subscriberCount > 0` en consola
2. Revisa que el evento tiene todos los campos requeridos
3. Confirma que `track_id` es único por trayectoria
4. Valida que `origin_cardinal` y `dest_cardinal` son 'N'|'S'|'E'|'O'

---

**¡Todo listo!** El sistema está preparado para conteo en vivo de trayectorias. 🎉
