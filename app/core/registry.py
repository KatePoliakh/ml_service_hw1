import json
import os
from datetime import datetime
from app.logger import logger

REGISTRY_PATH = "data/models_registry.json"

def _ensure_registry():
    """Ensure registry file exists"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "w") as f:
            json.dump({}, f)

def _load_registry():
    """Load registry data"""
    _ensure_registry()
    try:
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        return {}

def _save_registry(data):
    """Save registry data"""
    try:
        with open(REGISTRY_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")
        raise

def create_entry(name, model_class, hyperparams, dataset):
    """Create new model entry in registry"""
    registry = _load_registry()
    
    entry = {
        "id": name, 
        "name": name,
        "model_class": model_class,
        "hyperparams": hyperparams,
        "dataset": dataset,
        "status": "training",
        "created_at": datetime.now().isoformat(),
        "artifact_path": None,
        "val_score": None,
        "metrics": {}
    }
    
    registry[name] = entry
    _save_registry(registry)
    logger.info(f"Created model registry entry: {name}")
    return entry

def update_entry(model_id, **kwargs):
    """Update model entry in registry"""
    registry = _load_registry()
    if model_id not in registry:
        logger.warning(f"Model not found in registry: {model_id}")
        return
    
    registry[model_id].update(kwargs)
    _save_registry(registry)
    logger.info(f"Updated model {model_id}")

def list_entries():
    """List all model entries"""
    registry = _load_registry()
    return list(registry.values())

def get_entry(model_id):
    """Get specific model entry"""
    registry = _load_registry()
    return registry.get(model_id)