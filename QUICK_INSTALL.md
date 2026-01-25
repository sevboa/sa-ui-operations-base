# Быстрая установка

## Шаг 1: Создайте виртуальное окружение

```bash
# Создайте виртуальное окружение
python -m venv .venv

# Активируйте его
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

После активации вы увидите `(.venv)` в начале строки терминала.

## Шаг 2: Установите библиотеку

### Установка стабильной версии (рекомендуется):

```bash
pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/tags/v1.2.0.zip
```

### Установка последней версии из develop (для разработки):

```bash
pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/heads/develop.zip
```

## Шаг 3: Проверьте установку

```python
python -c "from sa_ui_operations import __version__; print(f'Версия: {__version__}')"
```

Должно вывести: `Версия: 1.2.0`

## Решение проблем

### Ошибка "externally-managed-environment"

Эта ошибка возникает, если вы пытаетесь установить в системный Python.

**Решение 1:** Убедитесь, что venv активирован правильно:
```bash
# Проверьте, что используется правильный pip
which pip
# Должно показать: /path/to/.venv/bin/pip

# Если показывает системный pip, переактивируйте:
deactivate
source .venv/bin/activate
```

**Решение 2:** Используйте полный путь к pip:
```bash
.venv/bin/pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/tags/v1.2.0.zip
```

**Решение 3:** Используйте `python -m pip`:
```bash
python -m pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/tags/v1.2.0.zip
```

**Решение 4:** Пересоздайте виртуальное окружение:
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/tags/v1.2.0.zip
```

Подробнее см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Ошибка при установке из ZIP

Убедитесь, что:
1. Виртуальное окружение активировано
2. У вас есть интернет-соединение
3. Тег версии существует (проверьте на GitHub)

## Использование в проекте

После установки используйте в своем коде:

```python
from sa_ui_operations import MainWindow, PluginRegistry
# ... ваш код
```

## Деактивация виртуального окружения

Когда закончите работу:

```bash
deactivate
```

