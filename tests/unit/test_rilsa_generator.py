"""
Tests unitarios para RilsaGenerator
"""

import pytest
from pathlib import Path
from api.services.rilsa_generator import RilsaGenerator


class TestRilsaGenerator:
    """Tests para RilsaGenerator"""

    def test_classify_movement_directo(self):
        """Test clasificación de movimiento directo"""
        result = RilsaGenerator._classify_movement("N", "S")
        assert result == "directo"

    def test_classify_movement_giro_izquierda(self):
        """Test clasificación de giro izquierda"""
        result = RilsaGenerator._classify_movement("N", "E")
        assert result == "giro_izquierda"

    def test_classify_movement_giro_derecha(self):
        """Test clasificación de giro derecha"""
        result = RilsaGenerator._classify_movement("N", "O")
        assert result == "giro_derecha"

    def test_classify_movement_retorno(self):
        """Test clasificación de retorno"""
        result = RilsaGenerator._classify_movement("N", "N")
        assert result == "retorno"

    def test_infer_movements_from_polygons(self):
        """Test inferencia de movimientos desde polígonos"""
        accesses = {
            "N": {
                "allows_entry": True,
                "allows_exit": True
            },
            "S": {
                "allows_entry": True,
                "allows_exit": True
            },
            "E": {
                "allows_entry": True,
                "allows_exit": True
            },
            "O": {
                "allows_entry": True,
                "allows_exit": True
            }
        }

        movements = RilsaGenerator.infer_movements_from_polygons(accesses)

        # Debe haber movimientos directos
        assert "N-S" in movements
        assert movements["N-S"]["code"] == 1
        assert movements["N-S"]["type"] == "directo"

        # Debe haber giros
        assert "N-E" in movements
        assert movements["N-E"]["type"] == "giro_izquierda"

    def test_get_rilsa_code_directo(self):
        """Test obtención de código RILSA para movimiento directo"""
        code = RilsaGenerator._get_rilsa_code(("N", "S"))
        assert code == 1

    def test_get_rilsa_code_izquierda(self):
        """Test obtención de código RILSA para giro izquierda"""
        code = RilsaGenerator._get_rilsa_code(("N", "E"))
        assert code == 5

    def test_get_rilsa_code_derecha(self):
        """Test obtención de código RILSA para giro derecha"""
        code = RilsaGenerator._get_rilsa_code(("N", "O"))
        assert code == 91

    def test_get_movement_description(self):
        """Test descripción de movimiento"""
        desc = RilsaGenerator.get_movement_description("N", "S")
        assert "Directo" in desc or "N" in desc

    def test_validate_rilsa_map_valid(self):
        """Test validación de mapa RILSA válido"""
        rilsa_map = {
            "N->S": 1,
            "S->N": 2,
            "E->O": 3,
            "O->E": 4
        }

        is_valid, errors = RilsaGenerator.validate_rilsa_map(rilsa_map)
        assert is_valid
        assert len(errors) == 0

    def test_validate_rilsa_map_invalid_code(self):
        """Test validación de mapa RILSA con código inválido"""
        rilsa_map = {
            "N->S": 999  # Código inválido
        }

        is_valid, errors = RilsaGenerator.validate_rilsa_map(rilsa_map)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_rilsa_map_duplicate_codes(self):
        """Test validación de mapa RILSA con códigos duplicados"""
        rilsa_map = {
            "N->S": 1,
            "S->N": 1  # Código duplicado
        }

        is_valid, errors = RilsaGenerator.validate_rilsa_map(rilsa_map)
        assert not is_valid
        assert any("duplicados" in error.lower() for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




