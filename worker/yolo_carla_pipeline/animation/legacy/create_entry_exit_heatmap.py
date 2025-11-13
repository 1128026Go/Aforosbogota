"""
Generador de Heatmap de Entradas y Salidas.

Crea visualización HTML interactiva mostrando las zonas calientes
de entrada y salida de vehículos.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """Generador de visualización de heatmap."""

    def __init__(self, combined_data_path: str, analysis_path: str):
        """Inicializa el generador."""
        logger.info("Cargando datos...")

        with open(combined_data_path, 'r', encoding='utf-8') as f:
            self.combined_data = json.load(f)

        with open(analysis_path, 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)

        self.aforos = self.combined_data['aforos']
        logger.info(f"  - Datos cargados correctamente")

    def generate_html(self, output_path: str):
        """Genera dashboard HTML con heatmap."""
        html_content = self._create_html_template()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"OK - Heatmap generado: {output_path}")

    def _create_html_template(self) -> str:
        """Crea el template HTML."""
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Entradas y Salidas - Bogotá Traffic</title>
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
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 3px solid;
        }}

        .stat-item.entry {{
            border-left-color: #2ecc71;
        }}

        .stat-item.exit {{
            border-left-color: #e74c3c;
        }}

        .stat-title {{
            font-size: 13px;
            color: #aaa;
            margin-bottom: 4px;
        }}

        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #fff;
        }}

        .hotspot {{
            background: #2a2a2a;
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 4px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .hotspot-rank {{
            background: #3498db;
            color: #fff;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }}

        .hotspot-info {{
            flex: 1;
            margin-left: 10px;
        }}

        .hotspot-count {{
            color: #3498db;
            font-weight: bold;
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

        .legend {{
            margin-top: 15px;
            padding: 15px;
            background: #252525;
            border-radius: 5px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 13px;
        }}

        .legend-color {{
            width: 30px;
            height: 15px;
            margin-right: 10px;
            border-radius: 3px;
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
            background: rgba(26, 26, 26, 0.9);
            border: 1px solid #333;
            color: #fff;
            width: 40px;
            height: 40px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.3s;
        }}

        .zoom-btn:hover {{
            background: rgba(52, 152, 219, 0.9);
        }}

        .aforo-label {{
            font-size: 12px;
            color: #aaa;
            margin-bottom: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="section">
                <h3>📊 Resumen General</h3>
                <div class="stat-item entry">
                    <div class="stat-title">Total Entradas</div>
                    <div class="stat-value" id="totalEntries">-</div>
                </div>
                <div class="stat-item exit">
                    <div class="stat-title">Total Salidas</div>
                    <div class="stat-value" id="totalExits">-</div>
                </div>
            </div>

            <div class="section">
                <h3>🎮 Controles de Visualización</h3>
                <button class="toggle-btn active" id="toggleEntries">Mostrar Entradas</button>
                <button class="toggle-btn active" id="toggleExits">Mostrar Salidas</button>
                <button class="toggle-btn active" id="toggleHeatmap">Mostrar Heatmap</button>
                <button class="toggle-btn" id="toggleLabels">Mostrar Etiquetas</button>
            </div>

            <div class="section">
                <h3>🔥 Top 10 Zonas de Entrada</h3>
                <div id="entryHotspots"></div>
            </div>

            <div class="section">
                <h3>🚪 Top 10 Zonas de Salida</h3>
                <div id="exitHotspots"></div>
            </div>

            <div class="section">
                <h3>🗺️ Aforos</h3>
                <div id="aforosList"></div>
            </div>

            <div class="legend">
                <h3 style="margin-bottom: 10px; font-size: 14px;">Leyenda</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background: rgba(46, 204, 113, 0.7);"></div>
                    <span>Puntos de Entrada</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: rgba(231, 76, 60, 0.7);"></div>
                    <span>Puntos de Salida</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: linear-gradient(90deg, rgba(46,204,113,0.3), rgba(46,204,113,0.9));"></div>
                    <span>Heatmap (Densidad)</span>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <h1>🗺️ Análisis de Zonas de Entrada y Salida - Sistema Multi-Aforo</h1>
            </div>
            <div class="canvas-container" id="canvasContainer">
                <canvas id="heatmapCanvas"></canvas>
                <canvas id="pointsCanvas"></canvas>
                <div class="zoom-controls">
                    <button class="zoom-btn" id="zoomIn">+</button>
                    <button class="zoom-btn" id="zoomOut">−</button>
                    <button class="zoom-btn" id="resetZoom">⟲</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Datos
        const analysisData = {json.dumps(self.analysis, ensure_ascii=False)};
        const aforosData = {json.dumps(self.aforos, ensure_ascii=False)};
        const trajectories = {json.dumps(self.combined_data['trajectories'], ensure_ascii=False)};

        // Canvas setup
        const container = document.getElementById('canvasContainer');
        const heatmapCanvas = document.getElementById('heatmapCanvas');
        const pointsCanvas = document.getElementById('pointsCanvas');
        const heatmapCtx = heatmapCanvas.getContext('2d');
        const pointsCtx = pointsCanvas.getContext('2d');

        // Canvas dimensions
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
        let showEntries = true;
        let showExits = true;
        let showHeatmap = true;
        let showLabels = false;

        // Extraer puntos de entrada y salida
        const entryPoints = [];
        const exitPoints = [];

        trajectories.forEach(traj => {{
            if (traj.positions && traj.positions.length > 0) {{
                entryPoints.push({{
                    x: traj.positions[0][0],
                    y: traj.positions[0][1],
                    aforo_id: traj.aforo_id,
                    clase: traj.clase
                }});
                exitPoints.push({{
                    x: traj.positions[traj.positions.length - 1][0],
                    y: traj.positions[traj.positions.length - 1][1],
                    aforo_id: traj.aforo_id,
                    clase: traj.clase
                }});
            }}
        }});

        // Actualizar estadísticas
        document.getElementById('totalEntries').textContent = entryPoints.length.toLocaleString();
        document.getElementById('totalExits').textContent = exitPoints.length.toLocaleString();

        // Poblar hotspots de entrada
        const entryHotspotsDiv = document.getElementById('entryHotspots');
        analysisData.entry_hotspots.slice(0, 10).forEach((hotspot, i) => {{
            const div = document.createElement('div');
            div.className = 'hotspot';
            div.innerHTML = `
                <div class="hotspot-rank">${{i + 1}}</div>
                <div class="hotspot-info">
                    <div>Zona (${{Math.round(hotspot.coordinates[0])}}, ${{Math.round(hotspot.coordinates[1])}})</div>
                    <div class="hotspot-count">${{hotspot.count}} entradas</div>
                </div>
            `;
            entryHotspotsDiv.appendChild(div);
        }});

        // Poblar hotspots de salida
        const exitHotspotsDiv = document.getElementById('exitHotspots');
        analysisData.exit_hotspots.slice(0, 10).forEach((hotspot, i) => {{
            const div = document.createElement('div');
            div.className = 'hotspot';
            div.innerHTML = `
                <div class="hotspot-rank">${{i + 1}}</div>
                <div class="hotspot-info">
                    <div>Zona (${{Math.round(hotspot.coordinates[0])}}, ${{Math.round(hotspot.coordinates[1])}})</div>
                    <div class="hotspot-count">${{hotspot.count}} salidas</div>
                </div>
            `;
            exitHotspotsDiv.appendChild(div);
        }});

        // Poblar lista de aforos
        const aforosListDiv = document.getElementById('aforosList');
        aforosData.forEach(aforo => {{
            const div = document.createElement('div');
            div.className = 'stat-item';
            div.style.borderLeftColor = aforo.color_tema;
            div.innerHTML = `
                <div class="aforo-label">${{aforo.nombre}}</div>
                <div style="font-size: 12px; color: #aaa;">Trayectorias: ${{aforo.num_trayectorias}}</div>
            `;
            aforosListDiv.appendChild(div);
        }});

        // Función para dibujar heatmap
        function drawHeatmap() {{
            heatmapCtx.clearRect(0, 0, canvasWidth, canvasHeight);

            if (!showHeatmap) return;

            const gridSize = analysisData.grid_size;

            // Crear densidad grid combinada
            const densityGrid = {{}};

            if (showEntries) {{
                entryPoints.forEach(point => {{
                    const gridX = Math.floor(point.x / gridSize);
                    const gridY = Math.floor(point.y / gridSize);
                    const key = `${{gridX}},${{gridY}}`;
                    densityGrid[key] = (densityGrid[key] || 0) + 1;
                }});
            }}

            if (showExits) {{
                exitPoints.forEach(point => {{
                    const gridX = Math.floor(point.x / gridSize);
                    const gridY = Math.floor(point.y / gridSize);
                    const key = `${{gridX}},${{gridY}}`;
                    densityGrid[key] = (densityGrid[key] || 0) + 1;
                }});
            }}

            // Encontrar max para normalizar
            const maxDensity = Math.max(...Object.values(densityGrid));

            // Dibujar cuadrados de calor
            Object.entries(densityGrid).forEach(([key, count]) => {{
                const [gridX, gridY] = key.split(',').map(Number);
                const x = gridX * gridSize;
                const y = gridY * gridSize;

                const intensity = count / maxDensity;
                const alpha = 0.3 + (intensity * 0.6);

                heatmapCtx.fillStyle = `rgba(255, 193, 7, ${{alpha}})`;
                heatmapCtx.fillRect(x, y, gridSize, gridSize);

                // Borde más intenso para zonas muy densas
                if (intensity > 0.7) {{
                    heatmapCtx.strokeStyle = `rgba(255, 152, 0, ${{alpha}})`;
                    heatmapCtx.lineWidth = 2;
                    heatmapCtx.strokeRect(x, y, gridSize, gridSize);
                }}
            }});
        }}

        // Función para dibujar puntos
        function drawPoints() {{
            pointsCtx.clearRect(0, 0, canvasWidth, canvasHeight);

            const pointSize = 5;

            // Dibujar puntos de entrada
            if (showEntries) {{
                entryPoints.forEach(point => {{
                    pointsCtx.fillStyle = 'rgba(46, 204, 113, 0.7)';
                    pointsCtx.beginPath();
                    pointsCtx.arc(point.x, point.y, pointSize, 0, Math.PI * 2);
                    pointsCtx.fill();
                }});
            }}

            // Dibujar puntos de salida
            if (showExits) {{
                exitPoints.forEach(point => {{
                    pointsCtx.fillStyle = 'rgba(231, 76, 60, 0.7)';
                    pointsCtx.beginPath();
                    pointsCtx.arc(point.x, point.y, pointSize, 0, Math.PI * 2);
                    pointsCtx.fill();
                }});
            }}

            // Dibujar etiquetas de hotspots si está activado
            if (showLabels) {{
                pointsCtx.font = '12px Arial';
                pointsCtx.textAlign = 'center';

                if (showEntries) {{
                    analysisData.entry_hotspots.slice(0, 5).forEach((hotspot, i) => {{
                        pointsCtx.fillStyle = '#2ecc71';
                        pointsCtx.fillText(
                            `E${{i + 1}}: ${{hotspot.count}}`,
                            hotspot.coordinates[0],
                            hotspot.coordinates[1] - 10
                        );
                    }});
                }}

                if (showExits) {{
                    analysisData.exit_hotspots.slice(0, 5).forEach((hotspot, i) => {{
                        pointsCtx.fillStyle = '#e74c3c';
                        pointsCtx.fillText(
                            `S${{i + 1}}: ${{hotspot.count}}`,
                            hotspot.coordinates[0],
                            hotspot.coordinates[1] + 20
                        );
                    }});
                }}
            }}
        }}

        // Función para actualizar transformación
        function updateTransform() {{
            heatmapCanvas.style.transform = `translate(${{offsetX}}px, ${{offsetY}}px) scale(${{scale}})`;
            pointsCanvas.style.transform = `translate(${{offsetX}}px, ${{offsetY}}px) scale(${{scale}})`;
        }}

        // Función de render completa
        function render() {{
            drawHeatmap();
            drawPoints();
            updateTransform();
        }}

        // Event listeners para controles
        document.getElementById('toggleEntries').addEventListener('click', (e) => {{
            showEntries = !showEntries;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('toggleExits').addEventListener('click', (e) => {{
            showExits = !showExits;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('toggleHeatmap').addEventListener('click', (e) => {{
            showHeatmap = !showHeatmap;
            e.target.classList.toggle('active');
            render();
        }});

        document.getElementById('toggleLabels').addEventListener('click', (e) => {{
            showLabels = !showLabels;
            e.target.classList.toggle('active');
            render();
        }});

        // Zoom controls
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

        // Pan controls
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

        // Zoom con rueda del mouse
        container.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale = Math.max(0.1, Math.min(5, scale * delta));
            updateTransform();
        }});

        // Render inicial
        render();
    </script>
</body>
</html>"""

def main():
    if len(sys.argv) < 3:
        print("Uso: python create_entry_exit_heatmap.py <combined_aforos.json> <entry_exit_analysis.json> [--output <heatmap.html>]")
        print("\nOpciones:")
        print("  --output      Archivo de salida HTML (default: entry_exit_heatmap.html)")
        sys.exit(1)

    combined_file = sys.argv[1]
    analysis_file = sys.argv[2]
    output_file = "entry_exit_heatmap.html"

    if "--output" in sys.argv:
        output_file = sys.argv[sys.argv.index("--output") + 1]

    print("="*70)
    print("GENERADOR DE HEATMAP DE ENTRADAS Y SALIDAS")
    print("="*70)

    generator = HeatmapGenerator(combined_file, analysis_file)
    generator.generate_html(output_file)

    print("\n" + "="*70)
    print("HEATMAP GENERADO EXITOSAMENTE")
    print("="*70)
    print(f"\nAbrir: {output_file}")


if __name__ == "__main__":
    main()
