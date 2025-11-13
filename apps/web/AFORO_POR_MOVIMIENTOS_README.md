# Sistema de Visualización de Aforo por Movimientos RILSA

Este documento describe el sistema completo de visualización de datos de aforo vehicular organizado por movimientos RILSA, implementado para el proyecto de aforos de tránsito.

## 📋 Descripción General

El sistema permite visualizar y exportar datos de aforo vehicular organizados por movimientos RILSA (1-10), mostrando conteos de vehículos en intervalos de 15 minutos con una presentación estilo Excel directamente en la aplicación web.

### Características Principales

- ✅ **Tablas estilo Excel** - Visualización familiar con bordes, zebra striping y encabezados fijos
- ✅ **Navegación por pestañas** - Tab de volúmenes totales + tabs individuales por cada movimiento detectado
- ✅ **Exportación CSV** - Botón de exportación en cada tabla
- ✅ **Responsive** - Adaptable a diferentes tamaños de pantalla
- ✅ **Movimientos dinámicos** - Solo muestra movimientos con datos reales
- ✅ **Metadatos integrados** - Ubicación, fecha y periodo del conteo siempre visibles

## 📁 Estructura de Archivos

```
apps/web/src/
├── types/
│   └── aforo.ts                              # Tipos TypeScript (extendidos con nuevos tipos)
├── lib/
│   ├── procesarAforoPorMovimiento.ts         # Lógica de procesamiento de datos
│   └── exportarCSV.ts                        # Funciones de exportación
└── components/aforos/
    ├── TablaVolumen.tsx                      # Componente de tabla individual
    ├── TablaVolumen.css                      # Estilos tipo Excel
    ├── AforoMovimientosTabs.tsx              # Sistema de pestañas
    ├── AforoMovimientosTabs.css              # Estilos de pestañas
    └── AforoMovimientosDemo.tsx              # Componente de demostración/integración
```

## 🔧 Componentes

### 1. `TablaVolumen`

Componente reutilizable que renderiza una tabla de volúmenes con estilo Excel.

**Props:**
- `titulo`: Título de la tabla (ej: "VOLUMENES TOTALES")
- `subtitulo`: Ubicación y fecha
- `descripcion`: Descripción adicional
- `filas`: Array de datos de intervalos de 15 min
- `totales`: Totales por categoría vehicular
- `onExportarCSV`: Callback para exportar

**Ejemplo:**
```tsx
<TablaVolumen
  titulo="MOVIMIENTO RILSA 1: N → S"
  subtitulo="Ubicación: Gx010322 | Fecha: 13 de agosto de 2025"
  filas={[
    { periodo: "06:00 - 06:15", autos: 27, buses: 1, camiones: 2, motos: 29, bicicletas: 0, timestamp_inicio: "2025-08-13 06:00:00" },
    // ...más filas
  ]}
  totales={{ autos: 500, buses: 20, camiones: 45, motos: 300, bicicletas: 15 }}
  onExportarCSV={() => exportarTablaACSV(...)}
/>
```

### 2. `AforoMovimientosTabs`

Componente principal con sistema de pestañas para navegar entre volúmenes totales y movimientos individuales.

**Props:**
- `datos`: Objeto `DatosAforoPorMovimiento` con toda la información procesada

**Ejemplo:**
```tsx
<AforoMovimientosTabs datos={datosAforoProcesados} />
```

### 3. `AforoMovimientosDemo`

Componente de alto nivel que carga datos desde CSV y muestra el sistema completo.

**Props:**
- `datasetId`: ID del dataset/aforo
- `csvUrl`: (Opcional) URL al CSV de volúmenes
- `metadata`: (Opcional) Ubicación y fecha

**Ejemplo:**
```tsx
<AforoMovimientosDemo
  datasetId="f8144347"
  metadata={{
    ubicacion: "Glorieta X01",
    fecha: "13 de agosto de 2025"
  }}
/>
```

## 🎨 Estilos

### Estilo Excel

Las tablas usan estilos CSS que emulan hojas de cálculo Excel:

