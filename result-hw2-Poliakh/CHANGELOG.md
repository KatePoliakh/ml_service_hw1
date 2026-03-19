# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New endpoint `POST /models/evaluate` for model evaluation on test datasets
  - Returns accuracy, precision, recall, f1_score metrics
  - Supports per-class metrics
  - Requires trained model ID and dataset name
- New `EvaluateRequest` and `EvaluateResponse` Pydantic schemas
- New `app/core/metrics.py` module with metrics calculation utilities
- New `evaluate_model()` function in `app/core/trainer.py`
- Basic tests for evaluate endpoint in `tests/test_api.py`

### Changed

- Updated API documentation in `API.md`
- Fixed linting issues with ruff

## [1.0.0] - 2023-01-01

### Added

- Initial release
- REST API for ML model training and prediction
- gRPC service support
- Streamlit dashboard
- ClearML integration
- DVC support for data versioning
