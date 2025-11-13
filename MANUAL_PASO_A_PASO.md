# Manual paso a paso – Aforos RILSA

Este manual resume cómo instalar, configurar y ejecutar el sistema de aforos basado en RILSA incluido en este repositorio.

## 1. Servicios y puertos fijos

El sistema utiliza varios servicios que se comunican entre sí. **No cambie estos puertos**, porque el frontend y el backend están configurados para ellos por defecto:

| Servicio                    | Puerto | Descripción                                         |
|----------------------------|:------:|-----------------------------------------------------|
| Frontend de gestión        |  **3000** | Interfaz React/Vite para subir y configurar datasets |
| API de gestión (`api`)     |  **3004** | Backend FastAPI para cargar PKL y editar configuraciones |
| Base de datos PostgreSQL   |  **5432** | Almacena metadatos y resultados                      |
| Redis (caché/cola)         |  **6379** | Opcional para colas y almacenamiento temporal        |

> **Nota:** si alguno de estos puertos está ocupado en su máquina, libérelo antes de ejecutar el proyecto (consulte la sección 2).

## 2. Instalación rápida con Docker

1. Instale [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/).
2. Clone este repositorio o copie la carpeta `Aforos_clean` en su máquina.
3. Desde la raíz del proyecto, ejecute:

```bash
docker‑compose up --build -d
```

Esto construirá las imágenes de backend y frontend, y levantará los servicios definidos en `docker-compose.yml`.  
Acceda al frontend en [http://localhost:3000](http://localhost:3000). La API de gestión estará disponible en [http://localhost:3004](http://localhost:3004).

Si obtiene errores porque algún puerto está en uso, libere el proceso que lo ocupa. Por ejemplo, en PowerShell:

```powershell
# Mostrar procesos que usan el puerto 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess
# Finalizar el proceso (reemplace 1234 por el PID real)
Stop-Process -Id 1234 -Force
```

## 3. Flujo de trabajo recomendado

El flujo básico para generar un aforo completo con movimientos RILSA es el siguiente:

1. **Subir PKL**: cargue un archivo `.pkl` desde el frontend de gestión o mediante la API:
   ```bash
   curl -X POST -F file=@GX010323.pkl http://localhost:3004/api/datasets
   ```
   Esto almacena el PKL y normaliza los datos a formato Parquet. La respuesta incluye un `id` del dataset.

2. **Asignar cardinales y delimitaciones**: en el frontend, dibuje los polígonos de entrada y salida para cada acceso (N, S, E, O) y establezca los puntos cardinales. También puede hacerlo mediante la API:
   ```bash
   curl -X PUT -H 'Content-Type: application/json' \
        -d '{"N": {...}, "S": {...}, "E": {...}, "O": {...}}' \
        http://localhost:3004/api/v1/datasets/<id>/cardinals
   ```
   Use el endpoint de delimitaciones para áreas de entrada/salida y U‑turns.

3. **Inferir movimientos RILSA**: una vez definidos los polígonos, solicite al sistema que genere el mapa de movimientos válidos de acuerdo con la nomenclatura RILSA.  
   Esto asigna códigos 1–10(4) (vehículos) y P1–P4 (peatones) según el origen/destino.

4. **Procesar y validar automáticamente**: inicie el procesamiento del aforo y la validación básica.  
   Esto ejecuta el seguimiento, clasifica los movimientos, agrega conteos en intervalos de 15 min y calcula estadísticas de validación rápida.

5. **Opcional – Validación avanzada**: si necesita estadísticas robustas, ejecute corridas adicionales con diferentes semillas y parámetros para estimar la variabilidad. Puede hacerlo desde la API de validación.

6. **Edición manual**: revise las trayectorias detectadas y corrija manualmente los errores de seguimiento o clasificación (por ejemplo, reasignar un vehículo a otro movimiento). Use los endpoints de corrección o el editor visual del frontend.

7. **Visualización y exportación**: visualice las series temporales y el diagrama RILSA interactivo. Descargue los reportes en CSV y PDF.

## 4. Endpoints clave de la API de gestión

- **POST `/api/datasets`** – Cargar un nuevo PKL y normalizarlo.  
- **GET `/api/datasets`** – Listar datasets cargados.  
- **PUT `/api/v1/datasets/{id}/cardinals`** – Guardar configuración de cardinales.  
- **PUT `/api/v1/datasets/{id}/delimiters`** – Guardar polígonos de entrada/salida.  
- **POST `/api/v1/datasets/{id}/infer-movements`** – Inferir movimientos RILSA desde la configuración.  
- **POST `/api/v1/aforos/process/run?pkl_id={id}`** – Iniciar procesamiento y validación automática.  
- **GET `/api/v1/aforos/status/{job_id}`** – Consultar progreso del procesamiento.  
- **POST `/api/v1/aforos/validate`** – Ejecutar validación avanzada con varias corridas (si está implementada).  
- **POST `/api/v1/aforos/multiaforo`** – Calcular consenso de varios PKL de la misma intersección (manual).  
- **GET `/api/v1/datasets/{id}/trajectory-corrections`** – Obtener correcciones manuales.  
- **POST `/api/v1/datasets/{id}/trajectory-corrections`** – Aplicar correcciones manuales.  

## 5. Consejos de operación

- **No cambie los puertos.** Si necesita usar otros puertos, modifíquelos de forma consistente en `docker-compose.yml`, `.env.example`, `vite.config.ts` y la documentación, y asegúrese de que el frontend conozca la nueva URL de la API.
- **Realice validaciones por PKL** antes de entregar resultados.  
  Si las métricas (por ejemplo, MAPE, coeficiente de variación) exceden los umbrales aceptables, revise los parámetros de detección o realice correcciones manuales.
- **Use la función de multiaforo** para comparar varias grabaciones de una misma intersección y obtener un consenso robusto de conteos y movimientos.
- **Revise la guía de mantenimiento** y los scripts de auditoría para asegurar que la configuración permanezca coherente (puertos, estructuras de directorios, etc.).

## 6. Recursos adicionales

Para más detalles sobre la arquitectura interna, los componentes y la contribución al proyecto, consulte los documentos en la carpeta `docs/` y el archivo `README.md` en la raíz del repositorio.
