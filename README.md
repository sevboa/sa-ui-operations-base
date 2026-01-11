# Universal Scripts UI - Библиотека для создания GUI приложений с плагинами

Универсальная библиотека для создания GUI приложений на PySide6 с системой плагинов. Позволяет легко создавать приложения с вкладками, где каждая вкладка может выполнять различные скрипты через систему плагинов.

## Особенности

- 🎨 **Базовый универсальный интерфейс** - готовый UI с вкладками, консолью и управлением
- 🔌 **Система плагинов** - легко добавлять новые скрипты как плагины
- 💾 **Автосохранение настроек** - автоматическое сохранение состояния вкладок и настроек плагинов
- 📝 **Консоль вывода** - встроенная сворачиваемая консоль для вывода результатов работы скриптов
- 🔄 **Переиспользование** - базовый интерфейс можно использовать в разных проектах

## Установка

### Установка из исходников

```bash
# Клонируйте репозиторий
git clone https://github.com/sevboa/sa-ui-operations-base.git
cd sa-ui-operations-base

# Установите библиотеку
pip install -e .
```

### Установка как пакет

После публикации в PyPI (или из локальной папки):

```bash
pip install sa-ui-operations-base
```

### Зависимости

Библиотека требует:
- Python >= 3.8
- PySide6 >= 6.6

## Быстрый старт

### 1. Базовое использование

После установки библиотеки:

```python
import sys
from PySide6.QtWidgets import QApplication
from sa_ui_operations import MainWindow, PluginRegistry
from sa_ui_operations.plugins.hello_plugin import HelloPlugin
from sa_ui_operations.plugins.other_plugin import OtherPlugin

def main():
    # Создаем реестр плагинов
    registry = PluginRegistry()
    
    # Регистрируем плагины
    registry.register(HelloPlugin())
    registry.register(OtherPlugin())
    
    # Создаем и запускаем приложение
    app = QApplication(sys.argv)
    window = MainWindow(registry)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 2. Создание собственного плагина

Создайте файл `my_plugin.py` в вашем проекте:

```python
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout

class MyPlugin(PluginInterface):
    """Пример собственного плагина"""
    
    def get_key(self):
        return "my_plugin"  # Уникальный идентификатор
    
    def get_title(self):
        return "Мой плагин"  # Название в выпадающем списке
    
    def create_widget(self, tab_context):
        """Создает виджет настроек плагина"""
        return MyPluginWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn):
        """Выполняет скрипт плагина"""
        # Получаем настройки из контекста
        text = tab_context.settings.value(
            tab_context.key("my_plugin/text"), 
            "", 
            type=str
        )
        
        # Выполняем работу
        console_output_fn(f"[RUN] Мой плагин запущен")
        console_output_fn(f"Введенный текст: {text}")
        # ... ваша логика ...
        console_output_fn("[DONE]")


class MyPluginWidget(QWidget):
    """Виджет настроек плагина"""
    def __init__(self, tab_ctx, parent=None):
        super().__init__(parent)
        self.tab_ctx = tab_ctx
        
        layout = QVBoxLayout(self)
        
        # Поле ввода
        row = QHBoxLayout()
        row.addWidget(QLabel("Текст:"))
        self.text_edit = QLineEdit()
        row.addWidget(self.text_edit)
        layout.addLayout(row)
        
        layout.addStretch(1)
        
        # Восстанавливаем сохраненное значение
        saved_text = self.tab_ctx.settings.value(
            self.tab_ctx.key("my_plugin/text"), 
            "", 
            type=str
        )
        self.text_edit.setText(saved_text)
        
        # Автосохранение при изменении
        self.text_edit.textChanged.connect(
            lambda v: self.tab_ctx.save_value("my_plugin/text", v)
        )
```

Затем зарегистрируйте плагин в вашем приложении:

```python
from my_plugin import MyPlugin

registry.register(MyPlugin())
```

## Архитектура

### Структура проекта

```
sa-ui-operations-base/
├── setup.py                # Скрипт установки через pip
├── pyproject.toml          # Современная конфигурация пакета
├── README.md               # Документация
├── INSTALL.md              # Инструкции по установке
├── LICENSE                 # Лицензия MIT
├── requirements.txt        # Зависимости
├── sa_ui_operations/        # Основной пакет библиотеки (устанавливается)
│   ├── __init__.py         # Экспорт основных классов
│   ├── base_ui.py          # Базовый универсальный интерфейс
│   ├── plugin_system.py    # Система плагинов (интерфейсы, реестр)
│   ├── main.py             # Консольная команда
│   └── plugins/            # Примеры плагинов
│       ├── __init__.py
│       ├── hello_plugin.py # Пример плагина
│       └── other_plugin.py # Пример плагина
└── examples/               # Примеры использования (НЕ устанавливаются)
    ├── __init__.py
    ├── example_usage.py    # Пример использования библиотеки
    └── README.md           # Описание примеров
