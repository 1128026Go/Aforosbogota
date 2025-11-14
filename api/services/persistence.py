"""
Service for persisting and loading dataset configurations
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from api.models.config import DatasetConfig


class ConfigPersistenceService:
    """Service for saving and loading dataset configurations to/from disk"""
    
    DEFAULT_CONFIG_DIR = "data/configs"
    CONFIG_FILENAME = "config.json"
    
    @classmethod
    def ensure_config_dir(cls, dataset_id: str) -> Path:
        """Ensure the config directory exists for a dataset"""
        config_dir = Path(cls.DEFAULT_CONFIG_DIR) / dataset_id
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @classmethod
    def get_config_path(cls, dataset_id: str) -> Path:
        """Get the full path to a dataset's config file"""
        return cls.ensure_config_dir(dataset_id) / cls.CONFIG_FILENAME
    
    @classmethod
    def load_config(cls, dataset_id: str) -> Optional[DatasetConfig]:
        """
        Load a dataset configuration from disk.
        
        Args:
            dataset_id: The dataset identifier
            
        Returns:
            DatasetConfig if found, None otherwise
        """
        config_path = cls.get_config_path(dataset_id)
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return DatasetConfig(**data)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            return None
    
    @classmethod
    def save_config(cls, config: DatasetConfig) -> bool:
        """
        Save a dataset configuration to disk.
        
        Args:
            config: The DatasetConfig to save
            
        Returns:
            True if successful, False otherwise
        """
        config_path = cls.get_config_path(config.dataset_id)
        
        try:
            config.updated_at = datetime.utcnow()
            with open(config_path, 'w', encoding='utf-8') as f:
                # Serialize with datetime as ISO format
                config_dict = json.loads(config.model_dump_json())
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
            return False
    
    @classmethod
    def create_default_config(cls, dataset_id: str) -> DatasetConfig:
        """
        Create a default empty configuration for a dataset.
        
        Args:
            dataset_id: The dataset identifier
            
        Returns:
            A new DatasetConfig with empty accesses and rules
        """
        return DatasetConfig(
            dataset_id=dataset_id,
            accesses=[],
            rilsa_rules=[]
        )
