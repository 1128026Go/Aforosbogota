"""
Interventoría de Trayectorias
Verifica la integridad y calidad de cada trayectoria procesada
"""

from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np


class TrajectoryAuditor:
    """
    Audita trayectorias para asegurar integridad:
    - El track_id existe en todas las posiciones
    - La trayectoria es continua (sin gaps grandes)
    - Los frames son secuenciales
    - La entrada y salida son consistentes
    """

    def __init__(self, max_frame_gap: int = 15):
        """
        Args:
            max_frame_gap: Máximo gap permitido entre frames consecutivos
        """
        self.max_frame_gap = max_frame_gap
        self.audit_reports = []

    def audit_track(
        self,
        track: Dict,
        segment: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Audita una trayectoria completa

        Args:
            track: Diccionario con trayectoria completa
            segment: Segmento específico si se generó un evento

        Returns:
            (is_valid, issues) - True si pasa auditoría, lista de problemas encontrados
        """
        issues = []
        track_id = track.get('track_id', 'unknown')
        positions = track.get('positions', [])
        frames = track.get('frames', [])

        # 1. VERIFICAR DATOS BÁSICOS
        if not track_id:
            issues.append("Track sin ID")

        if len(positions) == 0:
            issues.append("Track sin posiciones")
            return False, issues

        if len(frames) == 0:
            issues.append("Track sin frames")
            return False, issues

        if len(positions) != len(frames):
            issues.append(f"Desbalance: {len(positions)} posiciones vs {len(frames)} frames")

        # 2. VERIFICAR CONTINUIDAD DE FRAMES
        frame_gaps = self._check_frame_continuity(frames)
        if frame_gaps:
            issues.append(f"Gaps en frames: {len(frame_gaps)} saltos > {self.max_frame_gap} frames")
            issues.append(f"  Gaps detectados: {frame_gaps[:3]}{'...' if len(frame_gaps) > 3 else ''}")

        # 3. VERIFICAR CONTINUIDAD ESPACIAL
        spatial_jumps = self._check_spatial_continuity(positions)
        if spatial_jumps:
            issues.append(f"Saltos espaciales: {len(spatial_jumps)} saltos > 200px")
            issues.append(f"  Saltos: {spatial_jumps[:3]}{'...' if len(spatial_jumps) > 3 else ''}")

        # 4. VERIFICAR COBERTURA DE LA TRAYECTORIA
        coverage_issues = self._check_trajectory_coverage(positions, frames)
        if coverage_issues:
            issues.extend(coverage_issues)

        # 5. SI HAY SEGMENTO, VERIFICAR COHERENCIA CON EVENTO
        if segment:
            segment_issues = self._audit_segment(track, segment)
            if segment_issues:
                issues.extend(segment_issues)

        # Crear reporte
        is_valid = len(issues) == 0

        audit_report = {
            'track_id': track_id,
            'is_valid': is_valid,
            'issues': issues,
            'stats': {
                'total_positions': len(positions),
                'total_frames': len(frames),
                'frame_range': (min(frames), max(frames)) if frames else (0, 0),
                'has_segment': segment is not None
            }
        }
        self.audit_reports.append(audit_report)

        return is_valid, issues

    def _check_frame_continuity(self, frames: List[int]) -> List[Tuple[int, int, int]]:
        """
        Verifica que los frames sean continuos (sin gaps grandes)

        Returns:
            Lista de gaps: [(frame_start, frame_end, gap_size), ...]
        """
        gaps = []

        for i in range(1, len(frames)):
            gap = frames[i] - frames[i-1]
            if gap > self.max_frame_gap:
                gaps.append((frames[i-1], frames[i], gap))

        return gaps

    def _check_spatial_continuity(
        self,
        positions: List[Tuple[float, float]]
    ) -> List[Tuple[int, float]]:
        """
        Verifica que no haya saltos espaciales grandes

        Returns:
            Lista de saltos: [(index, distance), ...]
        """
        jumps = []
        threshold = 200.0  # píxeles

        for i in range(1, len(positions)):
            pos_prev = positions[i-1]
            pos_curr = positions[i]

            if isinstance(pos_prev, (list, tuple)) and isinstance(pos_curr, (list, tuple)):
                x1, y1 = float(pos_prev[0]), float(pos_prev[1])
                x2, y2 = float(pos_curr[0]), float(pos_curr[1])

                dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                if dist > threshold:
                    jumps.append((i, round(dist, 2)))

        return jumps

    def _check_trajectory_coverage(
        self,
        positions: List[Tuple[float, float]],
        frames: List[int]
    ) -> List[str]:
        """
        Verifica que la trayectoria tenga buena cobertura temporal

        Returns:
            Lista de problemas de cobertura
        """
        issues = []

        if not frames:
            return issues

        frame_start = min(frames)
        frame_end = max(frames)
        total_frames_span = frame_end - frame_start + 1
        actual_frames = len(frames)

        coverage_ratio = actual_frames / total_frames_span if total_frames_span > 0 else 0

        # Si la cobertura es muy baja (<50%), hay gaps grandes
        if coverage_ratio < 0.5:
            issues.append(
                f"Cobertura baja: {coverage_ratio*100:.1f}% "
                f"({actual_frames}/{total_frames_span} frames)"
            )

        return issues

    def _audit_segment(self, track: Dict, segment: Dict) -> List[str]:
        """
        Audita que el segmento sea consistente con la trayectoria

        Returns:
            Lista de problemas encontrados
        """
        issues = []

        track_id = track.get('track_id')
        frames = track.get('frames', [])
        positions = track.get('positions', [])

        entry_frame = segment.get('entry_frame')
        exit_frame = segment.get('exit_frame')
        entry_access = segment.get('entry_access_id')
        exit_access = segment.get('exit_access_id')

        # Verificar que entry_frame y exit_frame están en la trayectoria
        if entry_frame not in frames:
            issues.append(f"Frame de entrada {entry_frame} no existe en trayectoria")

        if exit_frame not in frames:
            issues.append(f"Frame de salida {exit_frame} no existe en trayectoria")

        # Verificar orden temporal
        if entry_frame >= exit_frame:
            issues.append(
                f"Orden temporal inválido: entrada={entry_frame} >= salida={exit_frame}"
            )

        # Verificar que accesos son válidos
        if not entry_access:
            issues.append("Acceso de entrada no definido")

        if not exit_access:
            issues.append("Acceso de salida no definido")

        # Verificar que el segmento cubre suficiente trayectoria
        if frames:
            entry_idx = frames.index(entry_frame) if entry_frame in frames else 0
            exit_idx = frames.index(exit_frame) if exit_frame in frames else len(frames) - 1

            segment_length = exit_idx - entry_idx + 1
            total_length = len(frames)

            coverage = segment_length / total_length if total_length > 0 else 0

            if coverage < 0.3:
                issues.append(
                    f"Segmento cubre solo {coverage*100:.1f}% de la trayectoria "
                    f"({segment_length}/{total_length} frames)"
                )

        return issues

    def audit_all_tracks(
        self,
        tracks: List[Dict],
        segments_map: Dict[str, Dict] = None
    ) -> Dict:
        """
        Audita todas las trayectorias

        Args:
            tracks: Lista de trayectorias
            segments_map: Mapa de track_id -> segment (si existe)

        Returns:
            Reporte completo de auditoría
        """
        self.audit_reports = []

        for track in tracks:
            track_id = track.get('track_id')
            segment = segments_map.get(track_id) if segments_map else None
            self.audit_track(track, segment)

        # Generar resumen
        total_tracks = len(self.audit_reports)
        valid_tracks = sum(1 for r in self.audit_reports if r['is_valid'])
        invalid_tracks = total_tracks - valid_tracks

        # Agrupar issues por tipo
        issue_types = {}
        for report in self.audit_reports:
            for issue in report['issues']:
                # Extraer tipo de issue (primera parte antes de ':')
                issue_type = issue.split(':')[0].strip()
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        summary = {
            'total_tracks': total_tracks,
            'valid_tracks': valid_tracks,
            'invalid_tracks': invalid_tracks,
            'validity_rate': valid_tracks / total_tracks if total_tracks > 0 else 0,
            'issue_types': issue_types,
            'detailed_reports': self.audit_reports
        }

        return summary

    def generate_report_text(self, summary: Dict, max_details: int = 10) -> str:
        """
        Genera reporte de auditoría en texto

        Args:
            summary: Resumen de auditoría
            max_details: Máximo de tracks con problemas a mostrar

        Returns:
            Reporte en texto
        """
        lines = []
        lines.append("=" * 60)
        lines.append("INTERVENTORÍA DE TRAYECTORIAS")
        lines.append("=" * 60)

        lines.append(f"\nTotal trayectorias auditadas: {summary['total_tracks']}")
        lines.append(f"  ✓ Válidas: {summary['valid_tracks']} ({summary['validity_rate']*100:.1f}%)")
        lines.append(f"  ✗ Con problemas: {summary['invalid_tracks']}")

        if summary['issue_types']:
            lines.append("\nTipos de problemas encontrados:")
            for issue_type, count in sorted(summary['issue_types'].items(), key=lambda x: -x[1]):
                lines.append(f"  • {issue_type}: {count}")

        # Mostrar tracks con problemas
        invalid_reports = [r for r in summary['detailed_reports'] if not r['is_valid']]
        if invalid_reports:
            lines.append(f"\nTracks con problemas (mostrando {min(max_details, len(invalid_reports))} de {len(invalid_reports)}):")

            for report in invalid_reports[:max_details]:
                lines.append(f"\n  Track ID: {report['track_id']}")
                lines.append(f"    Stats: {report['stats']['total_positions']} posiciones, "
                           f"frames {report['stats']['frame_range'][0]}-{report['stats']['frame_range'][1]}")
                lines.append(f"    Problemas:")
                for issue in report['issues']:
                    lines.append(f"      - {issue}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def export_failed_tracks(self, output_path: Path) -> int:
        """
        Exporta lista de tracks que fallaron auditoría

        Args:
            output_path: Ruta para guardar reporte JSON

        Returns:
            Número de tracks exportados
        """
        import json

        failed_tracks = [r for r in self.audit_reports if not r['is_valid']]

        export_data = {
            'total_failed': len(failed_tracks),
            'failed_tracks': failed_tracks
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return len(failed_tracks)
