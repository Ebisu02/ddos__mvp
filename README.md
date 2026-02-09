Требования
- Python 3.10+

Установка venv для Windows: virtualenv --system-site-packages -p python3 ./venv
Запуск:
- Linux: bash python -m venv .venv
- Windows: .venv\Scripts\activate

Откройте в браузере:
http://127.0.0.1:8000/

- `python main.py run --host 127.0.0.1 --port 8000` - запуск сервера.
- `python main.py init-db` — создать БД и таблицы.
- `python main.py generate --seconds 120` — сгенерировать метрики офлайн (запишет в БД).
- `python main.py analyze --limit 120` — проанализировать метрики (создаст инциденты).
- `python main.py run` — запустить генерацию+анализ в фоне и веб‑дашборд.