```

**Важно:** При установке через `pip install` устанавливается только пакет `sa_ui_operations/`. 
Папка `examples/` остается в репозитории для справки, но не устанавливается в venv.

### Компоненты библиотеки

#### 1. `sa_ui_operations.base_ui` - Базовый интерфейс

Содержит готовые компоненты для создания GUI:

- **`MainWindow`** - главное окно с системой вкладок
- **`ScriptTab`** - виджет вкладки с верхней панелью управления и консолью
- **`CollapsibleConsole`** - сворачиваемая консоль для вывода
- **`TabContext`** - контекст вкладки для работы с настройками
- **`DebouncedWriter`** - утилита для отложенной записи настроек

#### 2. `sa_ui_operations.plugin_system` - Система плагинов

- **`PluginInterface`** - базовый интерфейс для плагинов
- **`PluginRegistry`** - реестр для регистрации и управления плагинами

**Импорт:**

```python
from sa_ui_operations import MainWindow, PluginRegistry, PluginInterface
# или
from sa_ui_operations.base_ui import MainWindow, TabContext
from sa_ui_operations.plugin_system import PluginInterface, PluginRegistry
```

## API Документация

### PluginInterface

Базовый интерфейс, который должен реализовать каждый плагин:

```python
class PluginInterface(ABC):
    @abstractmethod
    def get_key(self) -> str:
        """Возвращает уникальный идентификатор плагина"""
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """Возвращает отображаемое название плагина"""
        pass
    
    @abstractmethod
    def create_widget(self, tab_context) -> QWidget:
        """Создает виджет настроек плагина"""
        pass
    
    @abstractmethod
    def execute(self, tab_context, console_output_fn):
        """Выполняет скрипт плагина"""
        pass
```

### TabContext

Контекст вкладки предоставляет доступ к настройкам:

```python
# Получить значение настройки
value = tab_context.settings.value(
    tab_context.key("plugin_name/setting_key"), 
    default_value, 
    type=str
)

# Сохранить значение настройки
tab_context.save_value("plugin_name/setting_key", value)
```

**Важно:** Используйте `tab_context.key()` для создания ключей настроек, чтобы они были изолированы для каждой вкладки.

### PluginRegistry

Реестр плагинов для регистрации и доступа к плагинам:

```python
registry = PluginRegistry()

# Регистрация плагина
registry.register(MyPlugin())

# Получение плагина по ключу
plugin = registry.get_plugin("my_plugin")

# Получение всех плагинов
all_plugins = registry.get_all_plugins()

# Проверка наличия плагина
if registry.has_plugin("my_plugin"):
    print("Плагин зарегистрирован")
```

## Примеры использования

### Пример 1: Простой плагин без настроек

```python
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SimplePlugin(PluginInterface):
    def get_key(self):
        return "simple"
    
    def get_title(self):
        return "Простой плагин"
    
    def create_widget(self, tab_context):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Этот плагин не требует настроек"))
        layout.addStretch(1)
        return widget
    
    def execute(self, tab_context, console_output_fn):
        console_output_fn("[RUN] Простой плагин выполняется")
        # Ваша логика здесь
        console_output_fn("[DONE]")
```

### Пример 2: Плагин с несколькими настройками

```python
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QCheckBox
)

class AdvancedPlugin(PluginInterface):
    def get_key(self):
        return "advanced"
    
    def get_title(self):
        return "Продвинутый плагин"
    
    def create_widget(self, tab_context):
        return AdvancedWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn):
        # Получаем все настройки
        name = tab_context.settings.value(
            tab_context.key("advanced/name"), "", type=str
        )
        count = tab_context.settings.value(
            tab_context.key("advanced/count"), 5, type=int
        )
        enabled = tab_context.settings.value(
            tab_context.key("advanced/enabled"), False, type=bool
        )
        
        console_output_fn(f"[RUN] Плагин: {name}, count={count}, enabled={enabled}")
        # Ваша логика
        console_output_fn("[DONE]")


