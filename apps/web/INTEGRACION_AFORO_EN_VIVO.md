# Integración de Aforo por Movimientos RILSA en Vivo

Este documento explica cómo funciona el sistema de aforo por movimientos RILSA integrado en el visualizador en vivo.

## 🎯 Flujo Completo

### Paso 1: Asignación de Puntos Cardinales (OBLIGATORIO)

**Ubicación**: Página de detalle del dataset → Paso 1 "Asignar Puntos Cardinales"

1. El usuario marca los **accesos** en el canvas (Norte, Sur, Este, Oeste)
2. Asigna el **punto cardinal** a cada acceso
3. **Presiona "Guardar Configuración"** ✅

**IMPORTANTE**: Este paso es **obligatorio** y los datos se guardan en:
```
API: POST /api/datasets/{datasetId}/cardinals
Archivo: api/data/dataset_{datasetId}/cardinals.json
```

Ejemplo de `cardinals.json`:
```json
{
  "datasetId": "f8144347",
  "accesses": [
    {
      "id": "access_1",
      "display_name": "Norte",
      "cardinal": "N",
      "cardinal_official": "N",
      "x": 600,
      "y": 100
    },
    {
      "id": "access_2",
      "display_name": "Sur",
      "cardinal": "S",
      "cardinal_official": "S",
      "x": 600,
      "y": 500
    }
    // ... etc
  ],
  "updatedAt": "2025-11-08T22:00:00Z"
}
```

### Paso 2: Configuración del Mapa RILSA (Opcional pero recomendado)

**Ubicación**: Página de detalle → Paso 2 "Configurar Mapa RILSA"

1. Define las **reglas de movimientos** (qué trayectorias corresponden a qué código RILSA)
2. Guarda la configuración

**Archivo guardado**: `api/data/dataset_{datasetId}/rilsa_map.json`

### Paso 3: Visualizador en Vivo CON Tablas de Aforo

**Ubicación**: Página de detalle → Paso 3 "Aforo en Vivo"

Una vez que se han guardado los puntos cardinales (Paso 1):

1. **Carga automática de cardinales**: Al abrir el Paso 3, la aplicación carga automáticamente los puntos cardinales guardados desde el backend
2. **Procesamiento en tiempo real**: Cada evento (trayectoria completada) tiene asignado automáticamente:
   - `origin_cardinal` (punto cardinal de origen)
   - `dest_cardinal` (punto cardinal de destino)
   - `mov_rilsa` (código del movimiento RILSA según origen → destino)
3. **Tablas actualizadas en vivo**: Las tablas de aforo por movimiento se actualizan automáticamente mientras el video se reproduce

## 📊 Códigos RILSA Implementados

### Movimientos Directos (pasan de frente)
- **1**: Norte → Sur
- **2**: Sur → Norte
- **3**: Oeste → Este
- **4**: Este → Oeste

### Giros a la Izquierda (metidos al centro del cruce)
- **5**: Norte → Este
- **6**: Sur → Oeste
- **7**: Oeste → Sur
- **8**: Este → Norte

### Giros a la Derecha (código 9#)
- **91** (9(1)): Norte → Oeste
- **92** (9(2)): Sur → Este
- **93** (9(3)): Oeste → Norte
- **94** (9(4)): Este → Sur

### Retornos en U (código 10#)
- **101** (10(1)): U-turn en acceso Norte
- **102** (10(2)): U-turn en acceso Sur
- **103** (10(3)): U-turn en acceso Oeste
- **104** (10(4)): U-turn en acceso Este

## 🔄 Persistencia de Puntos Cardinales

### ¿Cómo se Guardan?

Cuando el usuario presiona **"Guardar Configuración"** en el Paso 1:

```typescript
// Código en AforoDetailPage.tsx
const handleSaveCardinalsConfig = async () => {
  const config: CardinalsConfig = {
    datasetId,
    accesses,
    updatedAt: new Date().toISOString(),
  };

  await saveCardinals(datasetId, config);
};
```

Esto hace un `POST` al backend que guarda el archivo JSON.

### ¿Cómo se Cargan Automáticamente?

Cuando se abre el Paso 3 (LivePlaybackView):

