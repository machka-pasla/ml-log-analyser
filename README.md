# ML Anomaly Detection for Logs

Учебный/демонстрационный проект: обучение на нормальном потоке логов и последующее обнаружение аномалий с выдачей результатов через API и дашборд.

## Архитектура

```
src/
  domain/            # доменные модели (лог, результат аномалии)
  application/       # парсинг, фичи, обучение, синтетика
  infrastructure/    # хранение, модели, конфигурация, реестр артефактов
  api/               # FastAPI
```

Компоненты:
- Ingest: приём логов из файлов и через API.
- Parser: JSON Lines и plain text (regex).
- Feature extraction: независимый модуль с тестами.
- Model: базовый частотный и ML (Isolation Forest).
- Storage: SQLAlchemy (SQLite или PostgreSQL).
- API: `/ingest`, `/anomalies`, `/metrics`, `/health`.
- Dashboard: встроенная страница `/dashboard` + Grafana (docker-compose).

## Быстрый старт (локально)

1) Установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

2) Подготовьте конфигурацию:

```bash
cp .env.example .env
```

3) Сгенерируйте синтетические логи:

```bash
PYTHONPATH=src python scripts/generate_logs.py --total 500 --anomaly-ratio 0.05
```

4) Обучите модель на нормальном потоке:

```bash
PYTHONPATH=src python scripts/train.py --input data/logs/normal.jsonl --format jsonl --model isolation_forest
```

5) Запустите API:

```bash
PYTHONPATH=src uvicorn api.main:app --reload
```

6) Отправьте тестовые логи:

```bash
PYTHONPATH=src python scripts/ingest_file.py --input data/logs/with_anomalies.jsonl --format jsonl
```

7) Проверьте:
- API: `http://localhost:8000/health`
- Аномалии: `http://localhost:8000/anomalies`
- Метрики: `http://localhost:8000/metrics`
- Дашборд: `http://localhost:8000/dashboard`

## Запуск через Docker Compose

```bash
docker compose up --build
```

По умолчанию API автоматически обучает модель на `data/logs/normal.jsonl` при первом запуске (см. `AUTO_TRAIN_ON_STARTUP`).
Если нужно переобучить вручную:

```bash
docker compose run --rm api python scripts/train.py --input data/logs/normal.jsonl --format jsonl --model isolation_forest
```

Далее:
- API: `http://localhost:8000`
- Grafana: `http://localhost:3000` (login: admin / password: admin)
  - Дашборд `Log Anomalies` и источник данных Postgres создаются автоматически.

## Форматы логов

### JSON Lines (основной формат)
Обязательные поля: `timestamp`, `host` или `service`, `level`, `message`.
Опциональные поля: `user`, `ip`, `request_id`, `attributes`.

Пример:
```
{"timestamp":"2026-01-15T10:00:00+00:00","host":"auth-svc","level":"INFO","message":"User login succeeded","user":"alice","ip":"10.0.0.10","request_id":"req-1001"}
```

### Plain text
Базовый шаблон:
```
<timestamp> <level> <host|service> <message> [user=...] [ip=...] [request_id=...]
```

Пример:
```
2026-01-15T10:10:00+00:00 INFO auth-svc User login succeeded user=alice ip=10.0.0.10 request_id=req-2001
```

## Модели

- **Baseline**: частотный метод по нормализованным шаблонам сообщений.
- **Isolation Forest**: ML-модель с числовыми признаками (уровень, длина сообщения, временные признаки, наличие IP и т.д.).

Артефакты сохраняются в `artifacts/` с метаданными и версией модели.
Для периодического обновления достаточно запускать `scripts/train.py` на новом батче нормальных логов — реестр обновит `latest.json`.

## Тесты и качество

```bash
ruff check .
ruff format --check .
pytest
```

## Демо-сценарий

1) Обучить модель на `data/logs/normal.jsonl`.
2) Отправить `data/logs/with_anomalies.jsonl` через `/ingest`.
3) Убедиться, что `/anomalies` возвращает подозрительные события.
4) Посмотреть метрики на `/dashboard` или в Grafana.

## Допущения и ограничения

- Модель обучается на заранее размеченном нормальном потоке логов.
- Признаки являются упрощёнными и служат для демонстрации подхода.
- Для режима streaming предусмотрен интерфейс-заглушка; интеграции Kafka/Redis Streams не реализованы.
- По умолчанию пороги аномалий настраиваются в `.env`.

## Документы

- `docs/analysis.tex` — LaTeX-документ «Анализатор логов на основе ИИ» по ГОСТ.
- Примеры логов: `data/logs/`.

Сборка отчёта (нужен `inkscape` для SVG, запускать из `docs/` дважды для ссылок и оглавления):

```bash
cd docs
xelatex --shell-escape analysis.tex
xelatex --shell-escape analysis.tex
```
