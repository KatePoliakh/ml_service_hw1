"""
gRPC server for ML service - fixed version
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import grpc
from concurrent import futures

try:
    import ml_service_pb2
    import ml_service_pb2_grpc
    print("✓ Successfully imported proto files from root")
except ImportError as e:
    print(f"✗ Failed to import proto files: {e}")
    sys.exit(1)

try:
    from app.logger import logger
    from app.core.trainer import train, predict
    from app.core.registry import list_entries, get_entry
    print("✓ Successfully imported application modules")
except ImportError as e:
    print(f"✗ Failed to import application modules: {e}")
    sys.exit(1)

class MLServiceServicer(ml_service_pb2_grpc.MLServiceServicer):
    def HealthCheck(self, request, context):
        logger.info("gRPC HealthCheck called")
        return ml_service_pb2.HealthResponse(status="healthy")
    
    def GetModelClasses(self, request, context):
        logger.info("gRPC GetModelClasses called")
        classes = ["linear", "classifier"]
        return ml_service_pb2.ModelClassesResponse(classes=classes)
    
    def ListDatasets(self, request, context):
        logger.info("gRPC ListDatasets called")
        try:
            import os
            from pathlib import Path
            from datetime import datetime
            
            DATA_DIR = Path("datasets")
            datasets = []
            
            if DATA_DIR.exists():
                for file_path in DATA_DIR.iterdir():
                    if file_path.is_file() and file_path.suffix in ['.csv', '.json']:
                        stat = file_path.stat()
                        datasets.append(
                            ml_service_pb2.DatasetInfo(
                                name=file_path.name,
                                size=stat.st_size,
                                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                dvc_tracked=False
                            )
                        )
            
            response = ml_service_pb2.DatasetsResponse()
            response.datasets.extend(datasets)
            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.DatasetsResponse()
    
    def TrainModel(self, request, context):
        logger.info(f"gRPC TrainModel called: {request.model_class}")
        try:
            hyperparams_dict = {}
            for key, value in request.hyperparams.items():
                hyperparams_dict[key] = value
            
            model_id = train(
                request.dataset,
                request.model_class,
                hyperparams_dict,
                request.model_name,
                request.experiment_name
            )
            
            return ml_service_pb2.TrainResponse(
                status="started",
                model_id=model_id,
                message="Training started successfully"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.TrainResponse(status="failed", message=str(e))
    
    def ListModels(self, request, context):
        logger.info("gRPC ListModels called")
        try:
            models = list_entries()
            response = ml_service_pb2.ModelsResponse()
            for model in models:
                response.models.append(
                    ml_service_pb2.ModelInfo(
                        id=model["id"],
                        name=model["name"],
                        model_class=model["model_class"],
                        status=model["status"],
                        created_at=model["created_at"],
                        dataset=model.get("dataset", ""),
                        val_score=model.get("val_score", 0.0),
                        clearml_id=model.get("clearml_id", "")
                    )
                )
            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.ModelsResponse()
    
    def Predict(self, request, context):
        logger.info(f"gRPC Predict called for model: {request.model_id}")
        try:
            features = []
            for feature_list in request.features:
                features.append(list(feature_list.values))
            
            predictions = predict(request.model_id, features)
            
            return ml_service_pb2.PredictResponse(
                predictions=predictions,
                model_id=request.model_id
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.PredictResponse()

def serve():
    """Start gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ml_service_pb2_grpc.add_MLServiceServicer_to_server(MLServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("gRPC server started on port 50051")
    print("gRPC server is running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()