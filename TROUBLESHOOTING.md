# Решение проблем при установке

## Ошибка "externally-managed-environment" даже с активированным venv

### Проблема

Даже когда виртуальное окружение активировано, pip все еще пытается установить в системный Python.

### Решение 1: Используйте полный путь к pip из venv

```bash
# Вместо просто pip используйте полный путь
.venv/bin/pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Решение 2: Пересоздайте виртуальное окружение

```bash
# Удалите старое окружение
rm -rf .venv

# Создайте новое
python -m venv .venv

# Активируйте
source .venv/bin/activate

# Проверьте, что используется правильный pip
which pip
# Должно показать: /path/to/sa-ui-operations-base/.venv/bin/pip

# Установите пакет
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Решение 3: Используйте python -m pip

```bash
# Активируйте venv
source .venv/bin/activate

# Используйте python -m pip вместо просто pip
python -m pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Решение 4: Проверьте активацию venv

```bash
# Проверьте переменную окружения
echo $VIRTUAL_ENV
# Должно показать путь к .venv

# Проверьте, какой pip используется
which pip
# Должно показать: /path/to/.venv/bin/pip

# Если показывает системный pip, переактивируйте:
deactivate
source .venv/bin/activate
```

## Проверка правильности установки

После установки проверьте:

```bash
# Проверьте версию
python -c "from sa_ui_operations import __version__; print(__version__)"

# Проверьте, где установлен пакет
pip show sa-ui-operations-base
```

Должно показать путь внутри `.venv`.

## Альтернативный способ: установка в режиме разработки

Если установка из Git не работает, используйте локальную установку:

```bash
# Активируйте venv
source .venv/bin/activate

# Клонируйте репозиторий (если еще не клонирован)
git clone https://github.com/sevboa/sa-ui-operations-base.git
cd sa-ui-operations-base

# Переключитесь на нужную версию
git checkout v0.1.0

# Установите в режиме разработки
pip install -e .
```

## Проблемы с Arch Linux

В Arch Linux иногда нужно явно указать Python версию:

```bash
# Используйте python3 явно
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

## Если ничего не помогает

Используйте `--break-system-packages` (НЕ рекомендуется, только в крайнем случае):

```bash
pip install --break-system-packages git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

**⚠️ Внимание:** Это установит пакет в системный Python, что может вызвать проблемы. Используйте только если действительно необходимо.






