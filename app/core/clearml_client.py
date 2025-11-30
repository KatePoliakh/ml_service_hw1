import os
from app.logger import logger

class ClearMLClient:
    def __init__(self):
        self.task = None
        self._initialized = False
        self.project_name = os.getenv("CLEARML_PROJECT", "ML-Service")
        self._init_clearml()

   
    #INITIALIZATION
    def _init_clearml(self):
        """Try to initialize ClearML safely, fallback to offline mode"""
        try:
            from clearml import Task

            try:
                if Task.current_task() is not None:
                    Task.current_task().close()

                temp_task = Task.init(
                    project_name="__probe__",
                    task_name="probe",
                    reuse_last_task_id=False
                )
                temp_task.close()
            except Exception:
                logger.warning("ClearML server unreachable → offline mode")
                return

            self._initialized = True
            logger.info("ClearML initialized successfully")
        except Exception as e:
            logger.warning(f"ClearML init failed: {e}")
            self._initialized = False


    #CREATE EXPERIMENT
    def create_experiment(self, model_id, model_class, dataset_name, hyperparams=None, experiment_name=None):
        if not self._initialized:
            logger.info("ClearML offline → creating local experiment ID")
            return type("Task", (), {"id": f"local-{model_id}"})()

        try:
            from clearml import Task
            if Task.current_task() is not None:
                    Task.current_task().close()

            task_name = experiment_name or f"{model_class}_{model_id[:8]}"
            self.task = Task.init(
                project_name=self.project_name,
                task_name=task_name,
                task_type=Task.TaskTypes.training,
                reuse_last_task_id=False
            )

            self.task.connect({
                "model_id": model_id,
                "model_class": model_class,
                "dataset": dataset_name,
                **(hyperparams or {})
            })

            logger.info(f"Created ClearML experiment: {self.task.id}")
            return self.task
        except Exception as e:
            logger.error(f"Failed to init experiment: {e}")
            return type("Task", (), {"id": f"local-{model_id}"})()

    
    #LOG HYPERPARAMS
    def log_hyperparameters(self, hyperparams):
        if not self._initialized or not self.task:
            return
        try:
            self.task.connect(hyperparams)
        except Exception as e:
            logger.error(f"Failed to log hyperparameters: {e}")

   
    #LOG METRICS
    def log_metrics(self, metrics):
        if not self._initialized or not self.task:
            return
        try:
            logger_obj = self.task.get_logger()
            for key, value in metrics.items():
                logger_obj.report_scalar(title="metrics", series=key, value=value, iteration=0)
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    #UPLOAD MODEL
    def upload_model(self, model_id, local_path, metrics=None):
        if not self._initialized or not self.task:
            return
        try:
            from clearml import OutputModel
            output_model = OutputModel(task=self.task, name=model_id)
            output_model.update_weights(local_path)
            if metrics:
                self.log_metrics(metrics)
        except Exception as e:
            logger.error(f"Failed to upload model: {e}")


    #LOAD MODEL
    def load_model(self, model_id):
        if not self._initialized:
            raise FileNotFoundError("ClearML offline")
        try:
            from clearml import Model
            import joblib
            m = Model(model_id=model_id)
            path = m.get_local_copy()
            return joblib.load(path)
        except Exception as e:
            logger.error(f"Failed to load ClearML model: {e}")
            raise

    #LIST EXPERIMENTS
    def list_experiments(self):
        if not self._initialized:
            logger.info("ClearML offline → cannot list experiments")
            return []

        try:
            from clearml import Task
            tasks = Task.get_tasks(project_name=self.project_name) or []

            result = []
            for t in tasks:
                created = getattr(t, 'created', None)
                if created is None:
                    created = getattr(t, 'date_created', None)
                if created is not None:
                    created = created.isoformat() if hasattr(created, 'isoformat') else str(created)

                result.append({
                    "id": getattr(t, 'id', None),
                    "name": getattr(t, 'name', None),
                    "status": getattr(t, 'status', None),
                    "created": created
                })
            return result

        except Exception as e:
            logger.error(f"Failed to list experiments: {e}")
            return []


    #DELETE MODEL (stub)
    def delete_model(self, model_id):
        logger.info("ClearML model deletion not supported")
        return True

    # LOG FAILURE
    def log_failure(self, message):
        if not self._initialized or not self.task:
            return
        try:
            self.task.mark_failed(status_message=message)
        except Exception:
            pass
