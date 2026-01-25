# Инструкции по сборке и публикации пакета

## Локальная установка для разработки

```bash
# Установка в режиме разработки (editable mode)
pip install -e .

# Или с зависимостями для разработки
pip install -e ".[dev]"
```

## Проверка конфигурации

```bash
python setup.py check
```

## Сборка дистрибутивов

### Создание исходного дистрибутива (sdist)

```bash
python setup.py sdist
```

Создаст файл в `dist/sa-ui-operations-base-1.2.0.tar.gz`

### Создание wheel дистрибутива

```bash
python setup.py bdist_wheel
```

Создаст файл в `dist/sa_ui_operations_base-1.2.0-py3-none-any.whl`

### Создание обоих форматов

```bash
python setup.py sdist bdist_wheel
```

## Установка из собранного дистрибутива

### Из tar.gz

```bash
pip install dist/sa-ui-operations-base-1.2.0.tar.gz
```

### Из wheel

```bash
pip install dist/sa_ui_operations_base-1.2.0-py3-none-any.whl
```

## Публикация в PyPI

### 1. Установка twine

```bash
pip install twine
```

### 2. Сборка пакета

```bash
python setup.py sdist bdist_wheel
```

### 3. Проверка пакета

```bash
twine check dist/*
```

### 4. Тестовая публикация в TestPyPI

```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

### 5. Публикация в PyPI

```bash
twine upload dist/*
```

После публикации установка будет доступна через:

```bash
pip install sa-ui-operations-base
```

## Обновление версии

1. Обновите версию в `setup.py`:
   ```python
   version="1.2.0"
   ```

2. Обновите версию в `pyproject.toml`:
   ```toml
   version = "1.2.0"
   ```

3. Обновите версию в `sa_ui_operations/__init__.py`:
   ```python
   __version__ = "1.2.0"
   ```

4. Соберите и опубликуйте новую версию

## Структура пакета

После установки пакет будет доступен как:

```python
from sa_ui_operations import MainWindow, PluginRegistry
from sa_ui_operations.base_ui import TabContext
from sa_ui_operations.plugin_system import PluginInterface
```

## Проверка установки

```bash
python -c "from sa_ui_operations import MainWindow, PluginRegistry; print('✓ Установка успешна!')"
```

## Использование консольной команды

После установки доступна команда:

```bash
sa-ui-operations
```