```typescript
// Código en LivePlaybackView.tsx (línea 245)
useEffect(() => {
  const loadAccessesFromBackend = async () => {
    try {
      const res = await fetch(`http://localhost:3004/api/datasets/${datasetId}/cardinals`);
      if (res.ok) {
        const data = await res.json();
        const accessesWithCoords = (data.accesses || []).map((acc: any) => ({ ...acc }));
        setAccesses(accessesWithCoords);
      }
    } catch (error) {
      console.error('Error loading cardinals:', error);
    }
  };

  loadAccessesFromBackend();
}, [datasetId]);
```

**IMPORTANTE**: Los puntos cardinales **NO** se reinician cada vez que abres el visualizador. Se cargan desde el archivo guardado en el backend.

### ¿Qué Pasa si NO Hay Cardinales Guardados?

Si intentas abrir el Paso 3 sin haber guardado los puntos cardinales en el Paso 1:

1. La carga de cardinales falla (404)
2. Los eventos **NO tendrán** `origin_cardinal` y `dest_cardinal` asignados
3. **Las tablas de aforo NO funcionarán correctamente**

**Solución**: Siempre debes completar el Paso 1 y guardar la configuración antes de usar el Paso 3.

## 🧪 Verificación del Sistema

### Verificar que los Cardinales Están Guardados

```bash
# Verificar que existe el archivo
ls api/data/dataset_f8144347/cardinals.json

# Ver el contenido
cat api/data/dataset_f8144347/cardinals.json
```

### Verificar que se Cargan en el Visualizador

1. Abre el visualizador en vivo (Paso 3)
2. Abre DevTools (F12)
3. Ve a la pestaña **Console**
4. Busca el mensaje: `Accesses loaded: [...]`
5. Si ves `accesses.length > 0`, los cardinales se cargaron correctamente

### Verificar que los Movimientos Son Correctos

En las tablas de aforo, verifica que:

1. **Mov 1**: Norte → Sur
2. **Mov 2**: Sur → Norte
3. **Mov 3**: Oeste → Este
4. **Mov 4**: Este → Oeste
5. **Mov 5**: Norte → Este (giro izquierda)
6. **Mov 6**: Sur → Oeste (giro izquierda)
7. Etc.

Si los movimientos no coinciden con los puntos cardinales que asignaste, verifica:
- Que guardaste correctamente en el Paso 1
- Que los eventos tienen `origin_cardinal` y `dest_cardinal` correctos

## 🛠️ Solución de Problemas

### Problema: "Las tablas están vacías"

**Posibles causas**:
1. No se guardaron los puntos cardinales en el Paso 1
2. No hay eventos procesados todavía (el video no ha iniciado)
3. Los eventos no tienen `mov_rilsa` asignado

**Solución**:
1. Vuelve al Paso 1 y guarda los puntos cardinales
2. Inicia la reproducción del video
3. Verifica en consola que los eventos tienen datos

### Problema: "Los movimientos no coinciden con mis cardinales"

**Causa**: El backend está asignando movimientos RILSA basándose en cardinales antiguos o incorrectos.

**Solución**:
1. Vuelve al Paso 1
2. Borra todos los accesos existentes
3. Vuelve a crear los accesos con los puntos cardinales correctos
4. Guarda la configuración
5. Vuelve al Paso 3 y recarga la página

### Problema: "Los cardinales se 'reinician' cada vez que abro el visualizador"

**Esto NO debería pasar** si el sistema funciona correctamente.

**Verificar**:
1. Que el backend está guardando correctamente:
   ```bash
   curl http://localhost:3004/api/datasets/f8144347/cardinals
   ```
2. Que no hay errores en la consola del navegador al cargar
3. Que el archivo JSON existe en `api/data/dataset_*/cardinals.json`

Si los cardinales se pierden, es un problema del backend, no del frontend.

## 📝 Archivos Modificados

### Frontend (apps/web/src/)
- `lib/procesarAforoEnVivo.ts` - Procesa eventos en vivo a datos de aforo
- `components/Config/LivePlaybackView.tsx` - Visualizador con tablas integradas
- `types/aforo.ts` - Tipos y mapeo de movimientos RILSA (corregidos)

### Backend (api/)
- `routes/datasets.py` - Endpoints para guardar/cargar cardinales
- `data/dataset_{id}/cardinals.json` - Archivo de configuración guardado

## 🎓 Resumen

1. **Paso 1 es OBLIGATORIO**: Sin guardar los puntos cardinales, el aforo en vivo no funciona
2. **Los cardinales son persistentes**: Se guardan en el backend y se cargan automáticamente
3. **Las tablas se actualizan en tiempo real**: A medida que el video avanza, los conteos se actualizan
4. **Los movimientos RILSA son correctos**: Según la nomenclatura estándar que especificaste

---

**Última actualización**: Noviembre 2025
**Versión**: 1.0.0
