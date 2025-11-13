"""
Generador de Heatmap de Zonas de Acceso.

Visualiza las zonas más fuertes de acceso (entrada/salida combinadas)
mostrando dónde hay mayor actividad de tráfico.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AccessZonesAnalyzer:
    """Analizador de zonas de acceso."""

    def __init__(self, combined_data_path: str):
        """Inicializa el analizador."""
        logger.info(f"Cargando datos desde: {combined_data_path}")

        with open(combined_data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.trajectories = self.data['trajectories']
        self.aforos = self.data['aforos']

        logger.info(f"  - Total trayectorias: {len(self.trajectories)}")
        logger.info(f"  - Total aforos: {len(self.aforos)}")

    def extract_access_points(self) -> List[Dict]:
        """Extrae todos los puntos de acceso (entrada + salida)."""
        access_points = []

        logger.info("\nExtrayendo puntos de acceso...")

        for traj in self.trajectories:
            positions = traj['positions']

            if len(positions) < 2:
                continue

            # Punto de entrada
            access_points.append({
                'x': positions[0][0],
                'y': positions[0][1],
                'aforo_id': traj.get('aforo_id', 'unknown'),
                'clase': traj.get('clase', 'unknown'),
                'tipo': 'acceso'
            })

            # Punto de salida
            access_points.append({
                'x': positions[-1][0],
                'y': positions[-1][1],
                'aforo_id': traj.get('aforo_id', 'unknown'),
                'clase': traj.get('clase', 'unknown'),
                'tipo': 'acceso'
            })

        logger.info(f"  - Puntos de acceso extraídos: {len(access_points)}")
        return access_points

    def calculate_grid_density(self, points: List[Dict], grid_size: int = 50) -> Dict:
        """Calcula densidad en una cuadrícula."""
        density_grid = defaultdict(int)

        for point in points:
            x, y = point['x'], point['y']
            grid_x = int(x // grid_size)
            grid_y = int(y // grid_size)
            grid_key = f"{grid_x},{grid_y}"
            density_grid[grid_key] += 1

        return dict(density_grid)

    def find_hotspots(self, density_grid: Dict, top_n: int = 15) -> List[tuple]:
        """Identifica las zonas más calientes."""
        sorted_zones = sorted(density_grid.items(), key=lambda x: x[1], reverse=True)
        return sorted_zones[:top_n]

    def analyze(self, grid_size: int = 50) -> Dict:
        """Realiza análisis de zonas de acceso."""
        logger.info("\n" + "="*70)
        logger.info("ANÁLISIS DE ZONAS DE ACCESO")
        logger.info("="*70)

        # Extraer puntos
        access_points = self.extract_access_points()

        # Calcular densidad
        density_grid = self.calculate_grid_density(access_points, grid_size)

        # Encontrar hotspots
        hotspots = self.find_hotspots(density_grid, top_n=15)

        # Estadísticas por aforo
        access_by_aforo = defaultdict(list)
        for point in access_points:
            access_by_aforo[point['aforo_id']].append(point)

        aforo_stats = {}
        for aforo_id, points in access_by_aforo.items():
            aforo_density = self.calculate_grid_density(points, grid_size)
            aforo_stats[aforo_id] = {
                'num_accesos': len(points),
                'hotspots': self.find_hotspots(aforo_density, top_n=5)
            }

        logger.info("\n" + "="*70)
        logger.info("RESULTADOS DEL ANÁLISIS")
        logger.info("="*70)

        logger.info(f"\nTotal de accesos: {len(access_points)}")
        logger.info(f"\nTop 15 Zonas de ACCESO más fuertes:")
        for i, (zone, count) in enumerate(hotspots, 1):
            grid_coords = zone.split(',')
            x_center = (int(grid_coords[0]) + 0.5) * grid_size
            y_center = (int(grid_coords[1]) + 0.5) * grid_size
            logger.info(f"  {i}. Zona ({x_center:.0f}, {y_center:.0f}) - {count} accesos")

        logger.info("\nAnálisis por AFORO:")
        for aforo_id, stats in aforo_stats.items():
            aforo_info = next((a for a in self.aforos if a['id'] == aforo_id), None)
            nombre = aforo_info['nombre'] if aforo_info else aforo_id
            logger.info(f"\n  {nombre}:")
            logger.info(f"    - Total accesos: {stats['num_accesos']}")
            logger.info(f"    - Top 3 zonas más fuertes:")
            for i, (zone, count) in enumerate(stats['hotspots'][:3], 1):
                logger.info(f"      {i}. {count} accesos")

        return {
            'access_points': access_points,
            'density_grid': density_grid,
            'hotspots': hotspots,
            'aforo_stats': aforo_stats,
            'grid_size': grid_size
        }

    def _zone_to_coords(self, zone: str, grid_size: int) -> List[float]:
        """Convierte coordenadas de zona a coordenadas centrales."""
        grid_coords = zone.split(',')
        x_center = (int(grid_coords[0]) + 0.5) * grid_size
        y_center = (int(grid_coords[1]) + 0.5) * grid_size
        return [x_center, y_center]

    def generate_html(self, analysis_results: Dict, output_path: str):
        """Genera dashboard HTML con heatmap."""
        hotspots_data = [
            {
                'zone': zone,
                'count': count,
                'coordinates': self._zone_to_coords(zone, analysis_results['grid_size'])
            }
            for zone, count in analysis_results['hotspots']
        ]

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zonas de Acceso - Bogotá Traffic</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            overflow: hidden;
        }}

        .container {{
            display: flex;
            height: 100vh;
        }}

        .sidebar {{
            width: 350px;
            background: #1a1a1a;
            border-right: 1px solid #333;
            overflow-y: auto;
            padding: 20px;
        }}

        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        .header {{
            background: #1a1a1a;
            padding: 15px 20px;
            border-bottom: 1px solid #333;
        }}

        .header h1 {{
            font-size: 20px;
            color: #fff;
            margin: 0;
        }}

        .canvas-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
            background: #0a0a0a;
        }}

        canvas {{
            position: absolute;
            cursor: move;
        }}

        .section {{
            margin-bottom: 25px;
        }}

        .section h3 {{
            color: #fff;
            font-size: 16px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #333;
        }}

        .stat-item {{
            background: #252525;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 3px solid #3498db;
        }}

        .stat-title {{
            font-size: 13px;
            color: #aaa;
            margin-bottom: 4px;
        }}

        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #fff;
        }}

        .hotspot {{
            background: #2a2a2a;
            padding: 10px 12px;
            margin-bottom: 6px;
            border-radius: 5px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
            cursor: pointer;
            border: 2px solid transparent;
        }}

        .hotspot:hover {{
            background: #333;
        }}

        .hotspot.selected {{
            background: #34495e;
            border: 2px solid #3498db;
        }}

        .hotspot-rank {{
            background: #f39c12;
            color: #fff;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 13px;
            flex-shrink: 0;
        }}

        .hotspot-rank.top-3 {{
            background: #e74c3c;
        }}

        .hotspot-info {{
            flex: 1;
            margin-left: 12px;
        }}

        .hotspot-coords {{
            color: #aaa;
            font-size: 11px;
        }}

        .hotspot-count {{
            color: #f39c12;
            font-weight: bold;
            font-size: 15px;
        }}

        .toggle-btn {{
            background: #2c3e50;
            color: #fff;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            margin-bottom: 8px;
            font-size: 14px;
            transition: background 0.3s;
        }}

        .toggle-btn.active {{
            background: #3498db;
        }}

        .toggle-btn:hover {{
            background: #34495e;
        }}

        .toggle-btn.active:hover {{
            background: #2980b9;
        }}

        .zoom-controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 10;
        }}

        .zoom-btn {{
            background: rgba(26, 26, 26, 0.95);
            border: 1px solid #333;
            color: #fff;
            width: 45px;
            height: 45px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }}

        .zoom-btn:hover {{
            background: rgba(52, 152, 219, 0.95);
            transform: scale(1.1);
        }}

        .aforo-item {{
            background: #252525;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 3px solid;
        }}

        .aforo-name {{
            font-size: 13px;
            color: #fff;
            margin-bottom: 4px;
        }}

        .aforo-stat {{
            font-size: 11px;
            color: #aaa;
        }}

        .intensity-bar {{
            height: 4px;
            background: linear-gradient(90deg, #3498db, #f39c12, #e74c3c);
            margin-top: 15px;
            border-radius: 2px;
            position: relative;
        }}

        .intensity-label {{
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #666;
            margin-top: 5px;
        }}

        .cardinal-buttons {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 10px;
        }}

        .cardinal-btn {{
            background: #2c3e50;
            color: #fff;
            border: 2px solid #34495e;
            padding: 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s;
            text-align: center;
        }}

        .cardinal-btn:hover {{
            background: #34495e;
            border-color: #3498db;
        }}

        .cardinal-btn.selected {{
            background: #3498db;
            border-color: #3498db;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.5);
        }}

        .cardinal-btn.norte {{
            grid-column: 1 / -1;
        }}

        .cardinal-badge {{
            display: inline-block;
            background: #27ae60;
            color: #fff;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 5px;
        }}

        .cardinal-badge.norte {{
            background: #e74c3c;
        }}

        .cardinal-badge.sur {{
            background: #3498db;
        }}

        .cardinal-badge.este {{
            background: #f39c12;
        }}

        .cardinal-badge.oeste {{
            background: #9b59b6;
        }}

        .assignment-info {{
            background: #1a1a1a;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-size: 12px;
            color: #aaa;
            min-height: 40px;
        }}

        .assignment-info.active {{
            color: #3498db;
            border: 1px solid #3498db;
        }}

        .export-btn {{
            background: #27ae60;
            color: #fff;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
            transition: background 0.3s;
        }}

        .export-btn:hover {{
            background: #229954;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="section">
                <h3>🗺️ Zonas de Acceso</h3>
                <div class="stat-item">
                    <div class="stat-title">Total de Accesos Detectados</div>
                    <div class="stat-value">{len(analysis_results['access_points']):,}</div>
                </div>
            </div>

            <div class="section">
                <h3>🎮 Controles</h3>
                <button class="toggle-btn active" id="toggleHeatmap">Mostrar Heatmap</button>
                <button class="toggle-btn active" id="togglePoints">Mostrar Puntos</button>
                <button class="toggle-btn active" id="toggleLabels">Mostrar Etiquetas</button>
            </div>

            <div class="section">
                <h3>🧭 Asignar Puntos Cardinales</h3>
                <div class="assignment-info" id="assignmentInfo">
                    Selecciona una zona y luego un punto cardinal
                </div>
                <div class="cardinal-buttons">
                    <button class="cardinal-btn norte" data-cardinal="norte">⬆️ NORTE</button>
                    <button class="cardinal-btn" data-cardinal="este">➡️ ESTE</button>
                    <button class="cardinal-btn" data-cardinal="oeste">⬅️ OESTE</button>
                    <button class="cardinal-btn" data-cardinal="sur">⬇️ SUR</button>
                </div>
                <button class="export-btn" id="exportAssignments">💾 Exportar Asignaciones</button>
            </div>

            <div class="section">
                <h3>🔥 Top 15 Zonas Más Fuertes</h3>
                <div id="hotspotsList"></div>
                <div class="intensity-bar"></div>
                <div class="intensity-label">
                    <span>Baja</span>
                    <span>Alta</span>
                </div>
            </div>

            <div class="section">
                <h3>📍 Aforos</h3>
                <div id="aforosList"></div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <h1>🔥 Mapa de Zonas de Acceso - Sistema Multi-Aforo Bogotá</h1>
            </div>
            <div class="canvas-container" id="canvasContainer">
                <canvas id="heatmapCanvas"></canvas>
                <canvas id="pointsCanvas"></canvas>
                <div class="zoom-controls">
                    <button class="zoom-btn" id="zoomIn" title="Acercar">+</button>
                    <button class="zoom-btn" id="zoomOut" title="Alejar">−</button>
                    <button class="zoom-btn" id="resetZoom" title="Restablecer">⟲</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Datos
        const accessPoints = {json.dumps([{'x': p['x'], 'y': p['y']} for p in analysis_results['access_points']], ensure_ascii=False)};
        const hotspots = {json.dumps(hotspots_data, ensure_ascii=False)};
        const aforos = {json.dumps(self.aforos, ensure_ascii=False)};
        const gridSize = {analysis_results['grid_size']};
        const densityGrid = {json.dumps(analysis_results['density_grid'], ensure_ascii=False)};

        // Canvas setup
        const container = document.getElementById('canvasContainer');
        const heatmapCanvas = document.getElementById('heatmapCanvas');
        const pointsCanvas = document.getElementById('pointsCanvas');
        const heatmapCtx = heatmapCanvas.getContext('2d');
        const pointsCtx = pointsCanvas.getContext('2d');

        let canvasWidth = 3000;
        let canvasHeight = 2000;
        heatmapCanvas.width = canvasWidth;
        heatmapCanvas.height = canvasHeight;
        pointsCanvas.width = canvasWidth;
        pointsCanvas.height = canvasHeight;

        // View state
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let isDragging = false;
        let lastX = 0;
        let lastY = 0;

        // Visibility state
        let showHeatmap = true;
        let showPoints = true;
        let showLabels = true;

        // Cardinal assignment state
        let selectedZoneIndex = null;
        let selectedCardinal = null;
        let cardinalAssignments = {{}};

        // Poblar lista de hotspots
        const hotspotsListDiv = document.getElementById('hotspotsList');
        hotspots.forEach((hotspot, i) => {{
            const div = document.createElement('div');
            div.className = 'hotspot';
            div.dataset.zoneIndex = i;
            div.innerHTML = `
                <div class="hotspot-rank ${{i < 3 ? 'top-3' : ''}}">${{i + 1}}</div>
                <div class="hotspot-info">
                    <div class="hotspot-coords">(${{Math.round(hotspot.coordinates[0])}}, ${{Math.round(hotspot.coordinates[1])}})</div>
                    <div class="hotspot-count">${{hotspot.count}} accesos</div>
                </div>
                <div class="cardinal-badge-container"></div>
            `;

            // Add click event to select zone
            div.addEventListener('click', () => {{
                // Remove previous selection
                document.querySelectorAll('.hotspot').forEach(h => h.classList.remove('selected'));

                // Select this zone
                div.classList.add('selected');
                selectedZoneIndex = i;

                // Update info text
                updateAssignmentInfo();
            }});

            hotspotsListDiv.appendChild(div);
        }});

        // Poblar lista de aforos
        const aforosListDiv = document.getElementById('aforosList');
        aforos.forEach(aforo => {{
            const div = document.createElement('div');
            div.className = 'aforo-item';
            div.style.borderLeftColor = aforo.color_tema;
            div.innerHTML = `
                <div class="aforo-name">${{aforo.nombre}}</div>
                <div class="aforo-stat">Trayectorias: ${{aforo.num_trayectorias}}</div>
            `;
            aforosListDiv.appendChild(div);
        }});

        // Dibujar heatmap
        function drawHeatmap() {{
            heatmapCtx.clearRect(0, 0, canvasWidth, canvasHeight);

            if (!showHeatmap) return;

            const maxDensity = Math.max(...Object.values(densityGrid));

            Object.entries(densityGrid).forEach(([key, count]) => {{
                const [gridX, gridY] = key.split(',').map(Number);
                const x = gridX * gridSize;
                const y = gridY * gridSize;

                const intensity = count / maxDensity;
                const alpha = 0.2 + (intensity * 0.7);

                // Gradient de color basado en intensidad
                let r, g, b;
                if (intensity < 0.33) {{
                    // Azul a amarillo
                    r = Math.round(52 + (243 - 52) * (intensity / 0.33));
                    g = Math.round(152 + (156 - 152) * (intensity / 0.33));
                    b = Math.round(219 - 219 * (intensity / 0.33));
                }} else if (intensity < 0.66) {{
                    // Amarillo a naranja
                    const t = (intensity - 0.33) / 0.33;
                    r = 243;
                    g = Math.round(156 - (156 - 156) * t);
                    b = Math.round(18 * (1 - t));
                }} else {{
                    // Naranja a rojo
                    const t = (intensity - 0.66) / 0.34;
                    r = Math.round(243 + (231 - 243) * t);
                    g = Math.round(156 - (156 - 76) * t);
                    b = Math.round(18 + (60 - 18) * t);
                }}

                heatmapCtx.fillStyle = `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
                heatmapCtx.fillRect(x, y, gridSize, gridSize);

                // Borde para zonas muy intensas
                if (intensity > 0.8) {{
                    heatmapCtx.strokeStyle = `rgba(231, 76, 60, ${{alpha}})`;
                    heatmapCtx.lineWidth = 2;
                    heatmapCtx.strokeRect(x, y, gridSize, gridSize);
                }}
            }});
        }}

        // Dibujar puntos
        function drawPoints() {{
            pointsCtx.clearRect(0, 0, canvasWidth, canvasHeight);

            if (showPoints) {{
                accessPoints.forEach(point => {{
                    pointsCtx.fillStyle = 'rgba(52, 152, 219, 0.6)';
                    pointsCtx.beginPath();
                    pointsCtx.arc(point.x, point.y, 4, 0, Math.PI * 2);
                    pointsCtx.fill();
                }});
            }}

            if (showLabels) {{
                hotspots.slice(0, 15).forEach((hotspot, i) => {{
                    const x = hotspot.coordinates[0];
                    const y = hotspot.coordinates[1];

                    // Dibujar círculo grande de fondo
                    pointsCtx.fillStyle = i < 3 ? '#e74c3c' : (i < 8 ? '#f39c12' : '#3498db');
                    pointsCtx.beginPath();
                    pointsCtx.arc(x, y, 35, 0, Math.PI * 2);
                    pointsCtx.fill();

                    // Borde blanco
                    pointsCtx.strokeStyle = '#fff';
                    pointsCtx.lineWidth = 3;
                    pointsCtx.stroke();

                    // Dibujar número grande
                    pointsCtx.font = 'bold 28px Arial';
                    pointsCtx.textAlign = 'center';
                    pointsCtx.textBaseline = 'middle';
                    pointsCtx.fillStyle = '#fff';
                    pointsCtx.fillText(`${{i + 1}}`, x, y);

                    // Dibujar recuadro con información
                    const infoText = `(${{Math.round(hotspot.coordinates[0])}}, ${{Math.round(hotspot.coordinates[1])}})`;
                    const countText = `${{hotspot.count}} accesos`;

                    pointsCtx.font = 'bold 16px Arial';
                    const infoWidth = Math.max(pointsCtx.measureText(infoText).width, pointsCtx.measureText(countText).width);
                    const boxWidth = infoWidth + 20;
                    const boxHeight = 50;
                    const boxX = x - boxWidth / 2;
                    const boxY = y + 50;

                    // Fondo del recuadro
                    pointsCtx.fillStyle = 'rgba(0, 0, 0, 0.85)';
                    pointsCtx.fillRect(boxX, boxY, boxWidth, boxHeight);

                    // Borde del recuadro
                    pointsCtx.strokeStyle = i < 3 ? '#e74c3c' : (i < 8 ? '#f39c12' : '#3498db');
                    pointsCtx.lineWidth = 2;
                    pointsCtx.strokeRect(boxX, boxY, boxWidth, boxHeight);

                    // Texto de coordenadas
                    pointsCtx.fillStyle = '#fff';
                    pointsCtx.textAlign = 'center';
                    pointsCtx.font = 'bold 14px Arial';
                    pointsCtx.fillText(infoText, x, boxY + 15);

                    // Texto de conteo
                    pointsCtx.fillStyle = i < 3 ? '#e74c3c' : (i < 8 ? '#f39c12' : '#3498db');
                    pointsCtx.font = 'bold 16px Arial';
                    pointsCtx.fillText(countText, x, boxY + 35);
                }});
            }}
        }}

        function updateTransform() {{
            heatmapCanvas.style.transform = `translate(${{offsetX}}px, ${{offsetY}}px) scale(${{scale}})`;
            pointsCanvas.style.transform = `translate(${{offsetX}}px, ${{offsetY}}px) scale(${{scale}})`;
        }}

        function render() {{
            drawHeatmap();
            drawPoints();
            updateTransform();
        }}

        // Event listeners
        document.getElementById('toggleHeatmap').addEventListener('click', (e) => {{
            showHeatmap = !showHeatmap;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('togglePoints').addEventListener('click', (e) => {{
            showPoints = !showPoints;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('toggleLabels').addEventListener('click', (e) => {{
            showLabels = !showLabels;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('zoomIn').addEventListener('click', () => {{
            scale = Math.min(scale * 1.2, 5);
            updateTransform();
        }});

        document.getElementById('zoomOut').addEventListener('click', () => {{
            scale = Math.max(scale / 1.2, 0.1);
            updateTransform();
        }});

        document.getElementById('resetZoom').addEventListener('click', () => {{
            scale = 1;
            offsetX = 0;
            offsetY = 0;
            updateTransform();
        }});

        pointsCanvas.addEventListener('mousedown', (e) => {{
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
        }});

        window.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                offsetX += dx;
                offsetY += dy;
                lastX = e.clientX;
                lastY = e.clientY;
                updateTransform();
            }}
        }});

        window.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        container.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale = Math.max(0.1, Math.min(5, scale * delta));
            updateTransform();
        }});

        // Cardinal buttons functionality
        const cardinalButtons = document.querySelectorAll('.cardinal-btn');
        cardinalButtons.forEach(btn => {{
            btn.addEventListener('click', () => {{
                const cardinal = btn.dataset.cardinal;

                // If no zone selected, alert
                if (selectedZoneIndex === null) {{
                    alert('Por favor selecciona una zona primero');
                    return;
                }}

                // Remove previous cardinal button selection
                cardinalButtons.forEach(b => b.classList.remove('selected'));

                // Select this cardinal
                btn.classList.add('selected');
                selectedCardinal = cardinal;

                // Assign cardinal to zone
                assignCardinalToZone(selectedZoneIndex, cardinal);

                // Update display
                updateZoneBadges();
                updateAssignmentInfo();
            }});
        }});

        // Function to assign cardinal to zone
        function assignCardinalToZone(zoneIndex, cardinal) {{
            // Store assignment
            cardinalAssignments[zoneIndex] = {{
                cardinal: cardinal,
                zone: hotspots[zoneIndex],
                timestamp: new Date().toISOString()
            }};

            console.log('Assigned', cardinal.toUpperCase(), 'to Zone', zoneIndex + 1);
        }}

        // Function to update zone badges
        function updateZoneBadges() {{
            const hotspotElements = document.querySelectorAll('.hotspot');
            hotspotElements.forEach((el, i) => {{
                const badgeContainer = el.querySelector('.cardinal-badge-container');
                if (cardinalAssignments[i]) {{
                    const cardinal = cardinalAssignments[i].cardinal;
                    const cardinalEmoji = {{
                        'norte': '⬆️',
                        'sur': '⬇️',
                        'este': '➡️',
                        'oeste': '⬅️'
                    }};
                    badgeContainer.innerHTML = `<span class="cardinal-badge ${{cardinal}}">${{cardinalEmoji[cardinal]}} ${{cardinal.toUpperCase()}}</span>`;
                }} else {{
                    badgeContainer.innerHTML = '';
                }}
            }});
        }}

        // Function to update assignment info
        function updateAssignmentInfo() {{
            const infoDiv = document.getElementById('assignmentInfo');

            if (selectedZoneIndex !== null) {{
                const zone = hotspots[selectedZoneIndex];
                const coords = `(${{Math.round(zone.coordinates[0])}}, ${{Math.round(zone.coordinates[1])}})`;

                if (cardinalAssignments[selectedZoneIndex]) {{
                    const cardinal = cardinalAssignments[selectedZoneIndex].cardinal;
                    infoDiv.innerHTML = `<strong>Zona ${{selectedZoneIndex + 1}}</strong> ${{coords}}<br>Asignado: <span class="cardinal-badge ${{cardinal}}">${{cardinal.toUpperCase()}}</span>`;
                }} else {{
                    infoDiv.innerHTML = `<strong>Zona ${{selectedZoneIndex + 1}}</strong> ${{coords}}<br>Selecciona un punto cardinal`;
                }}
                infoDiv.classList.add('active');
            }} else {{
                infoDiv.innerHTML = 'Selecciona una zona y luego un punto cardinal';
                infoDiv.classList.remove('active');
            }}
        }}

        // Export assignments functionality
        document.getElementById('exportAssignments').addEventListener('click', () => {{
            if (Object.keys(cardinalAssignments).length === 0) {{
                alert('No hay asignaciones para exportar');
                return;
            }}

            // Format data for export
            const exportData = {{}};
            for (const [zoneIndex, assignment] of Object.entries(cardinalAssignments)) {{
                const zone = hotspots[zoneIndex];
                exportData[`zona_${{parseInt(zoneIndex) + 1}}`] = {{
                    numero: parseInt(zoneIndex) + 1,
                    coordenadas: {{
                        x: Math.round(zone.coordinates[0]),
                        y: Math.round(zone.coordinates[1])
                    }},
                    accesos: zone.count,
                    punto_cardinal: assignment.cardinal.toUpperCase(),
                    timestamp: assignment.timestamp
                }};
            }}

            // Create JSON and download
            const jsonStr = JSON.stringify(exportData, null, 2);
            const blob = new Blob([jsonStr], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `asignaciones_cardinales_${{new Date().toISOString().split('T')[0]}}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            console.log('Exported assignments:', exportData);
            alert(`${{Object.keys(cardinalAssignments).length}} asignaciones exportadas`);
        }});

        // Render inicial
        render();
    </script>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"\nOK - Heatmap de zonas de acceso generado: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python create_access_zones_heatmap.py <combined_aforos.json> [--output <heatmap.html>] [--grid-size <num>]")
        print("\nOpciones:")
        print("  --output      Archivo de salida HTML (default: access_zones_heatmap.html)")
        print("  --grid-size   Tamaño de la cuadrícula en píxeles (default: 50)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = "access_zones_heatmap.html"
    grid_size = 50

    if "--output" in sys.argv:
        output_file = sys.argv[sys.argv.index("--output") + 1]

    if "--grid-size" in sys.argv:
        grid_size = int(sys.argv[sys.argv.index("--grid-size") + 1])

    print("="*70)
    print("GENERADOR DE HEATMAP DE ZONAS DE ACCESO")
    print("="*70)

    analyzer = AccessZonesAnalyzer(input_file)
    results = analyzer.analyze(grid_size=grid_size)
    analyzer.generate_html(results, output_file)

    print("\n" + "="*70)
    print("HEATMAP GENERADO EXITOSAMENTE")
    print("="*70)


if __name__ == "__main__":
    main()
