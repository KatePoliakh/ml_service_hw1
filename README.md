# ML Training Service

Производственная система для обучения и управления ML-моделями с REST API, gRPC интерфейсом и интерактивным дашбордом.

## Возможности

- **Обучение ML-моделей** с настройкой гиперпараметров
- **2+ класса моделей**: Linear, Classifier, Decision Tree
- **REST API** для интеграции с другими системами
- **gRPC сервис** для высокопроизводительных приложений
- **Streamlit дашборд** для интерактивной работы
- **Управление датасетами** - загрузка, просмотр, удаление
- **Версионирование моделей** с системой registry
- **Логирование** всех операций
- **Docker контейнеризация** для легкого развертывания

## Архитектура

```
ml_service/
├── app/                    # Основное приложение
│   ├── api/               # REST API эндпоинты
│   ├── core/              # Бизнес-логика (trainer, registry)
│   ├── proto/             # gRPC protobuf файлы
│   └── logger.py          # Конфигурация логирования
├── dashboard/             # Streamlit дашборд
├── docker/               # Docker конфигурации
├── k8s/                  # Kubernetes манифесты
└── datasets/             # Хранилище датасетов
```

## Требования

- Python 3.11+
- Docker & Docker Compose
- Minikube (для развертывания в Kubernetes)

## Быстрый старт

### Локальная установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd ml_service_hw1
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Сгенерируйте gRPC код:**
```bash
make proto
```

5. **Запустите сервисы:**

**Терминал 1 - REST API:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Терминал 2 - gRPC сервер:**
```bash
python app/grpc_server.py
```

**Терминал 3 - Дашборд:**
```bash
streamlit run dashboard/streamlit_app.py
```

### Запуск через Docker

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## API Документация

### REST API

После запуска доступны следующие эндпоинты:

- **Документация Swagger**: http://localhost:8000/docs
- **Документация ReDoc**: http://localhost:8000/redoc

#### Основные эндпоинты:

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/health` | Проверка статуса сервиса |
| GET | `/models/classes` | Список доступных классов моделей |
| GET | `/datasets` | Список загруженных датасетов |
| POST | `/datasets/upload` | Загрузка нового датасета |
| DELETE | `/datasets/{name}` | Удаление датасета |
| POST | `/train` | Запуск обучения модели |
| GET | `/models` | Список всех обученных моделей |
| GET | `/models/{model_id}` | Информация о конкретной модели |
| POST | `/predict` | Получение предсказания от модели |
| POST | `/models/{model_id}/retrain` | Переобучение модели |
| DELETE | `/models/{model_id}` | Удаление модели |

### gRPC API

gRPC сервер запускается на порту 50051. Доступные процедуры:

- `HealthCheck` - проверка здоровья
- `GetModelClasses` - список классов моделей  
- `ListDatasets` - список датасетов
- `TrainModel` - обучение модели
- `ListModels` - список моделей
- `Predict` - получение предсказаний

## Использование

### 1. Через REST API

```bash
# Загрузка датасета
curl -X POST "http://localhost:8000/datasets/upload" \
  -F "file=@your_dataset.csv"

# Обучение модели
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "your_dataset.csv",
    "model_class": "classifier", 
    "hyperparams": {"max_depth": 5},
    "model_name": "my_model"
  }'

# Получение предсказания
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "your_model_id",
    "features": [[1.0, 2.0, 3.0]]
  }'
```

### 2. Через gRPC

Пример клиента в `notebooks/grpc_client_notebook.ipynb`:

```python
import grpc
import ml_service_pb2
import ml_service_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = ml_service_pb2_grpc.MLServiceStub(channel)

