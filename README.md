Требования
- Python 3.10+ (желательно 3.11+)

Установка зависимостей не нужна.
Запуск:
bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

python main.py init-db
python main.py run --host 127.0.0.1 --port 8000

Откройте в браузере:
http://127.0.0.1:8000/

`python main.py init-db` — создать БД и таблицы.
`python main.py generate --seconds 120` — сгенерировать метрики офлайн (запишет в БД).
`python main.py analyze --limit 120` — проанализировать метрики (создаст инциденты).
`python main.py run` — запустить генерацию+анализ в фоне и веб‑дашборд.
