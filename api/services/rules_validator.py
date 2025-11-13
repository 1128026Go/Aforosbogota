"""
Validador de reglas y trayectorias
Detecta trayectorias inválidas, incompletas o inconsistentes
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class RulesValidator:
    """Validador de trayectorias según reglas configuradas"""

    def __init__(self):
        self.validation_stats = defaultdict(int)

    def validate_trajectory(
        self,
        trajectory: Dict,
        config: Dict,
        rilsa_map: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Valida una trayectoria individual según reglas configuradas

        Args:
            trajectory: Trayectoria a validar
            config: Configuración del dataset
            rilsa_map: Mapa RILSA (opcional)

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        warnings = []

        # 1. Validar campos requeridos
        if not self._has_required_fields(trajectory):
            errors.append("Faltan campos requeridos (track_id, class, points)")
            return (False, errors)

        # 2. Validar filtros de trayectoria
        filter_errors = self._validate_trajectory_filters(trajectory, config)
        errors.extend(filter_errors)

        # 3. Validar consistencia con cardinales
        cardinal_errors = self._validate_cardinal_consistency(trajectory, config)
        errors.extend(cardinal_errors)

        # 4. Validar movimiento RILSA
        if rilsa_map:
            rilsa_errors = self._validate_rilsa_movement(trajectory, rilsa_map)
            errors.extend(rilsa_errors)

        # 5. Aplicar reglas de corrección personalizadas
        rule_errors = self._apply_correction_rules(trajectory, config)
        errors.extend(rule_errors)

        is_valid = len(errors) == 0

        if not is_valid:
            self.validation_stats["invalid_trajectories"] += 1
        else:
            self.validation_stats["valid_trajectories"] += 1

        return (is_valid, errors)

    def validate_batch(
        self,
        trajectories: List[Dict],
        config: Dict,
        rilsa_map: Optional[Dict] = None
    ) -> Dict:
        """
        Valida un lote de trayectorias

        Args:
            trajectories: Lista de trayectorias
            config: Configuración del dataset
            rilsa_map: Mapa RILSA (opcional)

        Returns:
            {
                "valid": [...],
                "invalid": [...],
                "statistics": {
                    "total": 100,
                    "valid": 85,
                    "invalid": 15,
                    "errors_by_type": {...}
                }
            }
        """
        valid_trajectories = []
        invalid_trajectories = []
        errors_by_type = defaultdict(int)

        for traj in trajectories:
            is_valid, errors = self.validate_trajectory(traj, config, rilsa_map)

            if is_valid:
                valid_trajectories.append(traj)
            else:
                traj["validation_errors"] = errors
                invalid_trajectories.append(traj)

                # Contar errores por tipo
                for error in errors:
                    error_type = error.split(":")[0] if ":" in error else error
                    errors_by_type[error_type] += 1

        stats = {
            "total": len(trajectories),
            "valid": len(valid_trajectories),
            "invalid": len(invalid_trajectories),
            "errors_by_type": dict(errors_by_type)
        }

        logger.info(
            f"Validación completada: {stats['valid']}/{stats['total']} válidas "
            f"({stats['invalid']} inválidas)"
        )

        return {
            "valid": valid_trajectories,
            "invalid": invalid_trajectories,
            "statistics": stats
        }

    def _has_required_fields(self, trajectory: Dict) -> bool:
        """Verifica que la trayectoria tenga campos requeridos"""
        required = ["track_id"]
        return all(field in trajectory for field in required)

    def _validate_trajectory_filters(
        self,
        trajectory: Dict,
        config: Dict
    ) -> List[str]:
        """Valida trayectoria según filtros configurados"""
        errors = []
        filters = config.get("trajectory_filters", {})

        # Duración
        duration = trajectory.get("duration", trajectory.get("t_exit", 0) - trajectory.get("t_entry", 0))
        min_duration = filters.get("min_duration_seconds", 2.0)
        max_duration = filters.get("max_duration_seconds", 300.0)

        if duration < min_duration:
            errors.append(f"Duración muy corta: {duration:.2f}s < {min_duration}s")
        if duration > max_duration:
            errors.append(f"Duración muy larga: {duration:.2f}s > {max_duration}s")

        # Distancia
        distance = trajectory.get("distance", trajectory.get("total_distance", 0))
        min_distance = filters.get("min_distance_meters", 5.0)
        max_distance = filters.get("max_distance_meters", 500.0)

        if distance < min_distance:
            errors.append(f"Distancia muy corta: {distance:.2f}m < {min_distance}m")
        if distance > max_distance:
            errors.append(f"Distancia muy larga: {distance:.2f}m > {max_distance}m")

        # Velocidad
        speed = trajectory.get("avg_speed", trajectory.get("velocidad_promedio", 0))
        if speed > 0:
            min_speed = filters.get("min_speed_kmh", 1.0)
            max_speed = filters.get("max_speed_kmh", 120.0)

            if speed < min_speed:
                errors.append(f"Velocidad muy baja: {speed:.2f} km/h < {min_speed} km/h")
            if speed > max_speed:
                errors.append(f"Velocidad muy alta: {speed:.2f} km/h > {max_speed} km/h")

        # Puntos mínimos
        points = trajectory.get("points", [])
        if len(points) < 2:
            errors.append(f"Pocos puntos: {len(points)} < 2")

        return errors

    def _validate_cardinal_consistency(
        self,
        trajectory: Dict,
        config: Dict
    ) -> List[str]:
        """Valida consistencia con configuración de cardinales"""
        errors = []
        cardinal_config = config.get("cardinal_config", {})
        accesses = cardinal_config.get("accesses", {})

        origin = trajectory.get("cardinal_origin", trajectory.get("origin_cardinal", ""))
        dest = trajectory.get("cardinal_destination", trajectory.get("dest_cardinal", ""))

        # Verificar que origen y destino existan en configuración
        if origin and origin not in accesses:
            errors.append(f"Origen cardinal '{origin}' no configurado")
        if dest and dest not in accesses:
            errors.append(f"Destino cardinal '{dest}' no configurado")

        # Verificar permisos de entrada/salida
        if origin in accesses:
            origin_cfg = accesses[origin]
            if not origin_cfg.get("allows_exit", True):
                errors.append(f"Acceso {origin} no permite salida")

        if dest in accesses:
            dest_cfg = accesses[dest]
            if not dest_cfg.get("allows_entry", True):
                errors.append(f"Acceso {dest} no permite entrada")

        return errors

    def _validate_rilsa_movement(
        self,
        trajectory: Dict,
        rilsa_map: Dict
    ) -> List[str]:
        """Valida que el movimiento RILSA sea válido"""
        errors = []

        rilsa_code = trajectory.get("movimiento_rilsa", trajectory.get("rilsa_code", 0))
        origin = trajectory.get("cardinal_origin", trajectory.get("origin_cardinal", ""))
        dest = trajectory.get("cardinal_destination", trajectory.get("dest_cardinal", ""))

        if not rilsa_code:
            errors.append("Código RILSA no asignado")
            return errors

        # Verificar que el movimiento existe en el mapa
        movement_key = f"{origin}-{dest}"
        if movement_key not in rilsa_map:
            errors.append(f"Movimiento {movement_key} no existe en mapa RILSA")

        # Verificar que el código coincida
        if movement_key in rilsa_map:
            expected_code = rilsa_map[movement_key].get("code") if isinstance(rilsa_map[movement_key], dict) else rilsa_map[movement_key]
            if rilsa_code != expected_code:
                errors.append(
                    f"Código RILSA inconsistente: {rilsa_code} != {expected_code} "
                    f"para movimiento {movement_key}"
                )

        return errors

    def _apply_correction_rules(
        self,
        trajectory: Dict,
        config: Dict
    ) -> List[str]:
        """Aplica reglas de corrección personalizadas"""
        errors = []
        rules = config.get("correction_rules", [])

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            rule_id = rule.get("rule_id", "")
            conditions = rule.get("conditions", {})
            action = rule.get("action", "warn")

            # Aplicar regla según tipo
            if rule_id == "remove_pedestrians_without_trajectory":
                if self._matches_rule(trajectory, conditions):
                    errors.append(f"Regla {rule_id}: {rule.get('description', '')}")

            elif rule_id == "restrict_west_entry_only":
                if self._matches_rule(trajectory, conditions):
                    errors.append(f"Regla {rule_id}: {rule.get('description', '')}")

        return errors

    def _matches_rule(self, trajectory: Dict, conditions: Dict) -> bool:
        """Verifica si una trayectoria coincide con las condiciones de una regla"""
        for field, expected_value in conditions.items():
            actual_value = trajectory.get(field)

            if field == "min_points":
                points = trajectory.get("points", [])
                if len(points) < expected_value:
                    return True
            elif actual_value != expected_value:
                return False

        return True

    def detect_incomplete_trajectories(
        self,
        trajectories: List[Dict]
    ) -> List[Dict]:
        """
        Detecta trayectorias incompletas (sin origen/destino, sin puntos suficientes, etc.)

        Returns:
            Lista de trayectorias incompletas
        """
        incomplete = []

        for traj in trajectories:
            issues = []

            # Sin puntos suficientes
            points = traj.get("points", [])
            if len(points) < 3:
                issues.append("pocos_puntos")

            # Sin origen o destino
            origin = traj.get("cardinal_origin", traj.get("origin_cardinal", ""))
            dest = traj.get("cardinal_destination", traj.get("dest_cardinal", ""))

            if not origin:
                issues.append("sin_origen")
            if not dest:
                issues.append("sin_destino")

            # Sin código RILSA
            rilsa_code = traj.get("movimiento_rilsa", traj.get("rilsa_code", 0))
            if not rilsa_code:
                issues.append("sin_codigo_rilsa")

            if issues:
                traj["incomplete_reasons"] = issues
                incomplete.append(traj)

        logger.info(f"Detectadas {len(incomplete)} trayectorias incompletas")

        return incomplete

    def get_validation_summary(self) -> Dict:
        """Obtiene resumen de estadísticas de validación"""
        return dict(self.validation_stats)