# Проверка здоровья
response = stub.HealthCheck(ml_service_pb2.HealthRequest())
print(f"Status: {response.status}")
```

### 3. Через Streamlit дашборд

Откройте http://localhost:8501 и используйте интерактивный интерфейс:

- **Status** - мониторинг сервиса
- **Datasets** - управление датасетами
- **Training** - обучение моделей
- **Models** - управление моделями
- **Inference** - получение предсказаний

## Конфигурация

### Модели и гиперпараметры

Доступные классы моделей:
- `linear` - линейная регрессия
- `classifier` - классификатор на расстояниях  
- `decision_tree` - дерево решений

Примеры гиперпараметров:

```json
{
  "linear": {
    "learning_rate": 0.01,
    "iterations": 1000
  },
  "classifier": {},
  "decision_tree": {
    "max_depth": 5
  }
}
```

### Логирование

Логи сохраняются в `logs/ml_service.log` с ротацией (5MB на файл, 3 файла бэкапа).

## Развертывание в Minikube

### Требования
- Minikube
- kubectl
- Docker driver

### Запуск

```bash
# Инициализация Minikube
minikube start --driver=docker

# Полное развертывание
make full-deploy

# Или по шагам:
make build    # Сборка образов
make deploy   # Развертывание в Kubernetes
```

### Доступ к сервисам

```bash
# Получение внешних URL
minikube service ml-service --url
minikube service list
```

## Интеграции

### DVC (Data Version Control)

```bash
# Инициализация DVC
dvc init
dvc remote add -d minio s3://dvc-storage
dvc remote modify minio endpointurl http://localhost:9000

# Добавление датасета в DVC
dvc add datasets/your_dataset.csv
git add datasets/your_dataset.csv.dvc .gitignore
git commit -m "Add dataset version"
dvc push
```

### ClearML (опционально)

Сервис поддерживает интеграцию с ClearML для трекинга экспериментов:

```bash
# Запуск ClearML сервера
docker-compose up clearml -d
```

## Тестирование

### Ручное тестирование

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Список моделей
curl http://localhost:8000/models/classes

# Список датасетов  
curl http://localhost:8000/datasets
```

## Мониторинг

### Логи
```bash
# Просмотр логов в реальном времени
tail -f logs/ml_service.log

# Логи REST API
docker-compose logs ml-api

# Логи gRPC сервера  
docker-compose logs ml-grpc
```

### Метрики
Сервис предоставляет метрики качества моделей:
- Accuracy для классификации
- R²-like метрика для регрессии

## Разработка

### Структура проекта

```
ml_service/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── api/
│   │   ├── models.py        # Pydantic модели
│   │   └── routes.py        # REST API эндпоинты
│   ├── core/
│   │   ├── trainer.py       # Логика обучения моделей
│   │   ├── registry.py      # Реестр моделей
│   │   └── clearml_client.py # Интеграция с ClearML
│   ├── grpc_server.py       # gRPC сервер
│   └── logger.py           # Конфигурация логирования
├── dashboard/
│   └── streamlit_app.py    # Streamlit дашборд
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.grpc
│   └── Dockerfile.streamlit
├── k8s/                    # Kubernetes манифесты
├── proto/                  # Protobuf схемы
└── notebooks/              # Примеры использования
```

### Добавление новой модели

1. Добавьте класс модели в `app/core/trainer.py`
2. Обновите `MODEL_MAP` и `DEFAULT_HYPERPARAMS`
3. Добавьте enum в `app/api/models.py`

### Makefile команды

```bash
make help        # Список всех команд
make proto       # Генерация gRPC кода
make build       # Сборка Docker образов
make deploy      # Развертывание в Kubernetes
make clean       # Очистка ресурсов
make test        # Запуск тестов
```

## Устранение неполадок

### Частые проблемы

1. **ModuleNotFoundError: No module named 'app'**
   ```bash
   # Убедитесь, что вы в корне проекта
   cd /path/to/ml_service_hw1
   ```

2. **gRPC импорты не работают**
   ```bash
   make proto
   ```

3. **Порт уже занят**
   ```bash
   # Найдите процесс использующий порт
   lsof -i :8000
   # или
   netstat -tulpn | grep :8000
   ```

4. **Проблемы с зависимостями**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/ml_service.log`
2. Убедитесь, что все сервисы запущены
3. Проверьте документацию по API
4. Создайте issue в репозитории