# Установка и использование библиотеки

## Установка из исходников

### 1. Клонирование репозитория

```bash
git clone https://github.com/sevboa/sa-ui-operations-base.git
cd sa-ui-operations-base
```

### 2. Установка в режиме разработки

```bash
pip install -e .
```

Или для установки с зависимостями для разработки:

```bash
pip install -e ".[dev]"
```

### 3. Установка обычным способом

```bash
pip install .
```

## Использование после установки

### Импорт в вашем коде

```python
from sa_ui_operations import MainWindow, PluginRegistry
from sa_ui_operations.plugin_system import PluginInterface
from sa_ui_operations.base_ui import TabContext

# Создание реестра и регистрация плагинов
registry = PluginRegistry()
registry.register(MyPlugin())

# Создание приложения
app = QApplication(sys.argv)
window = MainWindow(registry)
window.show()
app.exec()
```

### Использование консольной команды

После установки доступна консольная команда:

```bash
sa-ui-operations
```

Эта команда запустит приложение с примерами плагинов.

## Создание собственного приложения

Создайте файл `my_app.py`:

```python
import sys
from PySide6.QtWidgets import QApplication
from sa_ui_operations import MainWindow, PluginRegistry
from my_plugins import MyCustomPlugin

def main():
    registry = PluginRegistry()
    registry.register(MyCustomPlugin())
    
    app = QApplication(sys.argv)
    window = MainWindow(registry)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

## Сборка дистрибутива

### Создание исходного дистрибутива

```bash
python setup.py sdist
```

### Создание wheel дистрибутива

```bash
python setup.py bdist_wheel
```

### Установка из wheel

```bash
pip install dist/sa_ui_operations_base-0.1.0-py3-none-any.whl
```

## Публикация в PyPI (опционально)

### 1. Создание аккаунта на PyPI

Зарегистрируйтесь на https://pypi.org/

### 2. Установка инструментов

```bash
pip install twine
```

### 3. Сборка пакета

```bash
python setup.py sdist bdist_wheel
```

### 4. Проверка пакета

```bash
twine check dist/*
```

### 5. Загрузка в PyPI

```bash
twine upload dist/*
```

После публикации установка будет доступна через:

```bash
pip install sa-ui-operations-base
```

## Обновление версии

Для обновления версии измените `version` в `setup.py` и `pyproject.toml`:

```python
version="0.1.1"  # в setup.py
```

```toml
version = "0.1.1"  # в pyproject.toml
```

Также обновите `__version__` в `sa_ui_operations/__init__.py`.

