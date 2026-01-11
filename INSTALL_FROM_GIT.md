# Установка конкретной версии из Git

## Установка по тегу версии

### Установка версии 0.1.0

```bash
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Установка конкретного коммита

```bash
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@<commit-hash>
```

### Установка из ветки

```bash
# Из ветки develop
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop

# Из ветки main/master
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@main
```

### Установка в режиме разработки

```bash
# Клонируйте репозиторий
git clone https://github.com/sevboa/sa-ui-operations-base.git
cd sa-ui-operations-base

# Переключитесь на нужную версию
git checkout v0.1.0

# Установите в режиме разработки
pip install -e .
```

## Использование в requirements.txt

### Конкретная версия по тегу

```txt
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Конкретный коммит

```txt
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@abc123def456
```

### Ветка (последний коммит)

```txt
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

## Проверка установленной версии

```python
from sa_ui_operations import __version__
print(__version__)  # Выведет: 0.1.0
```

## Доступные версии

Проверить доступные теги можно на GitHub или через:

```bash
git ls-remote --tags https://github.com/sevboa/sa-ui-operations-base.git
```

## Обновление версии

При обновлении версии:

1. Обновите версию в файлах:
   - `setup.py` → `version="0.1.1"`
   - `pyproject.toml` → `version = "0.1.1"`
   - `sa_ui_operations/__init__.py` → `__version__ = "0.1.1"`

2. Создайте коммит и тег:
   ```bash
   git add .
   git commit -m "Версия 0.1.1"
   git tag -a v0.1.1 -m "Версия 0.1.1"
   git push origin main
   git push origin v0.1.1
   ```

3. Установка новой версии:
   ```bash
   pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.1
   ```

