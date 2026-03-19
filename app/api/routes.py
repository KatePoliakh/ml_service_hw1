from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from app.logger import logger
from app.api.models import TrainRequest, PredictRequest, ModelInfo, DatasetInfo, ModelClass, EvaluateRequest, EvaluateResponse
from app.core import trainer, registry
from app.core.clearml_client import ClearMLClient
from pathlib import Path
from datetime import datetime
import time
from app.core.monitoring import MODEL_INFERENCE_SECONDS

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "datasets"
DATA_DIR.mkdir(exist_ok=True)

# Health check
@router.get("/health", tags=["status"])
async def health():
    """Check service health status"""
    logger.info("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Get available model classes
@router.get("/models/classes", tags=["models"])
async def model_classes():
    """Get list of available model classes"""
    logger.info("Model classes requested")
    return {"classes": [cls.value for cls in ModelClass]}

# Dataset management
DATA_DIR = Path("datasets")
DATA_DIR.mkdir(exist_ok=True)

@router.get("/datasets", response_model=list[DatasetInfo], tags=["datasets"])
async def list_datasets():
    """Get list of available datasets"""
    logger.info("Datasets list requested")
    datasets = []
    for file_path in DATA_DIR.iterdir():
        if file_path.is_file() and file_path.suffix in ['.csv', '.json']:
            stat = file_path.stat()
            datasets.append(DatasetInfo(
                name=file_path.name,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                dvc_tracked=(DATA_DIR / (file_path.name + '.dvc')).exists()
            ))
    return datasets

@router.post("/datasets/upload", tags=["datasets"])
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a new dataset"""
    logger.info(f"Uploading dataset: {file.filename}")
    
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(400, "Only CSV and JSON files are supported")
    
    dest = DATA_DIR / file.filename
    try:
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Successfully uploaded dataset: {file.filename}")
        return {"status": "uploaded", "file": file.filename, "size": len(content)}
    except Exception as e:
        logger.error(f"Failed to upload dataset: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.delete("/datasets/{name}", tags=["datasets"])
async def delete_dataset(name: str):
    """Delete a dataset"""
    logger.info(f"Deleting dataset: {name}")
    
    path = DATA_DIR / name
    dvc_path = DATA_DIR / (name + '.dvc')
    
    if not path.exists():
        raise HTTPException(404, "Dataset not found")
    
    try:
        path.unlink()
        if dvc_path.exists():
            dvc_path.unlink()
        logger.info(f"Successfully deleted dataset: {name}")
        return {"status": "deleted", "dataset": name}
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(500, f"Deletion failed: {str(e)}")

# Model training
@router.post("/train", tags=["training"])
async def train_endpoint(req: TrainRequest, background_tasks: BackgroundTasks):
    """Start model training job"""

    logger.info(f"Training request received: dataset={req.dataset}, model_class={req.model_class}, model_name={req.model_name}")

    dataset_path = DATA_DIR / req.dataset
    if not dataset_path.exists():
        raise HTTPException(404, f"Dataset {req.dataset} not found")

    if not req.model_name or req.model_name.strip() == "":
        ts = int(datetime.now().timestamp())
        req.model_name = f"{req.model_class.value}_{ts}"
        logger.info(f"Auto-generated model name: {req.model_name}")

    if req.hyperparams is None:
        req.hyperparams = {}

    entry = registry.create_entry(
        name=req.model_name,
        model_class=req.model_class.value,
        hyperparams=req.hyperparams,
        dataset=req.dataset
    )

    model_id = entry["id"]
    logger.info(f"Registry entry created for model {model_id}")

    background_tasks.add_task(
        trainer.train,
        req.dataset,
        req.model_class.value,
        req.hyperparams,
        req.model_name,
        req.experiment_name
    )

    return {
        "status": "training_started",
        "model_id": model_id,
        "model_name": req.model_name
    }


# Model management
@router.get("/models", response_model=list[ModelInfo], tags=["models"])
async def list_models():
    """Get list of all trained models"""
    logger.info("Models list requested")
    return registry.list_entries()

@router.get("/models/{model_id}", response_model=ModelInfo, tags=["models"])
async def get_model(model_id: str):
    """Get specific model info"""
    logger.info(f"Model info requested: {model_id}")
    model = registry.get_entry(model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    return model

@router.post("/predict", tags=["models"])
async def predict(payload: PredictRequest):
    """Get prediction from model"""
    logger.info(f"Prediction requested for model: {payload.model_id}")
    
    model = registry.get_entry(payload.model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    
    if model["status"] != "ready":
        raise HTTPException(400, "Model is not ready for prediction")
    
    try:
        start = time.perf_counter()
        predictions = trainer.predict(payload.model_id, payload.features)
        duration = time.perf_counter() - start
        MODEL_INFERENCE_SECONDS.observe(duration)
        return {"predictions": predictions, "model_id": payload.model_id}
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")

@router.post("/models/evaluate", response_model=EvaluateResponse, tags=["models"])
async def evaluate_model_endpoint(request: EvaluateRequest):
    """Evaluate model on test dataset and return metrics"""
    logger.info(f"Evaluation requested for model: {request.model_id} on dataset: {request.dataset}")
    
    # Validate model exists
    model = registry.get_entry(request.model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    
    if model["status"] != "ready":
        raise HTTPException(400, "Model is not ready for evaluation")
    
    # Validate dataset exists
    dataset_path = DATA_DIR / request.dataset
    if not dataset_path.exists():
        raise HTTPException(404, "Dataset not found")
    
    try:
        metrics = trainer.evaluate_model(
            model_id=request.model_id,
            dataset_name=request.dataset,
            use_test_split=request.use_test_split
        )
        
        return metrics
        
    except FileNotFoundError as e:
        logger.error(f"File not found during evaluation: {e}")
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(500, f"Evaluation failed: {str(e)}")

@router.post("/models/{model_id}/retrain", tags=["models"])
async def retrain(model_id: str, background_tasks: BackgroundTasks):
    """Retrain an existing model"""
    logger.info(f"Retrain requested for model: {model_id}")
    
    model = registry.get_entry(model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    
    new_model_name = f"{model['name']}_retrained"
    background_tasks.add_task(
        trainer.train,
        model["dataset"],
        model["model_class"],
        model["hyperparams"],
        new_model_name,
        f"retrain_{model_id}"
    )
    
    return {"status": "retraining_started", "new_model_name": new_model_name}

@router.delete("/models/{model_id}", tags=["models"])
async def delete_model(model_id: str):
    """Delete a trained model"""
    logger.info(f"Delete requested for model: {model_id}")
    
    model = registry.get_entry(model_id)
    if not model:
        raise HTTPException(404, "Model not found")
    
    try:
        from app.core.trainer import delete_model as delete_model_func
        delete_model_func(model_id)
        
        if model.get("clearml_id"):
            clearml_client = ClearMLClient()
            clearml_client.delete_model(model["clearml_id"])
        
        logger.info(f"Successfully deleted model: {model_id}")
        return {"status": "deleted", "model_id": model_id}
    except Exception as e:
        logger.error(f"Failed to delete model: {e}")
        raise HTTPException(500, f"Deletion failed: {str(e)}")

# ClearML integration
@router.get("/clearml/experiments", tags=["clearml"])
async def get_clearml_experiments():
    """Get list of ClearML experiments"""
    logger.info("ClearML experiments requested")
    try:
        clearml_client = ClearMLClient()
        experiments = clearml_client.list_experiments()
        return {"experiments": experiments}
    except Exception as e:
        logger.error(f"Failed to get ClearML experiments: {e}")
        raise HTTPException(500, f"Failed to get experiments: {str(e)}")