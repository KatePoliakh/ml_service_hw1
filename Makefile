.PHONY: all build push deploy clean test proto minikube-setup full-deploy

# Variables
DOCKER_REGISTRY ?= localhost:5000
APP_NAME ?= ml-service

all: full-deploy

# Minikube setup
minikube-setup:
	@echo "Deleting any existing Minikube cluster..."
	minikube delete || true
	@echo "Starting Minikube..."
	minikube start --driver=docker
	@echo "Setting Docker env to Minikube..."
	eval $$(minikube docker-env)
	@echo "Minikube setup done."

# Build Docker images inside Minikube
build:
	@echo "Building Docker images inside Minikube..."
	eval $$(minikube docker-env) && \
	docker build -t $(APP_NAME)-api -f docker/Dockerfile.api . && \
	docker build -t $(APP_NAME)-grpc -f docker/Dockerfile.grpc . && \
	docker build -t $(APP_NAME)-dashboard -f docker/Dockerfile.streamlit .

# Push images to local registry (optional)
push:
	docker build -t $(DOCKER_REGISTRY)/$(APP_NAME)-api -f docker/Dockerfile.api .
	docker push $(DOCKER_REGISTRY)/$(APP_NAME)-api
	docker build -t $(DOCKER_REGISTRY)/$(APP_NAME)-grpc -f docker/Dockerfile.grpc .
	docker push $(DOCKER_REGISTRY)/$(APP_NAME)-grpc
	docker build -t $(DOCKER_REGISTRY)/$(APP_NAME)-dashboard -f docker/Dockerfile.streamlit .
	docker push $(DOCKER_REGISTRY)/$(APP_NAME)-dashboard

# Deploy Kubernetes manifests
deploy:
	@echo "Applying Kubernetes manifests..."
	kubectl apply -f k8s/pvc-dvc-cache.yaml
	kubectl apply -f k8s/deployment-minio.yaml
	kubectl apply -f k8s/deployment-clearml.yaml
	kubectl apply -f k8s/deployment-api.yaml
	kubectl apply -f k8s/deployment-dashboard.yaml
	@echo "Deployment done."


# Generate gRPC code
proto:
	python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/ml_service.proto

# Local development via Docker Compose
local:
	docker-compose up -d

stop:
	docker-compose down


# Clean up everything
clean:
	@echo "Cleaning Docker containers..."
	docker-compose down || true

	@if minikube status &>/dev/null; then \
		echo "Cleaning Kubernetes resources..."; \
		kubectl delete -f k8s/ --ignore-not-found=true || true; \
		minikube delete || true; \
	else \
		echo "Minikube is not running, skipping k8s cleanup"; \
	fi

# DVC setup
dvc-init:
	dvc init
	dvc remote add -d minio s3://dvc-storage
	dvc remote modify minio endpointurl http://localhost:9000

# Full deploy: setup Minikube, build images, deploy everything
full-deploy: clean minikube-setup build deploy
	@echo "Full deployment finished!"
