"""
ML model trainer with ClearML integration
"""
import traceback
from pathlib import Path
from joblib import dump, load
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

from app.core.registry import create_entry, update_entry
from app.core.clearml_client import ClearMLClient
from app.core.metrics import calculate_metrics
from app.logger import logger


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "trained_models"
DATASETS_DIR = PROJECT_ROOT / "datasets"

MODEL_DIR.mkdir(exist_ok=True)
DATASETS_DIR.mkdir(exist_ok=True)


# Available model classes
MODEL_MAP = {
    "logreg": LogisticRegression,
    "random_forest": RandomForestClassifier,
    "svm": SVC,
    "xgboost": XGBClassifier,
}

# Default hyperparameters
DEFAULT_HYPERPARAMS = {
    "logreg": {"C": 1.0, "max_iter": 1000, "random_state": 42},
    "random_forest": {"n_estimators": 100, "max_depth": 5, "random_state": 42},
    "svm": {"C": 1.0, "kernel": "rbf", "probability": True},
    "xgboost": {"n_estimators": 100, "max_depth": 3, "random_state": 42},
}



#DATASET LOADER

def _read_dataset(dataset_name: str):
    """
    Read dataset from /datasets directory, fallback to iris if missing.
    Must contain column 'target'.
    """
    path = DATASETS_DIR / dataset_name

    if not path.exists():
        logger.warning(f"Dataset {dataset_name} not found, loading Iris fallback dataset...")
        from sklearn.datasets import load_iris
        X, y = load_iris(return_X_y=True)
        return X, y

    if path.suffix == ".csv":
        df = pd.read_csv(path)
    elif path.suffix == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError("Unsupported dataset format: only CSV/JSON allowed")

    if "target" not in df.columns:
        raise ValueError("Dataset must contain 'target' column")

    X = df.drop(columns=["target"])
    y = df["target"]

    logger.info(f"Loaded dataset: {X.shape[0]} samples, {X.shape[1]} features")
    return X.values, y.values



# TRAIN METHOD

def train(dataset_name: str, model_class: str, hyperparams: dict = None,
          model_name: str = None, experiment_name: str = None):
    """
    Train ML model with optional ClearML experiment tracking.
    """

    # Create model registry entry
    entry = create_entry(model_name, model_class, hyperparams, dataset_name)
    model_id = entry["id"]

    # Try to initialize ClearML
    clearml = ClearMLClient()
    task = None

    try:
        task = clearml.create_experiment(
            model_id=model_id,
            model_class=model_class,
            dataset_name=dataset_name,
            hyperparams=hyperparams,
            experiment_name=experiment_name,
        )
        update_entry(model_id, clearml_id=task.id)
        logger.info(f"ClearML experiment created: {task.id}")

    except Exception as e:
        logger.warning(f"ClearML initialization failed: {e}")

    try:
        logger.info(f"Starting training: model={model_class}, dataset={dataset_name}")

        # Load data
        X, y = _read_dataset(dataset_name)

        # Train/val split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Select model class
        if model_class not in MODEL_MAP:
            raise ValueError(f"Unknown model class: {model_class}")

        ModelCls = MODEL_MAP[model_class]

        # Merge default + user hyperparams
        final_params = DEFAULT_HYPERPARAMS.get(model_class, {}).copy()
        final_params.update(hyperparams or {})

        logger.info(f"Using hyperparameters: {final_params}")
        clearml.log_hyperparameters(final_params)

        # Train model
        model = ModelCls(**final_params)
        model.fit(X_train, y_train)

        # Predict & evaluate
        y_pred = model.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average="weighted")

        # Generate classification report
        report = classification_report(y_val, y_pred, output_dict=True)

        logger.info(
            f"Training completed: accuracy={accuracy:.4f}, f1_score={f1:.4f}"
        )

        # Save model
        model_path = MODEL_DIR / f"{model_id}.joblib"
        dump(model, model_path)

        # Prepare metrics dict
        metrics = {
            "accuracy": float(accuracy),
            "f1_score": float(f1),
            "val_samples": len(y_val),
        }

        # Safely add per-class metrics
        for class_name, class_metrics in report.items():

            if isinstance(class_metrics, float):
                metrics[class_name] = float(class_metrics)
                continue

            if not (class_name.isdigit() or class_name in ["macro avg", "weighted avg"]):
                continue

            for metric_name, value in class_metrics.items():
                if isinstance(value, (int, float)):
                    metrics[f"{class_name}_{metric_name}"] = float(value)

        # Log to ClearML
        clearml.upload_model(model_id, str(model_path), metrics=metrics)

        # Update registry
        update_entry(
            model_id,
            status="ready",
            artifact_path=str(model_path),
            val_score=accuracy,
            metrics=metrics,
        )

        logger.info(f"Training done successfully for model {model_id}")
        return model_id

    except Exception as e:
        logger.error(f"Training failed: {e}")
        update_entry(
            model_id,
            status="failed",
            error={"error": str(e), "traceback": traceback.format_exc()},
        )
        clearml.log_failure(str(e))
        raise



