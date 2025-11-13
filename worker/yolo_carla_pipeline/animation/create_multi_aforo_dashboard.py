"""
Dashboard Multi-Aforo - Sistema Integrado de Tráfico.

Visualiza múltiples aforos en el mismo lienzo con:
- Soporte para datos combinados de múltiples intersecciones
- Identificación visual de cada aforo
- Filtros por aforo y categoría
- Vista unificada en tiempo real
"""

import json
from pathlib import Path
from typing import Dict

# Colores y emojis
COLOR_MAP = {
    'car': '#3498db', 'truck': '#e74c3c', 'bus': '#9b59b6',
    'motorcycle': '#f39c12', 'bicycle': '#2ecc71', 'person': '#1abc9c', 'unknown': '#95a5a6'
}

EMOJI_MAP = {
    'car': '🚗', 'truck': '🚚', 'bus': '🚌',
    'motorcycle': '🏍️', 'bicycle': '🚴', 'person': '🚶', 'unknown': '⚫'
}


class MultiAforoDashboard:
    """Generador de dashboard multi-aforo."""

    def generate_html(self, combined_data: Dict, output_path: str):
        """Genera dashboard HTML para múltiples aforos."""
        print(f"\nGenerando dashboard multi-aforo...")

        trajectories = combined_data['trajectories']
        aforos_info = combined_data.get('aforos', [])
        all_classes = sorted(set(t['clase'] for t in trajectories))

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Multi-Aforo - Sistema de Tráfico Integrado</title>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            background: #1a1a1a;
        }}

        #canvas-container {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            overflow: hidden;
        }}

        #backgroundCanvas, #trajectoryCanvas {{ position: absolute; top: 0; left: 0; }}
        #trajectoryCanvas {{ cursor: grab; z-index: 2; }}
        #trajectoryCanvas:active {{ cursor: grabbing; }}

        .dashboard-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.5);
            z-index: 1000;
            max-width: 380px;
            max-height: 90vh;
            overflow-y: auto;
            backdrop-filter: blur(10px);
        }}

        .panel-title {{
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}

        .control-section {{
            margin-bottom: 20px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}

        .control-label {{
            font-size: 14px;
            font-weight: 600;
            color: #34495e;
            margin-bottom: 10px;
            display: block;
        }}

        .button-group {{ display: flex; gap: 10px; margin-bottom: 10px; }}

        button {{
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
            flex: 1;
        }}

        button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .btn-play {{ background: #27ae60; color: white; }}
        .btn-pause {{ background: #e67e22; color: white; }}
        .btn-reset {{ background: #95a5a6; color: white; }}

        .slider-container {{ margin-bottom: 15px; }}

        input[type="range"] {{
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #d3d3d3;
            outline: none;
            margin-top: 5px;
        }}

        input[type="range"]::-webkit-slider-thumb {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #3498db;
            cursor: pointer;
        }}

        .checkbox-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 200px;
            overflow-y: auto;
            padding: 8px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            background: white;
        }}

        .checkbox-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px;
            border-radius: 4px;
            transition: background 0.2s;
        }}

        .checkbox-item:hover {{ background: #e9ecef; }}

        .checkbox-item input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}

        .checkbox-item label {{
            cursor: pointer;
            font-size: 13px;
            color: #2c3e50;
            flex: 1;
        }}

        .emoji-icon {{ font-size: 22px; }}

        .aforo-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            margin-left: auto;
        }}

        .stats-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(255,255,255,0.95);
            padding: 18px 22px;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.3);
            z-index: 1000;
            font-size: 13px;
            backdrop-filter: blur(10px);
        }}

        .stats-item {{
            margin: 6px 0;
            color: #2c3e50;
        }}

        .stats-item strong {{ color: #3498db; }}

        .progress-bar {{
            width: 100%;
            height: 24px;
            background: #ecf0f1;
            border-radius: 12px;
            overflow: hidden;
            margin-top: 10px;
            border: 2px solid #bdc3c7;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.05s linear;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }}

        .zoom-controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .zoom-btn {{
            width: 48px;
            height: 48px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s;
        }}

        .zoom-btn:hover {{
            background: white;
            transform: scale(1.1);
        }}

        .zoom-btn:active {{ transform: scale(0.95); }}

        .aforos-legend {{
            position: absolute;
            top: 20px;
            right: 90px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.3);
            z-index: 1000;
            backdrop-filter: blur(10px);
            max-width: 250px;
        }}

        .legend-title {{
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 6px 0;
            font-size: 12px;
        }}

        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}

        /* Panel de Aforo en Vivo */
        .aforo-live-panel {{
            position: absolute;
            top: 20px;
            right: 350px;
            background: rgba(255, 255, 255, 0.97);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.5);
            z-index: 1001;
            max-width: 900px;
            max-height: 85vh;
            overflow-y: auto;
            backdrop-filter: blur(10px);
            border: 2px solid #3498db;
        }}

        .aforo-live-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 3px solid #3498db;
        }}

        .aforo-live-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        }}

        .aforo-live-meta {{
            font-size: 11px;
            color: #7f8c8d;
            margin-top: 4px;
        }}

        .aforo-controls {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .aforo-controls button,
        .aforo-controls select {{
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .aforo-controls button {{
            background: #3498db;
            color: white;
        }}

        .aforo-controls button:hover {{
            background: #2980b9;
            transform: translateY(-1px);
        }}

        .aforo-controls button.danger {{
            background: #e74c3c;
        }}

        .aforo-controls button.danger:hover {{
            background: #c0392b;
        }}

        .aforo-controls select {{
            background: white;
            border: 2px solid #bdc3c7;
            color: #2c3e50;
            font-weight: normal;
        }}

        .aforo-table-container {{
            margin-top: 15px;
            overflow-x: auto;
        }}

        .aforo-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 6px;
            overflow: hidden;
        }}

        .aforo-table th,
        .aforo-table td {{
            padding: 10px 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}

        .aforo-table th {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .aforo-table th.mov-header {{
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
        }}

        .aforo-table tbody tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .aforo-table tbody tr:hover {{
            background: #e3f2fd;
        }}

        .aforo-table .total-row {{
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%) !important;
            font-weight: bold;
            color: white;
        }}

        .aforo-table .total-col {{
            background: #fff3cd;
            font-weight: bold;
        }}

        .aforo-count {{
            font-weight: 600;
            color: #2c3e50;
        }}

        .aforo-count.zero {{
            color: #bdc3c7;
        }}

        .aforo-count.nonzero {{
            color: #e74c3c;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div id="canvas-container">
        <canvas id="backgroundCanvas"></canvas>
        <canvas id="trajectoryCanvas"></canvas>
    </div>

    <!-- Panel de Aforo en Vivo -->
    <div class="aforo-live-panel">
        <div class="aforo-live-header">
            <div>
                <div class="aforo-live-title">📊 Aforo en Vivo - 15 min</div>
                <div class="aforo-live-meta">
                    Bucket: <span id="currentBucket">--</span> |
                    Total: <span id="liveTotal">0</span> trayectorias
                </div>
            </div>
            <div class="aforo-controls">
                <select id="bucketSelector" onchange="changeBucket()">
                    <option value="">Seleccionar bucket...</option>
                </select>
                <button onclick="exportCSV()">💾 CSV</button>
                <button onclick="resetAforoLive()" class="danger">🔄 Reset</button>
            </div>
        </div>
        <div class="aforo-table-container">
            <table class="aforo-table">
                <thead>
                    <tr>
                        <th class="mov-header">Mov</th>
                        <th>🚗 Car</th>
                        <th>🚚 Truck</th>
                        <th>🚌 Bus</th>
                        <th>🏍️ Moto</th>
                        <th>🚴 Bici</th>
                        <th>🚶 Pers</th>
                        <th class="total-col">Total</th>
                    </tr>
                </thead>
                <tbody id="aforoTableBody">
                    <!-- Se genera dinámicamente -->
                </tbody>
            </table>
        </div>

        <!-- Tabla de Peatones -->
        <div class="aforo-table-container" style="margin-top: 20px;">
            <div style="font-weight: bold; margin-bottom: 10px; color: #4fc3f7;">🚶 MOVIMIENTOS PEATONALES</div>
            <table class="aforo-table">
                <thead>
                    <tr>
                        <th class="mov-header">Mov</th>
                        <th>🚶 Peatón</th>
                        <th class="total-col">Total</th>
                    </tr>
                </thead>
                <tbody id="aforoPedestrianTableBody">
                    <!-- Se genera dinámicamente -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Panel de Control -->
    <div class="dashboard-panel">
        <div class="panel-title">🗺️ Sistema Multi-Aforo</div>

        <!-- Controles de Reproducción -->
        <div class="control-section">
            <div class="control-label">⏯️ Reproducción</div>
            <div class="button-group">
                <button class="btn-play" onclick="playAnimation()">▶ Play</button>
                <button class="btn-pause" onclick="pauseAnimation()">⏸ Pause</button>
                <button class="btn-reset" onclick="resetAnimation()">↺ Reset</button>
            </div>

            <div class="slider-container">
                <div class="control-label">⚡ Velocidad: <span id="speedValue">1x</span></div>
                <input type="range" id="speedSlider" min="0.25" max="5" step="0.25" value="1" oninput="updateSpeed(this.value)">
            </div>

            <div class="progress-bar">
                <div class="progress-fill" id="progressBar">0%</div>
            </div>
        </div>

        <!-- Filtro por Aforo -->
        <div class="control-section">
            <div class="control-label">📍 Filtrar por Aforo</div>
            <div class="checkbox-group" id="aforoFilters">
                <!-- Se genera dinámicamente -->
            </div>
        </div>

        <!-- Filtro por Categoría -->
        <div class="control-section">
            <div class="control-label">🎯 Filtrar por Categoría</div>
            <div class="checkbox-group" id="categoryFilters">
                <!-- Se genera dinámicamente -->
            </div>
        </div>

        <!-- Filtro por Movimiento RILSA -->
        <div class="control-section">
            <div class="control-label">🚶 Filtrar por Movimiento</div>
            <div class="checkbox-group" id="movementFilters">
                <!-- Se genera dinámicamente -->
            </div>
        </div>

        <!-- Opciones -->
        <div class="control-section">
            <div class="control-label">⚙️ Opciones</div>
            <div class="checkbox-item">
                <input type="checkbox" id="showTrails" checked onchange="redrawBackground()">
                <label for="showTrails">Mostrar trayectorias</label>
            </div>
            <div class="checkbox-item">
                <input type="checkbox" id="showLabels" onchange="needsRender = true">
                <label for="showLabels">Mostrar IDs</label>
            </div>
            <div class="checkbox-item">
                <input type="checkbox" id="showGrid" onchange="redrawBackground()">
                <label for="showGrid">Mostrar cuadrícula</label>
            </div>
            <div class="checkbox-item">
                <input type="checkbox" id="showAforoLabels" checked onchange="redrawBackground()">
                <label for="showAforoLabels">Mostrar nombres de aforos</label>
            </div>
        </div>
    </div>

    <!-- Leyenda de Aforos -->
    <div class="aforos-legend">
        <div class="legend-title">📊 Aforos Activos</div>
        <div id="aforosLegendContent">
            <!-- Se genera dinámicamente -->
        </div>
    </div>

    <!-- Panel de Estadísticas -->
    <div class="stats-panel">
        <div class="stats-item"><strong>Frame:</strong> <span id="currentFrame">0</span> / <span id="totalFrames">0</span></div>
        <div class="stats-item"><strong>Tiempo:</strong> <span id="currentTime">00:00:00</span></div>
        <div class="stats-item"><strong>Activos:</strong> <span id="activeVehicles">0</span></div>
        <div class="stats-item"><strong>Total Trayectorias:</strong> <span id="totalTrajectories">{len(trajectories)}</span></div>
        <div class="stats-item"><strong>Aforos:</strong> <span id="totalAforos">{len(aforos_info)}</span></div>
        <div class="stats-item"><strong>Zoom:</strong> <span id="zoomLevel">100%</span></div>
    </div>

    <!-- Controles de Zoom -->
    <div class="zoom-controls">
        <div class="zoom-btn" onclick="zoomIn()">+</div>
        <div class="zoom-btn" onclick="zoomOut()">−</div>
        <div class="zoom-btn" onclick="resetZoom()" style="font-size: 20px;">⟲</div>
    </div>

    <script>
        const trajectories = {json.dumps(trajectories)};
        const aforosInfo = {json.dumps(aforos_info)};

        const bgCanvas = document.getElementById('backgroundCanvas');
        const bgCtx = bgCanvas.getContext('2d');
        const canvas = document.getElementById('trajectoryCanvas');
        const ctx = canvas.getContext('2d');

        let currentFrame = 0, minFrame = Infinity, maxFrame = -Infinity;
        let isPlaying = false, animationSpeed = 1, needsRender = true;
        let activeCategories = new Set(), activeAforos = new Set(), activeMovements = new Set();
        let scale = 1, translateX = 0, translateY = 0;
        let isDragging = false, lastX = 0, lastY = 0;
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        const FPS = 30.0;  // Frames por segundo del video

        // Precalcular bounds
        trajectories.forEach(traj => {{
            traj.frames.forEach(f => {{
                minFrame = Math.min(minFrame, f);
                maxFrame = Math.max(maxFrame, f);
            }});
            traj.positions.forEach(pos => {{
                minX = Math.min(minX, pos[0]);
                maxX = Math.max(maxX, pos[0]);
                minY = Math.min(minY, pos[1]);
                maxY = Math.max(maxY, pos[1]);
            }});
        }});

        currentFrame = minFrame;

        function setupCanvas() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;

            bgCanvas.width = canvas.width = width;
            bgCanvas.height = canvas.height = height;

            const padding = 100;
            const dataWidth = maxX - minX;
            const dataHeight = maxY - minY;

            const scaleX = (width - padding * 2) / dataWidth;
            const scaleY = (height - padding * 2) / dataHeight;
            scale = Math.min(scaleX, scaleY);

            translateX = (width - dataWidth * scale) / 2 - minX * scale;
            translateY = (height - dataHeight * scale) / 2 - minY * scale;

            updateZoomDisplay();
            redrawBackground();
        }}

        function init() {{
            setupCanvas();

            // Inicializar filtros de aforos
            aforosInfo.forEach(aforo => activeAforos.add(aforo.id));
            const aforoFilterContainer = document.getElementById('aforoFilters');
            const legendContainer = document.getElementById('aforosLegendContent');

            aforosInfo.forEach(aforo => {{
                aforoFilterContainer.innerHTML += `
                    <div class="checkbox-item">
                        <input type="checkbox" id="aforo_${{aforo.id}}" checked onchange="toggleAforo('${{aforo.id}}')">
                        <label for="aforo_${{aforo.id}}">${{aforo.nombre}}</label>
                        <span class="aforo-badge" style="background: ${{aforo.color_tema}}">${{aforo.num_trayectorias}}</span>
                    </div>
                `;

                legendContainer.innerHTML += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${{aforo.color_tema}}"></div>
                        <span>${{aforo.nombre}}</span>
                    </div>
                `;
            }});

            // Inicializar filtros de categorías
            const categories = [...new Set(trajectories.map(t => t.clase))];
            categories.forEach(cat => activeCategories.add(cat));

            const categoryFilterContainer = document.getElementById('categoryFilters');
            categories.forEach(cat => {{
                const emoji = trajectories.find(t => t.clase === cat).emoji;
                categoryFilterContainer.innerHTML += `
                    <div class="checkbox-item">
                        <input type="checkbox" id="cat_${{cat}}" checked onchange="toggleCategory('${{cat}}')">
                        <span class="emoji-icon">${{emoji}}</span>
                        <label for="cat_${{cat}}">${{cat}}</label>
                    </div>
                `;
            }});

            // Inicializar filtros de movimientos RILSA
            const movements = [...new Set(trajectories.map(t => t.movimiento_rilsa || '?'))].sort();
            movements.forEach(mov => activeMovements.add(mov));

            const movementFilterContainer = document.getElementById('movementFilters');
            movements.forEach(mov => {{
                const isPedestrian = mov.startsWith('P(');
                const emoji = isPedestrian ? '🚶' : '🚗';
                movementFilterContainer.innerHTML += `
                    <div class="checkbox-item">
                        <input type="checkbox" id="mov_${{mov}}" checked onchange="toggleMovement('${{mov}}')">
                        <span class="emoji-icon">${{emoji}}</span>
                        <label for="mov_${{mov}}">${{mov}}</label>
                    </div>
                `;
            }});

            document.getElementById('totalFrames').textContent = maxFrame - minFrame;

            canvas.addEventListener('mousedown', e => {{ isDragging = true; lastX = e.clientX; lastY = e.clientY; }});
            canvas.addEventListener('mousemove', e => {{
                if (!isDragging) return;
                translateX += e.clientX - lastX;
                translateY += e.clientY - lastY;
                lastX = e.clientX;
                lastY = e.clientY;
                redrawBackground();
            }});
            canvas.addEventListener('mouseup', () => isDragging = false);
            canvas.addEventListener('mouseleave', () => isDragging = false);
            canvas.addEventListener('wheel', e => {{
                e.preventDefault();
                const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                const mouseX = e.clientX;
                const mouseY = e.clientY;
                translateX = mouseX - (mouseX - translateX) * zoomFactor;
                translateY = mouseY - (mouseY - translateY) * zoomFactor;
                scale *= zoomFactor;
                updateZoomDisplay();
                redrawBackground();
            }}, {{ passive: false }});

            window.addEventListener('resize', () => {{ setupCanvas(); needsRender = true; }});

            requestAnimationFrame(renderLoop);
        }}

        function transformX(x) {{ return x * scale + translateX; }}
        function transformY(y) {{ return y * scale + translateY; }}

        function redrawBackground() {{
            bgCtx.fillStyle = '#1a1a1a';
            bgCtx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);
            bgCtx.save();

            // Grilla
            if (document.getElementById('showGrid')?.checked) {{
                const gridSize = 100 * scale;
                bgCtx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
                bgCtx.lineWidth = 1;
                for (let x = 0; x < bgCanvas.width; x += gridSize) {{
                    bgCtx.beginPath();
                    bgCtx.moveTo(x, 0);
                    bgCtx.lineTo(x, bgCanvas.height);
                    bgCtx.stroke();
                }}
                for (let y = 0; y < bgCanvas.height; y += gridSize) {{
                    bgCtx.beginPath();
                    bgCtx.moveTo(0, y);
                    bgCtx.lineTo(bgCanvas.width, y);
                    bgCtx.stroke();
                }}
            }}

            // Etiquetas de aforos
            if (document.getElementById('showAforoLabels')?.checked) {{
                aforosInfo.forEach(aforo => {{
                    const x = transformX(aforo.offset_x);
                    const y = transformY(aforo.offset_y);

                    bgCtx.font = 'bold 16px Arial';
                    bgCtx.fillStyle = aforo.color_tema;
                    bgCtx.shadowColor = 'rgba(0,0,0,0.8)';
                    bgCtx.shadowBlur = 4;
                    bgCtx.fillText(aforo.nombre, x, y - 10);
                    bgCtx.shadowBlur = 0;
                }});
            }}

            // Trayectorias
            if (document.getElementById('showTrails')?.checked) {{
                trajectories.forEach(traj => {{
                    if (!activeCategories.has(traj.clase) || !activeAforos.has(traj.aforo_id)) return;
                    if (!activeMovements.has(traj.movimiento_rilsa || '?')) return;
                    bgCtx.strokeStyle = traj.color;
                    bgCtx.lineWidth = Math.max(1, 2 * scale);
                    bgCtx.globalAlpha = 0.3;
                    bgCtx.beginPath();
                    traj.positions.forEach((pos, idx) => {{
                        const x = transformX(pos[0]);
                        const y = transformY(pos[1]);
                        if (idx === 0) bgCtx.moveTo(x, y);
                        else bgCtx.lineTo(x, y);
                    }});
                    bgCtx.stroke();
                }});
                bgCtx.globalAlpha = 1;
            }}

            bgCtx.restore();
            needsRender = true;
        }}

        function renderLoop() {{
            if (isPlaying) {{
                currentFrame += Math.max(1, Math.floor(10 * animationSpeed));
                if (currentFrame > maxFrame) currentFrame = minFrame;
                needsRender = true;
            }}
            if (needsRender) {{
                renderFrame();
                needsRender = false;
            }}
            requestAnimationFrame(renderLoop);
        }}

        function renderFrame() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const showLabels = document.getElementById('showLabels')?.checked || false;
            let activeCount = 0;

            trajectories.forEach(traj => {{
                if (!activeCategories.has(traj.clase) || !activeAforos.has(traj.aforo_id)) return;
                if (!activeMovements.has(traj.movimiento_rilsa || '?')) return;

                const frameIndex = traj.frames.findIndex(f => f >= currentFrame);
                if (frameIndex === -1 || frameIndex === 0) return;

                const prevFrameIdx = frameIndex - 1;
                const prevFrame = traj.frames[prevFrameIdx];
                const nextFrame = traj.frames[frameIndex];
                const ratio = Math.min(1, (currentFrame - prevFrame) / (nextFrame - prevFrame));

                const prevPos = traj.positions[prevFrameIdx];
                const nextPos = traj.positions[frameIndex];

                const x = prevPos[0] + (nextPos[0] - prevPos[0]) * ratio;
                const y = prevPos[1] + (nextPos[1] - prevPos[1]) * ratio;

                const canvasX = transformX(x);
                const canvasY = transformY(y);

                const emojiSize = Math.max(24, 30 * scale);
                ctx.font = `${{emojiSize}}px Arial`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                ctx.shadowBlur = 10;
                ctx.shadowOffsetX = 2;
                ctx.shadowOffsetY = 2;

                ctx.fillText(traj.emoji, canvasX, canvasY);

                ctx.shadowBlur = 0;
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 0;

                if (showLabels) {{
                    const fontSize = Math.max(10, 11 * scale);
                    ctx.font = `bold ${{fontSize}}px Arial`;
                    const text = `${{traj.track_id_original}}`;
                    const textWidth = ctx.measureText(text).width;
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
                    ctx.fillRect(canvasX - textWidth/2 - 3, canvasY - emojiSize/2 - fontSize - 5, textWidth + 6, fontSize + 4);
                    ctx.fillStyle = 'white';
                    ctx.fillText(text, canvasX, canvasY - emojiSize/2 - fontSize/2 - 3);
                }}

                activeCount++;
            }});

            document.getElementById('currentFrame').textContent = currentFrame - minFrame;
            document.getElementById('activeVehicles').textContent = activeCount;

            // Calcular y mostrar tiempo (HH:MM:SS)
            const segundosTotales = Math.floor((currentFrame - minFrame) / FPS);
            const horas = Math.floor(segundosTotales / 3600);
            const minutos = Math.floor((segundosTotales % 3600) / 60);
            const segundos = segundosTotales % 60;
            const tiempoFormateado = `${{horas.toString().padStart(2, '0')}}:${{minutos.toString().padStart(2, '0')}}:${{segundos.toString().padStart(2, '0')}}`;
            document.getElementById('currentTime').textContent = tiempoFormateado;

            const progress = ((currentFrame - minFrame) / (maxFrame - minFrame) * 100).toFixed(1);
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = progress + '%';
            progressBar.textContent = `${{tiempoFormateado}} (${{progress}}%)`;
        }}

        function playAnimation() {{ isPlaying = true; }}
        function pauseAnimation() {{ isPlaying = false; }}
        function resetAnimation() {{ pauseAnimation(); currentFrame = minFrame; needsRender = true; }}
        function updateSpeed(value) {{ animationSpeed = parseFloat(value); document.getElementById('speedValue').textContent = value + 'x'; }}

        function toggleAforo(aforoId) {{
            const checkbox = document.getElementById('aforo_' + aforoId);
            if (checkbox.checked) activeAforos.add(aforoId);
            else activeAforos.delete(aforoId);
            redrawBackground();
        }}

        function toggleCategory(category) {{
            const checkbox = document.getElementById('cat_' + category);
            if (checkbox.checked) activeCategories.add(category);
            else activeCategories.delete(category);
            redrawBackground();
        }}

        function toggleMovement(movement) {{
            const checkbox = document.getElementById('mov_' + movement);
            if (checkbox.checked) activeMovements.add(movement);
            else activeMovements.delete(movement);
            redrawBackground();
        }}

        function zoomIn() {{ scale *= 1.3; updateZoomDisplay(); redrawBackground(); }}
        function zoomOut() {{ scale /= 1.3; updateZoomDisplay(); redrawBackground(); }}
        function resetZoom() {{ setupCanvas(); }}
        function updateZoomDisplay() {{ document.getElementById('zoomLevel').textContent = Math.round(scale * 100) + '%'; }}

        // ======================================
        // SISTEMA DE AFORO EN VIVO
        // ======================================

        const CLASES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'];

        // Mapeo RILSA estándar correcto
        const RILSA_MAP = {{
            // Directos (1-4)
            'N->S': 1,   // Norte → Sur
            'S->N': 2,   // Sur → Norte
            'O->E': 3,   // Oeste → Este
            'E->O': 4,   // Este → Oeste

            // Izquierdas (5-8)
            'N->E': 5,   // Norte → Este
            'S->O': 6,   // Sur → Oeste
            'O->N': 7,   // Oeste → Norte (izquierda)
            'E->S': 8,   // Este → Sur

            // Derechas (91-94)
            'N->O': 91,  // Norte → Oeste (derecha) 9(1)
            'S->E': 92,  // Sur → Este (derecha) 9(2)
            'O->S': 93,  // Oeste → Sur (derecha) 9(3)
            'E->N': 94,  // Este → Norte (derecha) 9(4)

            // U-turns (101-104)
            'N->N': 101, // Retorno en Norte 10(1)
            'S->S': 102, // Retorno en Sur 10(2)
            'O->O': 103, // Retorno en Oeste 10(3)
            'E->E': 104  // Retorno en Este 10(4)
        }};

        let aforoData = {{
            seenTracks: new Set(),
            counts: new Map(),
            totales: new Map(),
            currentBucket: null
        }};

        let completedTracks = new Set();

        function floor15(date) {{
            const d = new Date(date);
            const minutes = d.getMinutes();
            const floored = Math.floor(minutes / 15) * 15;
            d.setMinutes(floored, 0, 0);
            return d;
        }}

        // Descripciones detalladas por código RILSA
        const DESCRIPCIONES_RILSA = {{
            1: 'Norte → Sur (directo)',
            2: 'Sur → Norte (directo)',
            3: 'Oeste → Este (directo)',
            4: 'Este → Oeste (directo)',
            5: 'Norte → Este (izquierda)',
            6: 'Sur → Oeste (izquierda)',
            7: 'Oeste → Norte (izquierda)',
            8: 'Este → Sur (izquierda)',
            91: 'Norte → Oeste (derecha) 9(1)',
            92: 'Sur → Este (derecha) 9(2)',
            93: 'Oeste → Sur (derecha) 9(3)',
            94: 'Este → Norte (derecha) 9(4)',
            101: 'Retorno en Norte 10(1)',
            102: 'Retorno en Sur 10(2)',
            103: 'Retorno en Oeste 10(3)',
            104: 'Retorno en Este 10(4)'
        }};

        function mapRilsa(origen, destino) {{
            if (!origen || !destino) return 0;
            const key = `${{origen}}->${{destino}}`;
            return RILSA_MAP[key] || 0;
        }}

        function getDescripcionRilsa(codigo) {{
            return DESCRIPCIONES_RILSA[codigo] || `Movimiento ${{codigo}}`;
        }}

        function onTrackComplete(track) {{
            // Evitar duplicados
            if (completedTracks.has(track.track_id)) return;
            completedTracks.add(track.track_id);

            // Determinar origen y destino
            const origen = track.origin_cardinal || 'N';
            const destino = track.dest_cardinal || 'S';

            // Detectar si es peatón
            const esPeaton = ['person', 'peaton', 'pedestrian'].includes(track.clase.toLowerCase());

            // Asignar código RILSA
            let mov_rilsa;
            if (esPeaton) {{
                // Peatones: usar código P(x) según origen
                const indicePeaton = {{ 'N': 1, 'S': 2, 'O': 3, 'E': 4 }};
                mov_rilsa = `P(${{indicePeaton[origen] || 1}})`;
            }} else {{
                // Vehículos: usar mapeo tradicional
                mov_rilsa = mapRilsa(origen, destino);
            }}

            // Timestamp de salida
            const exitTime = new Date();
            const bucketDate = floor15(exitTime);
            const bucketKey = bucketDate.toISOString();

            // Clasificar periodo
            const hora = bucketDate.getHours();
            const periodo = hora < 12 ? 'mañana' : 'tarde';

            // Crear clave de bucket
            const bucketObj = {{ bucket_iso: bucketKey, ramal: origen, periodo }};
            const bucketStr = JSON.stringify(bucketObj);

            // Crear clave de conteo
            const countKey = {{ movimiento_rilsa: mov_rilsa, clase: track.clase }};
            const countStr = JSON.stringify(countKey);

            // Inicializar bucket si no existe
            if (!aforoData.counts.has(bucketStr)) {{
                aforoData.counts.set(bucketStr, new Map());
                aforoData.totales.set(bucketStr, 0);
            }}

            const bucketCounts = aforoData.counts.get(bucketStr);
            const prevCount = bucketCounts.get(countStr) || 0;
            bucketCounts.set(countStr, prevCount + 1);
            aforoData.totales.set(bucketStr, aforoData.totales.get(bucketStr) + 1);

            // Actualizar UI
            if (!aforoData.currentBucket) {{
                aforoData.currentBucket = bucketStr;
            }}

            updateAforoPanel();
            updatePedestrianAforoPanel();
            updateBucketSelector();

            console.log(`✅ Track ${{track.track_id}} completado: ${{track.clase}} - Mov ${{mov_rilsa}} (${{origen}}→${{destino}})`);
        }}

        function updateAforoPanel() {{
            if (!aforoData.currentBucket) return;

            const bucketCounts = aforoData.counts.get(aforoData.currentBucket) || new Map();
            const bucketTotal = aforoData.totales.get(aforoData.currentBucket) || 0;
            const bucketObj = JSON.parse(aforoData.currentBucket);

            // Actualizar header
            document.getElementById('currentBucket').textContent =
                new Date(bucketObj.bucket_iso).toLocaleString('es-CO', {{
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit'
                }});
            document.getElementById('liveTotal').textContent = bucketTotal;

            // Generar tabla
            let tableHTML = '';

            for (let mov = 1; mov <= 10; mov++) {{
                let rowHTML = `<tr><td class="mov-header">${{mov}}</td>`;
                let rowTotal = 0;

                CLASES.forEach(clase => {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    const count = bucketCounts.get(countStr) || 0;
                    rowTotal += count;

                    const cssClass = count === 0 ? 'aforo-count zero' : 'aforo-count nonzero';
                    rowHTML += `<td><span class="${{cssClass}}">${{count}}</span></td>`;
                }});

                rowHTML += `<td class="total-col">${{rowTotal}}</td></tr>`;
                tableHTML += rowHTML;
            }}

            // Fila de totales
            let totalRow = '<tr class="total-row"><td>TOTAL</td>';
            let grandTotal = 0;

            CLASES.forEach(clase => {{
                let claseTotal = 0;
                for (let mov = 1; mov <= 10; mov++) {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    claseTotal += bucketCounts.get(countStr) || 0;
                }}
                grandTotal += claseTotal;
                totalRow += `<td>${{claseTotal}}</td>`;
            }});

            totalRow += `<td>${{grandTotal}}</td></tr>`;
            tableHTML += totalRow;

            document.getElementById('aforoTableBody').innerHTML = tableHTML;
        }}

        function updatePedestrianAforoPanel() {{
            if (!aforoData.currentBucket) return;

            const bucketCounts = aforoData.counts.get(aforoData.currentBucket) || new Map();

            // Generar tabla de peatones
            let tableHTML = '';
            const pedestrianMovements = ['P(1)', 'P(2)', 'P(3)', 'P(4)'];
            const pedestrianClasses = ['person', 'peaton', 'pedestrian'];

            pedestrianMovements.forEach(mov => {{
                let rowHTML = `<tr><td class="mov-header">${{mov}}</td>`;
                let rowTotal = 0;

                // Sumar todas las clases peatonales para este movimiento
                pedestrianClasses.forEach(clase => {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    const count = bucketCounts.get(countStr) || 0;
                    rowTotal += count;
                }});

                const cssClass = rowTotal === 0 ? 'aforo-count zero' : 'aforo-count nonzero';
                rowHTML += `<td><span class="${{cssClass}}">${{rowTotal}}</span></td>`;
                rowHTML += `<td class="total-col">${{rowTotal}}</td></tr>`;
                tableHTML += rowHTML;
            }});

            // Fila de totales
            let totalRow = '<tr class="total-row"><td>TOTAL</td>';
            let grandTotal = 0;

            pedestrianMovements.forEach(mov => {{
                pedestrianClasses.forEach(clase => {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    grandTotal += bucketCounts.get(countStr) || 0;
                }});
            }});

            totalRow += `<td>${{grandTotal}}</td><td>${{grandTotal}}</td></tr>`;
            tableHTML += totalRow;

            document.getElementById('aforoPedestrianTableBody').innerHTML = tableHTML;
        }}

        function updateBucketSelector() {{
            const selector = document.getElementById('bucketSelector');
            const buckets = Array.from(aforoData.counts.keys()).sort().reverse();

            selector.innerHTML = '<option value="">Seleccionar bucket...</option>';

            buckets.forEach(bucket => {{
                const bucketObj = JSON.parse(bucket);
                const date = new Date(bucketObj.bucket_iso);
                const label = date.toLocaleString('es-CO', {{
                    month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit'
                }}) + ` (${{aforoData.totales.get(bucket)}})`;

                const option = document.createElement('option');
                option.value = bucket;
                option.textContent = label;
                option.selected = (bucket === aforoData.currentBucket);
                selector.appendChild(option);
            }});
        }}

        function changeBucket() {{
            const selector = document.getElementById('bucketSelector');
            aforoData.currentBucket = selector.value;
            updateAforoPanel();
            updatePedestrianAforoPanel();
        }}

        function exportCSV() {{
            if (!aforoData.currentBucket) {{
                alert('No hay datos para exportar');
                return;
            }}

            const bucketCounts = aforoData.counts.get(aforoData.currentBucket);
            const bucketObj = JSON.parse(aforoData.currentBucket);

            let csv = 'movimiento_rilsa,clase,n\\n';

            // Exportar movimientos vehiculares (1-10)
            for (let mov = 1; mov <= 10; mov++) {{
                CLASES.forEach(clase => {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    const count = bucketCounts.get(countStr) || 0;
                    if (count > 0) {{
                        csv += `${{mov}},${{clase}},${{count}}\\n`;
                    }}
                }});
            }}

            // Exportar movimientos peatonales (P(1-4))
            const pedestrianMovements = ['P(1)', 'P(2)', 'P(3)', 'P(4)'];
            const pedestrianClasses = ['person', 'peaton', 'pedestrian'];

            pedestrianMovements.forEach(mov => {{
                pedestrianClasses.forEach(clase => {{
                    const countKey = {{ movimiento_rilsa: mov, clase }};
                    const countStr = JSON.stringify(countKey);
                    const count = bucketCounts.get(countStr) || 0;
                    if (count > 0) {{
                        csv += `${{mov}},${{clase}},${{count}}\\n`;
                    }}
                }});
            }});

            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            const filename = `aforo_${{bucketObj.bucket_iso.replace(/:/g, '-')}}.csv`;
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();

            console.log(`📥 CSV exportado: ${{filename}}`);
        }}

        function resetAforoLive() {{
            if (!confirm('¿Resetear todos los conteos? Esta acción no se puede deshacer.')) return;

            aforoData = {{
                seenTracks: new Set(),
                counts: new Map(),
                totales: new Map(),
                currentBucket: null
            }};

            completedTracks.clear();

            document.getElementById('currentBucket').textContent = '--';
            document.getElementById('liveTotal').textContent = '0';
            document.getElementById('aforoTableBody').innerHTML = '';
            document.getElementById('aforoPedestrianTableBody').innerHTML = '';
            document.getElementById('bucketSelector').innerHTML = '<option value="">Seleccionar bucket...</option>';

            console.log('🔄 Aforo resetado');
        }}

        // Hook para detectar cuando una trayectoria completa
        function checkTrackCompletion() {{
            trajectories.forEach(traj => {{
                // Si el frame actual supera el último frame de la trayectoria
                if (currentFrame >= traj.frames[traj.frames.length - 1] && !completedTracks.has(traj.track_id_original)) {{
                    onTrackComplete({{
                        track_id: traj.track_id_original,
                        clase: traj.clase,
                        origin_cardinal: traj.origin_cardinal || 'N',
                        dest_cardinal: traj.dest_cardinal || 'S'
                    }});
                }}
            }});
        }}

        // Integrar con el loop de animación
        const originalRenderLoop = renderLoop;
        renderLoop = function() {{
            checkTrackCompletion();
            originalRenderLoop();
        }};

        window.onload = init;
    </script>
</body>
</html>"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"OK - Dashboard multi-aforo guardado en: {output_path}")
        print(f"  Tamaño: {output_file.stat().st_size / (1024 * 1024):.2f} MB")


def main():
    import sys

    if len(sys.argv) < 3:
        print("Uso: python create_multi_aforo_dashboard.py <combined_aforos.json> <output.html>")
        sys.exit(1)

    combined_path = sys.argv[1]
    output_path = sys.argv[2]

    print("="*70)
    print("GENERADOR DE DASHBOARD MULTI-AFORO")
    print("="*70)

    with open(combined_path, 'r', encoding='utf-8') as f:
        combined_data = json.load(f)

    print(f"\nDatos cargados:")
    print(f"  - Trayectorias: {len(combined_data['trajectories'])}")
    print(f"  - Aforos: {len(combined_data.get('aforos', []))}")

    dashboard = MultiAforoDashboard()
    dashboard.generate_html(combined_data, output_path)

    print("\n" + "="*70)
    print("DASHBOARD GENERADO EXITOSAMENTE")
    print(f"Abre: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()
