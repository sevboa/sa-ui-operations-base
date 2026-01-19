# Установка из Git - Руководство

## Важно: Используйте виртуальное окружение!

**⚠️ Не устанавливайте в системный Python!** Используйте виртуальное окружение:

```bash
# Создайте виртуальное окружение (если еще не создано)
python -m venv .venv

# Активируйте его
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Теперь устанавливайте пакет
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

## Как это работает?

При установке из Git pip клонирует репозиторий и устанавливает пакет из указанной точки (тег, ветка или коммит).

## Рекомендации по выбору источника установки

### ✅ Используйте теги версий (рекомендуется для продакшена)

**Когда использовать:**
- Для стабильных проектов
- Когда нужна конкретная версия
- Для production окружений
- Когда важна воспроизводимость

**Преимущества:**
- ✅ Фиксированная версия - всегда одна и та же
- ✅ Стабильность - теги создаются для проверенных релизов
- ✅ Воспроизводимость - одинаковый код у всех

**Пример:**
```bash
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### ⚠️ Используйте ветку develop (только для разработки)

**Когда использовать:**
- Для разработки и тестирования
- Когда нужны последние изменения
- Для локальной разработки
- Когда тестируете новые функции

**Недостатки:**
- ⚠️ Нестабильность - код может меняться
- ⚠️ Невоспроизводимость - разные коммиты = разные версии
- ⚠️ Возможны баги - код может быть не протестирован

**Пример:**
```bash
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

## Способы установки

### 1. Установка конкретной версии по тегу (РЕКОМЕНДУЕТСЯ)

**Важно:** Убедитесь, что виртуальное окружение активировано!

```bash
# Активируйте виртуальное окружение (если еще не активировано)
source .venv/bin/activate  # Linux/macOS
# или
# .venv\Scripts\activate  # Windows

# Версия 0.1.0
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0

# Версия 0.1.1 (когда будет создана)
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.1
```

**Плюсы:**
- Стабильная версия
- Можно откатиться к предыдущей версии
- Все получат одинаковый код

### 2. Установка из ветки develop (только для разработки)

**Важно:** Убедитесь, что виртуальное окружение активировано!

```bash
# Активируйте виртуальное окружение
source .venv/bin/activate  # Linux/macOS

# Последний коммит из ветки develop
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

**Когда использовать:**
- Тестируете новые функции до релиза
- Разрабатываете плагины и нужны последние изменения
- Локальная разработка

**Важно:** После каждого обновления develop нужно переустанавливать:
```bash
pip install --upgrade --force-reinstall git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

### 3. Установка конкретного коммита

```bash
# По хешу коммита
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@abc123def456
```

**Когда использовать:**
- Нужна конкретная версия между релизами
- Отладка проблем с конкретным коммитом

### 4. Установка из ветки main/master

```bash
# Если у вас есть стабильная ветка main
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@main
```

## Использование в requirements.txt

### Рекомендуемый способ (по тегу):

```txt
# Стабильная версия 0.1.0
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Для разработки (из ветки):

```txt
# ⚠️ Только для разработки! Может быть нестабильно
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

### С указанием конкретного коммита:

```txt
# Конкретный коммит (для отладки)
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@abc123def456
```

## Рекомендуемый workflow

### Для production проектов:

1. **Используйте теги версий:**
   ```txt
   sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
   ```

2. **Обновляйте версию явно:**
   ```txt
   sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.1
   ```

3. **Тестируйте новую версию перед обновлением:**
   ```bash
   # Установите новую версию в тестовом окружении
   pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.1
   # Протестируйте
   # Если всё ок, обновите requirements.txt
   ```

### Для разработки:

1. **Используйте develop для тестирования:**
   ```bash
   pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop
   ```

2. **После релиза переключитесь на тег:**

```bash
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

## Проверка установленной версии

```python
from sa_ui_operations import __version__
print(f"Установленная версия: {__version__}")
```

## Обновление установленной версии

### Если установлена из тега:

```bash
# Установить новую версию
pip install --upgrade git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.1
```

### Если установлена из ветки:

```bash
# Получить последние изменения из ветки
pip install --upgrade --force-reinstall git+https://github.com/sevboa/sa-ui-operations-base.git@develop
```

## Доступные версии

Проверить доступные теги можно:

```bash
# Через git
git ls-remote --tags https://github.com/sevboa/sa-ui-operations-base.git

# Или на GitHub:
# https://github.com/sevboa/sa-ui-operations-base/tags
```

## Сравнение подходов

| Способ | Стабильность | Воспроизводимость | Когда использовать |
|--------|--------------|-------------------|---------------------|
| **Тег версии** | ✅ Высокая | ✅ Да | Production, стабильные проекты |
| **Ветка develop** | ⚠️ Низкая | ❌ Нет | Разработка, тестирование |
| **Конкретный коммит** | ✅ Средняя | ✅ Да | Отладка, промежуточные версии |

## Итоговые рекомендации

1. **Для продакшена:** Используйте только теги версий (`@v0.1.0`)
2. **Для разработки:** Можно использовать develop, но помните о нестабильности
3. **Для командной работы:** Всегда используйте теги - так все получат одинаковый код
4. **При обновлении:** Сначала тестируйте новую версию, затем обновляйте requirements.txt

## Примеры для разных сценариев

### Сценарий 1: Production проект

```txt
# requirements.txt
sa-ui-operations-base @ git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Сценарий 2: Разработка плагина

```bash
# Установить последнюю версию для тестирования
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@develop

# После релиза переключиться на тег
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@v0.1.0
```

### Сценарий 3: Отладка проблемы

```bash
# Установить конкретный коммит, где всё работало
pip install git+https://github.com/sevboa/sa-ui-operations-base.git@abc123def456
```