- **Encabezados**: Fondo degradado oscuro, texto blanco, sticky al hacer scroll
- **Zebra striping**: Filas alternadas (blanco / gris claro)
- **Hover**: Resaltado azul claro al pasar el mouse
- **Fila de totales**: Fondo verde degradado, sticky en el bottom
- **Bordes**: Bordes sutiles entre celdas
- **Tipografía**: Números en fuente monoespaciada, alineados a la derecha

### Personalización

Los estilos se pueden personalizar editando:
- `TablaVolumen.css` - Estilos de tablas
- `AforoMovimientosTabs.css` - Estilos de pestañas

## 📊 Procesamiento de Datos

### Flujo de Datos

1. **Entrada**: CSV con formato:
   ```csv
   timestamp_inicio,periodo,ramal,movimiento_rilsa,clase,conteo
   2025-08-13 06:00:00,mañana,E,2,car,27
   2025-08-13 06:00:00,mañana,E,2,motorcycle,29
   ...
   ```

2. **Procesamiento**:
   - Clasificación de vehículos (car → autos, truck → camiones, etc.)
   - Agrupación por intervalos de 15 minutos
   - Asignación a movimientos RILSA
   - Cálculo de totales

3. **Salida**: Objeto `DatosAforoPorMovimiento`:
   ```typescript
   {
     metadata: { ubicacion, fecha, hora_inicio, hora_fin },
     volumenes_totales: { filas, totales },
     movimientos: {
       1: { codigo, nombre, tipo, filas, totales },
       2: { codigo, nombre, tipo, filas, totales },
       ...
     }
   }
   ```

### Clasificación de Vehículos

| Clase detectada | Categoría en tabla |
|----------------|-------------------|
| `car` | Autos |
| `bus` | Buses |
| `truck` | Camiones |
| `motorcycle` | Motos |
| `bicycle` | Bicicletas |
| `person` | *(excluido - se maneja aparte)* |

### Movimientos RILSA

#### 1. Movimientos Directos (pasan de frente)

| Código | Nombre | Descripción |
|--------|---------|-------------|
| 1 | N → S | Del Norte al Sur |
| 2 | S → N | Del Sur al Norte |
| 3 | O → E | Del Oeste al Este |
| 4 | E → O | Del Este al Oeste |

#### 2. Giros a la Izquierda (metidos al centro del cruce)

| Código | Nombre | Descripción |
|--------|---------|-------------|
| 5 | N → E | Del Norte al Este |
| 6 | S → O | Del Sur al Oeste |
| 7 | O → S | Del Oeste al Sur |
| 8 | E → N | Del Este al Norte |

#### 3. Giros a la Derecha (codificados como 9(#))

| Código | Nombre | Descripción |
|--------|---------|-------------|
| 9 ó 91 | N → O | Del Norte al Oeste - 9(1) |
| 92 | S → E | Del Sur al Este - 9(2) |
| 93 | O → N | Del Oeste al Norte - 9(3) |
| 94 | E → S | Del Este al Sur - 9(4) |

#### 4. Giros en U (codificados como 10(#))

| Código | Nombre | Descripción |
|--------|---------|-------------|
| 10 ó 101 | U-turn Norte | Retorno en U en acceso Norte - 10(1) |
| 102 | U-turn Sur | Retorno en U en acceso Sur - 10(2) |
| 103 | U-turn Oeste | Retorno en U en acceso Oeste - 10(3) |
| 104 | U-turn Este | Retorno en U en acceso Este - 10(4) |

## 💾 Exportación

### Exportar Tabla Individual

Cada tabla tiene un botón "Exportar CSV" que descarga los datos visibles.

**Formato del archivo CSV exportado:**
```csv
# Ubicación: Gx010322
# Fecha: 13 de agosto de 2025

Periodo,Autos,Buses,Camiones,Motos,Bicicletas
06:00 - 06:15,27,1,2,29,0
06:15 - 06:30,38,0,1,35,2
...
TOTAL,500,20,45,300,15
```

**Nombre del archivo:** `Mov1_N-S_20250813.csv` (ejemplo)

### Exportar Todos los Movimientos

```typescript
import { exportarTodosLosMovimientos } from '@/lib/exportarCSV';

await exportarTodosLosMovimientos(datos, {
  incluirTotales: true
});
```

Esto descargará un CSV por cada movimiento + el CSV de totales.

## 🚀 Integración en la Aplicación

