# ML Training Service API Documentation

## Overview

This document describes the REST API endpoints for the ML Training Service.

## Base URL

- Local development: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Health Check

### GET `/health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00"
}
```

## Models

### GET `/models/classes`

Get list of available model classes.

**Response:**
```json
{
  "classes": ["logreg", "random_forest", "svm", "xgboost"]
}
```

### GET `/models`

Get list of all trained models.

**Response:**
```json
[
  {
    "id": "model_12345",
    "name": "logreg_1689012345",
    "model_class": "logreg",
    "hyperparams": {
      "C": 1.0,
      "max_iter": 1000
    },
    "dataset": "iris.csv",
    "status": "ready",
    "val_score": 0.96,
    "created_at": "2023-01-01T00:00:00",
    "artifact_path": "trained_models/model_12345.joblib"
  }
]
```

### GET `/models/{model_id}`

Get specific model information.

**Response:**
```json
{
  "id": "model_12345",
  "name": "logreg_1689012345",
  "model_class": "logreg",
  "hyperparams": {
    "C": 1.0,
    "max_iter": 1000
  },
  "dataset": "iris.csv",
  "status": "ready",
  "val_score": 0.96,
  "created_at": "2023-01-01T00:00:00",
  "artifact_path": "trained_models/model_12345.joblib"
}
```

### POST `/train`

Start model training job.

**Request:**
```json
{
  "dataset": "iris.csv",
  "model_class": "logreg",
  "hyperparams": {
    "C": 1.0
  },
  "model_name": "my_model",
  "experiment_name": "experiment_1"
}
```

**Response:**
```json
{
  "status": "training_started",
  "model_id": "model_12345",
  "model_name": "my_model"
}
```

### POST `/predict`

Get predictions from trained model.

**Request:**
```json
{
  "model_id": "model_12345",
  "features": [[5.1, 3.5, 1.4, 0.2]]
}
```

**Response:**
```json
{
  "predictions": [0],
  "model_id": "model_12345"
}
```

### POST `/models/evaluate`

Evaluate trained model on test dataset and return metrics.

**Request:**
```json
{
  "model_id": "model_12345",
  "dataset": "test_data.csv",
  "use_test_split": true
}
```

**Response:**
```json
{
  "model_id": "model_12345",
  "dataset": "test_data.csv",
  "accuracy": 0.96,
  "precision": 0.96,
  "recall": 0.96,
  "f1_score": 0.96,
  "class_metrics": {
    "0": {
      "precision": 1.0,
      "recall": 1.0,
      "f1_score": 1.0,
      "support": 10
    }
  },
  "total_samples": 30
}
```

### POST `/models/{model_id}/retrain`

Retrain existing model.

**Response:**
```json
{
  "status": "retraining_started",
  "new_model_name": "logreg_1689012345_retrained"
}
```

### DELETE `/models/{model_id}`

Delete trained model.

**Response:**
```json
{
  "status": "deleted",
  "model_id": "model_12345"
}
```

## Datasets

### GET `/datasets`

Get list of uploaded datasets.

**Response:**
```json
[
  {
    "name": "iris.csv",
    "size": 4500,
    "created_at": "2023-01-01T00:00:00",
    "dvc_tracked": false
  }
]
```

### POST `/datasets/upload`

Upload new dataset.

**Request (multipart/form-data):**
```
file: iris.csv
```

**Response:**
```json
{
  "status": "uploaded",
  "file": "iris.csv",
  "size": 4500
}
```

### DELETE `/datasets/{name}`

Delete dataset.

**Response:**
```json
{
  "status": "deleted",
  "dataset": "iris.csv"
}
```

## ClearML

### GET `/clearml/experiments`

Get list of ClearML experiments.

**Response:**
```json
{
  "experiments": [
    {
      "id": "task_12345",
      "name": "experiment_1",
      "status": "completed",
      "project": "ML-Service",
      "started": "2023-01-01T00:00:00"
    }
  ]
}
```