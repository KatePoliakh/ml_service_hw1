# Runbook: Запуск мониторинга и нагрузочного тестирования

## Предварительные требования
- Python 3.11+
- Docker и Docker Compose (для локального запуска)
- Или kubectl + minikube/kind (для k8s)

---

## Часть 1: Локальный запуск API с мониторингом

### 1.1 Создание виртуального окружения (venv)
```bash
cd /Users/ekaterinapolah/Desktop/hse/ml/ml_service_hw1
python -m venv venv
source venv/bin/activate
```

### 1.2 Установка зависимостей
```bash
pip install -r requirements.txt
```

### 1.3 Запуск API локально
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.4 Проверка /metrics endpoint (в новом терминале)
```bash
# Активируйте venv в новом терминале тоже
source venv/bin/activate
curl http://localhost:8000/metrics
```
Ожидаемый результат: Prometheus-формат метрик (http_requests_total, http_request_duration_seconds и т.д.)

### 1.5 Проверка основных endpoint'ов
```bash
# Health check
curl http://localhost:8000/health

# Список моделей
curl http://localhost:8000/models

# Список датасетов
curl http://localhost:8000/datasets

# Предсказание (требуется существующая модель)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"model_id": "test_model", "features": [[5.1, 3.5, 1.4, 0.2]]}'
```

---

## Часть 2: Запуск VictoriaMetrics + Grafana (Docker Compose)

### 2.1 Добавление сервисов в docker-compose.yml
Создайте файл `docker-compose.monitoring.yml`:
```yaml
version: '3.8'

services:
  victoriametrics:
    image: victoriametrics/victoria-metrics:v1.102.1
    ports:
      - "8428:8428"
    command:
      - "--storageDataPath=/victoria-metrics-data"
      - "--retentionPeriod=1"
      - "--selfScrapeInterval=10s"
      - "--promscrape.config=/etc/vm/promscrape.yml"
    volumes:
      - ./config/promscrape.yml:/etc/vm/promscrape.yml

  grafana:
    image: grafana/grafana:11.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

### 2.2 Создание конфигурации scrape
```bash
mkdir -p config
cat > config/promscrape.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "ml-api"
    metrics_path: /metrics
    static_configs:
      - targets: ["host.docker.internal:8000"]
EOF
```

### 2.3 Запуск мониторинга
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2.4 Проверка VictoriaMetrics
```bash
# Проверка targets
curl http://localhost:8428/api/v1/targets

# Проверка метрик
curl 'http://localhost:8428/api/v1/query?query=http_requests_total'
```

### 2.5 Настройка Grafana

#### 2.5.1 Открыть Grafana
```
http://localhost:3000
```
Логин: `admin`
Пароль: `admin` (или тот, что указан в GF_SECURITY_ADMIN_PASSWORD)

#### 2.5.2 Добавление Data Source
1. Configuration → Data Sources → Add data source
2. Выбрать "Prometheus"
3. URL: `http://victoriametrics:8428`
4. Save & Test

#### 2.5.3 Импорт Dashboard
1. Create → Import
2. Upload JSON или вставить содержимое из `k8s/deployment-grafana.yaml` (раздел grafana-dashboard-ml-service)
3. Выбрать VictoriaMetrics как datasource

#### 2.5.4 Проверка панелей
Должны отображаться:
- RPS by Endpoint
- Error Rate %
- Latency p50/p95/p99
- Model Inference Duration p50/p95

---

## Часть 3: Запуск в Kubernetes (minikube/kind)

### 3.1 Запуск minikube
```bash
minikube start --driver=docker --memory=4096 --cpus=2
```

### 3.2 Сборка образа API
```bash
# В терминале с запущенным minikube
eval $(minikube docker-env)
docker build -t ml-service-api:latest -f docker/Dockerfile.api .
```

### 3.3 Применение манифестов
```bash
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/service-api.yaml
kubectl apply -f k8s/deployment-victoriametrics.yaml
kubectl apply -f k8s/deployment-grafana.yaml
```

### 3.4 Проверка статуса подов
```bash
kubectl get pods
kubectl get svc
```

### 3.5 Доступ к сервисам
```bash
# API
kubectl port-forward svc/ml-api-service 8000:8000

# VictoriaMetrics
kubectl port-forward svc/victoriametrics-service 8428:8428

# Grafana
kubectl port-forward svc/grafana-service 3000:3000
```

---

## Часть 4: Нагрузочное тестирование (Locust)

### 4.1 Запуск Locust локально (с активированным venv)
```bash
source venv/bin/activate
locust -f tests/load/locustfile.py --host http://localhost:8000
```