class AdvancedWidget(QWidget):
    def __init__(self, tab_ctx, parent=None):
        super().__init__(parent)
        self.tab_ctx = tab_ctx
        
        layout = QVBoxLayout(self)
        
        # Имя
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Имя:"))
        self.name_edit = QLineEdit()
        row1.addWidget(self.name_edit)
        layout.addLayout(row1)
        
        # Количество
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Количество:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100)
        row2.addWidget(self.count_spin)
        layout.addLayout(row2)
        
        # Включено
        self.enabled_check = QCheckBox("Включено")
        layout.addWidget(self.enabled_check)
        
        layout.addStretch(1)
        
        # Восстановление значений
        self.name_edit.setText(
            self.tab_ctx.settings.value(
                self.tab_ctx.key("advanced/name"), "", type=str
            )
        )
        self.count_spin.setValue(
            self.tab_ctx.settings.value(
                self.tab_ctx.key("advanced/count"), 5, type=int
            )
        )
        self.enabled_check.setChecked(
            self.tab_ctx.settings.value(
                self.tab_ctx.key("advanced/enabled"), False, type=bool
            )
        )
        
        # Автосохранение
        self.name_edit.textChanged.connect(
            lambda v: self.tab_ctx.save_value("advanced/name", v)
        )
        self.count_spin.valueChanged.connect(
            lambda v: self.tab_ctx.save_value("advanced/count", v)
        )
        self.enabled_check.toggled.connect(
            lambda v: self.tab_ctx.save_value("advanced/enabled", v)
        )
```

### Пример 3: Плагин с асинхронным выполнением

```python
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread, Signal

class AsyncWorker(QThread):
    """Поток для выполнения длительной операции"""
    output = Signal(str)
    
    def __init__(self, console_output_fn):
        super().__init__()
        self.console_output_fn = console_output_fn
    
    def run(self):
        for i in range(10):
            self.output.emit(f"Шаг {i+1}/10")
            self.msleep(500)  # Имитация работы
        self.output.emit("[DONE]")


class AsyncPlugin(PluginInterface):
    def get_key(self):
        return "async"
    
    def get_title(self):
        return "Асинхронный плагин"
    
    def create_widget(self, tab_context):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Плагин с асинхронным выполнением"))
        layout.addStretch(1)
        return widget
    
    def execute(self, tab_context, console_output_fn):
        console_output_fn("[RUN] Запуск асинхронной задачи")
        
        # Создаем и запускаем поток
        worker = AsyncWorker(console_output_fn)
        worker.output.connect(console_output_fn)
        worker.start()
```

## Интеграция в другие проекты

### Установка через pip (рекомендуется)

```bash
pip install sa-ui-operations-base
```

Затем в вашем коде:

```python
from sa_ui_operations import MainWindow, PluginRegistry
```

### Установка из локальной папки

Если библиотека находится локально:

```bash
pip install /path/to/sa-ui-operations-base
```

Или в режиме разработки:

```bash
pip install -e /path/to/sa-ui-operations-base
```

### Использование в requirements.txt

Добавьте в `requirements.txt` вашего проекта:

```
sa-ui-operations-base>=0.1.0
```

Затем установите:

```bash
pip install -r requirements.txt
```

## Настройки приложения

Настройки сохраняются автоматически через `QSettings`:
- Организация: `RequiemTools`
- Приложение: `UniversalScriptsUI`

Настройки хранятся в:
- **Linux**: `~/.config/RequiemTools/UniversalScriptsUI.conf`
- **Windows**: `HKEY_CURRENT_USER\Software\RequiemTools\UniversalScriptsUI`
- **macOS**: `~/Library/Preferences/com.RequiemTools.UniversalScriptsUI.plist`

Структура настроек:
```
tabs/
  <tab_id>/
    meta/
      name: "Название вкладки"
      operation: "plugin_key"
      console_expanded: true/false
    <plugin_key>/
      <setting_key>: <value>
```

## Советы и лучшие практики

1. **Именование ключей плагинов**: Используйте уникальные ключи, например `my_project_plugin_name`

2. **Изоляция настроек**: Всегда используйте `tab_context.key()` для создания ключей настроек

3. **Автосохранение**: Используйте `tab_context.save_value()` для автоматического сохранения настроек

4. **Обработка ошибок**: Добавьте обработку ошибок в метод `execute()`:

```python
def execute(self, tab_context, console_output_fn):
    try:
        console_output_fn("[RUN] Запуск плагина")
        # Ваша логика
        console_output_fn("[DONE]")
    except Exception as e:
        console_output_fn(f"[ERROR] {str(e)}")
```

5. **Валидация настроек**: Проверяйте значения настроек перед использованием:

```python
count = tab_context.settings.value(
    tab_context.key("plugin/count"), 10, type=int
)
if count < 1 or count > 100:
    count = 10  # Значение по умолчанию
```

## Лицензия

Используйте свободно в своих проектах.

## Поддержка

При возникновении вопросов или проблем создайте issue в репозитории проекта.

