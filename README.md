# Proyecto Aforos RILSA – Bogotá Traffic

Este repositorio contiene un sistema completo para procesar videos de tránsito y generar aforos vehiculares y peatonales siguiendo la nomenclatura RILSA.  
Incluye un backend FastAPI, un frontend React y scripts utilitarios para validar y consolidar datos de múltiples videos.

## 📚 Documentación principal

La documentación operativa se concentra en un único manual: [`MANUAL_PASO_A_PASO.md`](./MANUAL_PASO_A_PASO.md).  
Allí encontrará instrucciones detalladas para instalar el proyecto, configurar los servicios, subir videos (`.pkl`), asignar cardinales, procesar los datos, realizar validaciones y exportar resultados.

## 🚀 Inicio rápido

1. Asegúrese de tener [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/) instalados.  
2. Ejecute:

```bash
docker-compose up --build -d
```

3. Abra el navegador en [http://localhost:3000](http://localhost:3000) para acceder al frontend.  
   La API estará disponible en [http://localhost:3004](http://localhost:3004).

## 🛠 Servicios y puertos

| Servicio           | Puerto | Descripción                        |
|-------------------|:------:|------------------------------------|
| Frontend (React)  | **3000** | Interfaz para cargar y configurar datasets |
| Backend (FastAPI) | **3004** | API de gestión de datasets y configuración |
| PostgreSQL        | **5432** | Base de datos para metadatos y resultados |
| Redis (opcional)  | **6379** | Caché/cola para validaciones asíncronas    |

Estos valores son fijos por diseño.  
Si un puerto está ocupado, libérelo antes de ejecutar el proyecto.

## 📦 Contenido del repositorio

- `api/` – Backend FastAPI con routers para datasets, configuración y validación.
- `apps/` – Frontend React/Vite (gestión de datasets y configuración).
- `yolo_carla_pipeline/` – Módulos de procesamiento de trayectorias y generación de aforos.
- `docker-compose.yml` – Orquestación de servicios con Docker.
- `.env.example` – Variables de entorno de ejemplo.
- `MANUAL_PASO_A_PASO.md` – Guía paso a paso para usuarios.

## ❓ Soporte

Para dudas sobre el uso o contribución, consulte el manual y los documentos en la carpeta `docs/`.  
Si necesita más ayuda, abra un issue en el repositorio original.
