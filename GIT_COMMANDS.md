# Команды Git для работы с версиями

## Отправка коммита и тега в GitHub

```bash
# Отправить коммит в ветку develop
git push origin develop

# Отправить тег версии
git push origin v1.2.0

# Или отправить все теги сразу
git push origin --tags
```

## Установка конкретной версии из GitHub

### После того как вы запушите тег в GitHub:

```bash
# Установка версии 1.2.0 (без Git)
pip install https://github.com/sevboa/sa-ui-operations-base/archive/refs/tags/v1.2.0.zip

# Или с указанием ветки
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

## Создание нового релиза

1. Обновите версию в файлах:
   - `setup.py` → `version="1.2.0"`
   - `pyproject.toml` → `version = "1.2.0"`
   - `sa_ui_operations/__init__.py` → `__version__ = "1.2.0"`

2. Создайте коммит:
   ```bash
   git add .
   git commit -m "Версия 1.2.0 - описание изменений"
   ```

3. Создайте тег:
   ```bash
   git tag -a v1.2.0 -m "Версия 1.2.0 - описание изменений"
   ```

4. Отправьте в GitHub:
   ```bash
   git push origin develop
   git push origin v1.2.0
   ```

5. Создайте Release на GitHub (опционально):
   - Перейдите на https://github.com/sevboa/sa-ui-operations-base/releases/new
   - Выберите тег v1.2.0
   - Заполните описание релиза
   - Опубликуйте

## Проверка тегов

```bash
# Локальные теги
git tag -l

# Удаленные теги
git ls-remote --tags origin

# Информация о теге
git show v1.2.0
```

## Удаление тега (если нужно)

```bash
# Удалить локальный тег
git tag -d v1.2.0

# Удалить удаленный тег
git push origin --delete v1.2.0
```