### 4.2 Открытие веб-интерфейса Locust
```
http://localhost:8089
```

### 4.3 Настройка теста (в веб-интерфейсе)
- Number of users: 30 (для baseline)
- Spawn rate: 5
- Host: http://localhost:8000

### 4.4 Запуск теста
Нажать "Start swarming"

### 4.5 Сценарии тестирования (по очереди)

#### Smoke Test
- Users: 5
- Spawn rate: 1
- Duration: 2 минуты

#### Baseline Test
- Users: 30
- Spawn rate: 5
- Duration: 10 минут

#### Stress Test
- Users: 120
- Spawn rate: 10
- Duration: 15 минут

#### Spike Test
- Users: 100
- Spawn rate: 25
- Duration: 5 минут

### 4.6 CLI-режим (без веб-интерфейса, с venv)
```bash
source venv/bin/activate

# Smoke
locust -f tests/load/locustfile.py --host http://localhost:8000 -u 5 -r 1 -t 2m --headless

# Baseline
locust -f tests/load/locustfile.py --host http://localhost:8000 -u 30 -r 5 -t 10m --headless

# Stress
locust -f tests/load/locustfile.py --host http://localhost:8000 -u 120 -r 10 -t 15m --headless

# Spike
locust -f tests/load/locustfile.py --host http://localhost:8000 -u 100 -r 25 -t 5m --headless
```

### 4.7 Экспорт результатов
```bash
source venv/bin/activate
locust -f tests/load/locustfile.py --host http://localhost:8000 -u 30 -r 5 -t 10m --headless --csv=load_test_results
```
Создаст файлы:
- `load_test_results_stats.csv`
- `load_test_results_failures.csv`
- `load_test_results_exceptions.csv`

---

## Часть 5: Проверка метрик в Grafana во время теста

### 5.1 Запросы для проверки метрик

#### RPS по эндпоинтам
```promql
sum by (handler) (rate(http_requests_total[1m]))
```

#### Error Rate %
```promql
100 * (sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m])))
```

#### Latency p50/p95/p99
```promql
# p50
histogram_quantile(0.50, sum by (le, handler) (rate(http_request_duration_seconds_bucket[5m])))

# p95
histogram_quantile(0.95, sum by (le, handler) (rate(http_request_duration_seconds_bucket[5m])))

# p99
histogram_quantile(0.99, sum by (le, handler) (rate(http_request_duration_seconds_bucket[5m])))
```

#### Model Inference Duration
```promql
# p50
histogram_quantile(0.50, sum by (le) (rate(model_inference_seconds_bucket[5m])))

# p95
histogram_quantile(0.95, sum by (le) (rate(model_inference_seconds_bucket[5m])))
```

### 5.2 Создание скриншота дашборда
1. В Grafana: Share → Direct link rendered image
2. Или просто сделать скриншот экрана
3. Сохранить как `result-hw2-Poliakh/grafana-dashboard.png`

---

## Часть 6: Заполнение отчета

Отредактируйте `result-hw2-Poliakh/LOAD_TEST_REPORT.md`, добавив:
- Фактические значения RPS, latency, error rate для каждого сценария
- Наблюдения из Grafana
- Выводы о производительности системы

---

## Часть 7: Остановка

### Docker Compose
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Kubernetes
```bash
kubectl delete -f k8s/deployment-grafana.yaml
kubectl delete -f k8s/deployment-victoriametrics.yaml
kubectl delete -f k8s/deployment-api.yaml
kubectl delete -f k8s/service-api.yaml
```

### Locust
Ctrl+C в терминале с Locust

---

## Чек-лист перед сдачей

- [ ] API запущен и `/metrics` возвращает метрики
- [ ] VictoriaMetrics собирает метрики с API
- [ ] Grafana доступна и показывает дашборд
- [ ] Все 4 панели дашборда отображают данные:
  - [ ] RPS by Endpoint
  - [ ] Error Rate %
  - [ ] Latency p50/p95/p99
  - [ ] Model Inference p50/p95
- [ ] Прогнаны сценарии Locust (smoke, baseline, stress, spike)
- [ ] Заполнен `LOAD_TEST_REPORT.md`
- [ ] Добавлен скриншот `result-hw2-Poliakh/grafana-dashboard.png`

---

## Быстрый старт (4 команды)

```bash
# 1. Создание и активация venv (один раз)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Запуск API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. В новом терминале — проверка метрик
source venv/bin/activate
curl http://localhost:8000/metrics

# 4. Запуск Locust
source venv/bin/activate
locust -f tests/load/locustfile.py --host http://localhost:8000
```