### Opción 1: Usar el Componente Demo

```tsx
import { AforoMovimientosDemo } from '@/components/aforos/AforoMovimientosDemo';

export default function MiPaginaAforo() {
  const { datasetId } = useParams();

  return (
    <div>
      <h1>Análisis de Aforo</h1>
      <AforoMovimientosDemo
        datasetId={datasetId}
        metadata={{
          ubicacion: "Intersección XYZ",
          fecha: "13 de agosto de 2025"
        }}
      />
    </div>
  );
}
```

### Opción 2: Procesar Datos Manualmente

```tsx
import { useEffect, useState } from 'react';
import { cargarYProcesarCSV } from '@/lib/procesarAforoPorMovimiento';
import { AforoMovimientosTabs } from '@/components/aforos/AforoMovimientosTabs';

export default function MiComponente() {
  const [datos, setDatos] = useState(null);

  useEffect(() => {
    cargarYProcesarCSV('/ruta/al/csv.csv', {
      ubicacion: 'Mi ubicación',
      fecha: '13 de agosto de 2025'
    }).then(setDatos);
  }, []);

  if (!datos) return <div>Cargando...</div>;

  return <AforoMovimientosTabs datos={datos} />;
}
```

### Opción 3: Con Datos desde API

```tsx
import { procesarDatosAforoPorMovimiento } from '@/lib/procesarAforoPorMovimiento';

// Obtener datos de API
const response = await fetch('/api/aforos/volumenes');
const registros = await response.json();

// Procesar
const datos = procesarDatosAforoPorMovimiento(registros, {
  ubicacion: 'Mi ubicación',
  fecha: '13 de agosto de 2025'
});

// Renderizar
<AforoMovimientosTabs datos={datos} />
```

## ✅ Criterios de Validación

### Verificación de Conteos

Los conteos se pueden validar asegurando que:

1. **Suma de movimientos = Total general** (por intervalo)
2. **Sin filas vacías** para movimientos sin datos
3. **Totales correctos** al final de cada tabla
4. **Intervalos completos** de 15 minutos

### Ejemplo de Verificación

```typescript
// Verificar que la suma de todos los movimientos coincida con el total
const totalAutos = Object.values(datos.movimientos).reduce(
  (sum, mov) => sum + mov.totales.autos,
  0
);

console.assert(
  totalAutos === datos.volumenes_totales.totales.autos,
  'Los totales de autos no coinciden'
);
```

## 🐛 Solución de Problemas

### "No hay datos para procesar"

**Causa:** El CSV está vacío o mal formateado.

**Solución:** Verificar que el CSV tenga el formato correcto con encabezados.

### "TypeError: datos.movimientos is undefined"

**Causa:** Los datos no fueron procesados correctamente.

**Solución:** Asegurar que `procesarDatosAforoPorMovimiento` se ejecutó exitosamente.

### Los totales no coinciden

**Causa:** Clasificación incorrecta de vehículos o movimientos duplicados.

**Solución:** Revisar la lógica en `procesarAforoPorMovimiento.ts`.

### Tabla no se renderiza

**Causa:** Faltan imports de CSS.

**Solución:** Asegurar que los archivos CSS están siendo importados:
```tsx
import './TablaVolumen.css';
import './AforoMovimientosTabs.css';
```

## 📝 Notas Técnicas

- **React 18+** requerido para hooks
- **TypeScript** 5.0+ para tipos
- **No requiere librerías externas** para visualización (solo React)
- **Tamaño mínimo** - ~15KB gzipped (componentes + estilos)
- **Compatible con** Chrome, Firefox, Safari, Edge

## 🔮 Futuras Mejoras

- [ ] Filtros por periodo del día (mañana/tarde)
- [ ] Gráficos integrados (barras, líneas)
- [ ] Comparación entre múltiples aforos
- [ ] Exportación a Excel (.xlsx) con formato
- [ ] Impresión optimizada
- [ ] Modo oscuro
- [ ] Internacionalización (i18n)

## 📞 Soporte

Para preguntas o problemas con este sistema, contactar al equipo de desarrollo o abrir un issue en el repositorio del proyecto.

---

**Versión:** 1.0.0
**Última actualización:** Noviembre 2025
