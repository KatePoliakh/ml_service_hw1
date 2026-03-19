# FEATURE PLAN: Model Evaluation Endpoint

## Goal
Add new endpoint: POST /models/evaluate

This endpoint:
- Loads trained model
- Accepts test dataset
- Computes evaluation metrics
- Returns metrics as JSON

---

## Step 1
Create request and response Pydantic schemas.

## Step 2
Create metrics utility module:
- accuracy
- precision
- recall
- f1-score

## Step 3
Add evaluation service function.

## Step 4
Add new FastAPI endpoint.

## Step 5
Add basic test for endpoint.

## Step 6
Run linter (ruff).

## Step 7
Update API.md.

## Step 8
Update CHANGELOG.md.