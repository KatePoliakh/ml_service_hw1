from locust import HttpUser, task, between
import random


class MLServiceUser(HttpUser):
    wait_time = between(0.2, 1.5)

    @task(1)
    def health(self):
        self.client.get("/health", name="/health")

    @task(2)
    def list_models(self):
        self.client.get("/models", name="/models")

    @task(3)
    def list_datasets(self):
        self.client.get("/datasets", name="/datasets")

    @task(4)
    def predict(self):
        payload = {
            "model_id": "test_model",
            "features": [[
                random.uniform(4.0, 8.0),
                random.uniform(2.0, 4.5),
                random.uniform(1.0, 7.0),
                random.uniform(0.1, 2.5)
            ]]
        }
        self.client.post("/predict", json=payload, name="/predict")
