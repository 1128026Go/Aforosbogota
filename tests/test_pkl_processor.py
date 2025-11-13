"""
Tests unitarios para PKLProcessor
"""

import pytest
from core.pkl_processor import PKLProcessor
from utils.validators import DataValidator
from utils.pkl_handler import PKLHandler


class TestPKLProcessor:
    """Tests para PKLProcessor"""

    def test_processor_initialization(self):
        """Test de inicialización del procesador"""
        processor = PKLProcessor()
        assert processor is not None
        assert processor.pkl_handler is not None
        assert processor.validator is not None

    def test_processor_stats(self):
        """Test de estadísticas del procesador"""
        processor = PKLProcessor()
        stats = processor.get_stats()
        assert isinstance(stats, dict)
        assert 'processed_files' in stats
        assert stats['processed_files'] == 0


class TestDataValidator:
    """Tests para DataValidator"""

    def test_validate_valid_vehicle(self, sample_vehicle_data):
        """Test de validación de vehículo válido"""
        is_valid, errors = DataValidator.validate_vehicle_data(sample_vehicle_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_vehicle(self):
        """Test de validación de vehículo inválido"""
        invalid_vehicle = {'id': 'test'}  # Falta location
        is_valid, errors = DataValidator.validate_vehicle_data(invalid_vehicle)
        assert is_valid is False
        assert len(errors) > 0

    def test_detect_anomalies(self, sample_vehicle_data):
        """Test de detección de anomalías"""
        anomalies = DataValidator.detect_anomalies(sample_vehicle_data)
        assert isinstance(anomalies, list)
        # Velocidad normal, no debe haber anomalías
        assert len(anomalies) == 0

    def test_detect_high_velocity_anomaly(self):
        """Test de detección de velocidad anormal"""
        vehicle_with_high_velocity = {
            'id': 'test',
            'location': {'x': 0, 'y': 0, 'z': 0},
            'velocity': 100  # Velocidad muy alta (> 55 m/s)
        }
        anomalies = DataValidator.detect_anomalies(vehicle_with_high_velocity)
        assert len(anomalies) > 0
        assert 'velocity' in anomalies[0].lower()


class TestPKLHandler:
    """Tests para PKLHandler"""

    def test_validate_structure_valid(self, sample_pkl_data):
        """Test de validación de estructura PKL válida"""
        handler = PKLHandler()
        is_valid = handler.validate_structure(sample_pkl_data)
        assert is_valid is True

    def test_validate_structure_invalid(self):
        """Test de validación de estructura PKL inválida"""
        handler = PKLHandler()
        invalid_data = {'frame': 123}  # Falta timestamp y datos
        is_valid = handler.validate_structure(invalid_data)
        assert is_valid is False

    def test_extract_metadata(self, sample_pkl_data):
        """Test de extracción de metadatos"""
        handler = PKLHandler()
        metadata = handler.extract_metadata(sample_pkl_data)
        assert metadata['frame'] == sample_pkl_data['frame']
        assert metadata['timestamp'] == sample_pkl_data['timestamp']
        assert metadata['num_vehicles'] == 1
        assert metadata['num_pedestrians'] == 0


# --- Fin de tests/test_pkl_processor.py ---