#PREDICT METHOD

def predict(model_id: str, features):
    """
    Run inference using saved model.
    """

    model_path = MODEL_DIR / f"{model_id}.joblib"

    # Local model
    if model_path.exists():
        model = load(model_path)
        logger.info(f"Loaded model {model_id} from local storage")
    else:
        # Try loading from ClearML
        try:
            clearml = ClearMLClient()
            model = clearml.load_model(model_id)
            logger.info(f"Loaded model {model_id} from ClearML")
        except Exception:
            logger.error(f"Model {model_id} not found anywhere")
            raise FileNotFoundError(f"Model {model_id} not found")

    # Prepare features array
    arr = np.array(features)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    preds = model.predict(arr).tolist()
    logger.info(f"Predicted {len(preds)} samples")
    return preds


def evaluate_model(model_id: str, dataset_name: str, use_test_split: bool = True):
    """
    Evaluate trained model on test dataset and return metrics.
    
    Args:
        model_id: ID of the model to evaluate
        dataset_name: Name of the dataset to use for evaluation
        use_test_split: Whether to use the test split of the dataset if available

    Returns:
        Dict with evaluation metrics
    
    Raises:
        FileNotFoundError: If model or dataset not found
        ValueError: If dataset is invalid
    """
    logger.info(f"Evaluating model {model_id} on dataset {dataset_name}")

    # Load model
    model_path = MODEL_DIR / f"{model_id}.joblib"
    if model_path.exists():
        model = load(model_path)
        logger.info(f"Loaded model {model_id} from local storage")
    else:
        try:
            clearml = ClearMLClient()
            model = clearml.load_model(model_id)
            logger.info(f"Loaded model {model_id} from ClearML")
        except Exception:
            logger.error(f"Model {model_id} not found anywhere")
            raise FileNotFoundError(f"Model {model_id} not found")

    # Load dataset
    X_test, y_test = _read_dataset(dataset_name)
    
    # If dataset has predefined splits, use test split
    # For now, using full dataset
    logger.info(f"Loaded test dataset with {len(y_test)} samples")
    
    # Generate predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    from app.core.metrics import prepare_evaluation_data
    y_true, y_pred = prepare_evaluation_data(y_test, y_pred)
    metrics = calculate_metrics(y_true, y_pred)
    
    # Add model and dataset info
    metrics["model_id"] = model_id
    metrics["dataset"] = dataset_name
    
    logger.info(f"Evaluation completed: accuracy={metrics['accuracy']:.4f}, f1_score={metrics['f1_score']:.4f}")
    return metrics


#DELETE METHOD

def delete_model(model_id: str):
    """
    Delete model locally and in ClearML registry.
    """

    from app.core.registry import delete_entry

    model_path = MODEL_DIR / f"{model_id}.joblib"

    if model_path.exists():
        model_path.unlink()
        logger.info(f"Deleted local model file: {model_path}")

    # Remove from registry
    deleted = delete_entry(model_id)

    try:
        clearml = ClearMLClient()
        clearml.delete_model(model_id)
    except Exception as e:
        logger.warning(f"Failed to delete model in ClearML: {e}")

    return deleted
