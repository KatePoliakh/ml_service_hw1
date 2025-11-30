from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from enum import Enum

class BaseModelNoNS(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=()
    )

class ModelClass(str, Enum):
    LOGREG = "logreg"
    RANDOM_FOREST = "random_forest"
    SVM = "svm"
    XGBOOST = "xgboost"


class TrainRequest(BaseModelNoNS):
    dataset: str = Field(..., description="Name of the dataset to use for training")
    model_class: ModelClass = Field(..., description="Type of model to train")
    hyperparams: Optional[Dict[str, Any]] = Field(default={}, description="Hyperparameters for the model")
    model_name: Optional[str] = Field(default=None, description="Custom name for the trained model")
    experiment_name: Optional[str] = Field(default=None, description="ClearML experiment name")


class PredictRequest(BaseModelNoNS):
    features: List[List[float]] = Field(..., description="List of feature vectors for prediction")
    model_id: str = Field(..., description="ID of the model to use for prediction")


class ModelInfo(BaseModelNoNS):
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Model name")
    model_class: str = Field(..., description="Type of model")
    status: str = Field(..., description="Training status")
    created_at: str = Field(..., description="Creation timestamp")
    dataset: str = Field(..., description="Dataset used for training")
    val_score: Optional[float] = Field(default=None, description="Validation score")
    clearml_id: Optional[str] = Field(default=None, description="ClearML task ID")
    artifact_path: Optional[str] = Field(default=None, description="Path to model artifact")


class DatasetInfo(BaseModelNoNS):
    name: str = Field(..., description="Dataset name")
    size: int = Field(..., description="Dataset size in bytes")
    created_at: str = Field(..., description="Creation timestamp")
    dvc_tracked: bool = Field(..., description="Whether dataset is tracked by DVC")
