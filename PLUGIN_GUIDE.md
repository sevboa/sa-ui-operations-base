# Руководство по созданию плагинов

Это руководство поможет вам создать собственный плагин для библиотеки `sa-ui-operations-base`. Плагины позволяют добавлять новые скрипты и операции в приложение без изменения базового кода.

## 🎯 Ключевые особенности

- **Автоматическое создание формы настроек** - вам не нужно писать код для виджетов настроек, просто определите список настроек
- **Простота использования** - достаточно реализовать несколько методов интерфейса
- **Гибкость** - поддержка различных типов настроек (строка, пароль, число)
- **Общие настройки** - возможность определять настройки, общие для всех плагинов
- **Визуальное разделение** - автоматическое разделение общих и плагин-специфичных настроек

## 📋 Содержание

1. [Базовый интерфейс плагина](#базовый-интерфейс-плагина)
2. [Создание простого плагина](#создание-простого-плагина)
3. [Добавление настроек](#добавление-настроек)
4. [Использование настроек в execute()](#использование-настроек-в-execute)
5. [Типы настроек](#типы-настроек)
6. [Общие настройки](#общие-настройки)
7. [Полный пример](#полный-пример)

---

## Базовый интерфейс плагина

Каждый плагин должен реализовать интерфейс `PluginInterface`, который требует следующие методы:

```python
from sa_ui_operations import PluginInterface

class MyPlugin(PluginInterface):
    def get_key(self) -> str:
        """Уникальный идентификатор плагина"""
        pass
    
    def get_title(self) -> str:
        """Отображаемое название плагина"""
        pass
    
    def create_widget(self, tab_context):
        """Создает виджет основного окна плагина"""
        pass
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """Выполняет скрипт плагина"""
        pass
    
    def get_settings(self) -> List[SettingItem]:
        """Возвращает список настроек плагина (опционально)"""
        return []
```

---

## Создание простого плагина

### Минимальный пример

```python
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SimplePlugin(PluginInterface):
    """Простой плагин без настроек"""
    
    def get_key(self):
        return "simple"
    
    def get_title(self):
        return "Простой плагин"
    
    def create_widget(self, tab_context):
        """Создает простое окно плагина"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Это простой плагин без настроек"))
        layout.addStretch(1)
        return widget
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """Выполняет скрипт"""
        console_output_fn("[RUN] Простой плагин запущен")
        console_output_fn("Выполняю работу...")
        # Ваша логика здесь
        console_output_fn("[DONE]")
    
    def get_settings(self):
        """Нет настроек"""
        return []
```

---

## Добавление настроек

### Автоматическое создание формы настроек

**Важно:** Вам НЕ нужно создавать виджеты настроек вручную! Библиотека автоматически создает форму на основе списка настроек, который вы возвращаете из метода `get_settings()`.

### Пример плагина с настройками

```python
from sa_ui_operations import PluginInterface
from sa_ui_operations.settings import StringSetting, IntegerSetting, PasswordSetting
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread

class ApiPlugin(PluginInterface):
    """Плагин с настройками для работы с API"""
    
    def get_key(self):
        return "api_plugin"
    
    def get_title(self):
        return "API Plugin"
    
    def create_widget(self, tab_context):
        """Основное окно плагина (может быть простым)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("API Plugin"))
        layout.addWidget(QLabel("Настройки доступны через кнопку ⚙"))
        layout.addStretch(1)
        return widget
    
    def get_settings(self):
        """
        Определяет настройки плагина.
        Форма создается автоматически - не нужно писать код для виджетов!
        """
        return [
            StringSetting(
                key="api_url",                    # Уникальный ключ настройки
                label="URL API",                  # Отображаемое имя в форме
                default_value="https://api.example.com",  # Значение по умолчанию
                description="Базовый URL для API запросов"  # Подсказка (опционально)
            ),
            PasswordSetting(
                key="api_token",
                label="API Token",
                default_value="",
                description="Токен авторизации (будет скрыт при вводе)"
            ),
            IntegerSetting(
                key="timeout",
                label="Таймаут (сек)",
                default_value=30,
                description="Таймаут запросов в секундах"
            ),
        ]
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """Выполняет скрипт с использованием настроек"""
        # Получаем настройки через систему настроек
        settings = self.get_settings()
        settings_dict = {s.key: s for s in settings}
        
        # Получаем значения настроек
        api_url = settings_dict["api_url"].get_value(tab_context)
        api_token = settings_dict["api_token"].get_value(tab_context)
        timeout = settings_dict["timeout"].get_value(tab_context)
        
        # Используем настройки
        console_output_fn(f"[RUN] API Plugin")
        console_output_fn(f"  URL: {api_url}")
        console_output_fn(f"  Token: {'*' * len(api_token) if api_token else '(не задан)'}")
        console_output_fn(f"  Timeout: {timeout} сек")
        
        # Ваша логика работы с API
        # ...
        
        console_output_fn("[DONE]")
```

---

## Использование настроек в execute()

### Рекомендуемый способ

```python
def execute(self, tab_context, console_output_fn, stop_flag=None):
    # 1. Получаем список настроек
    settings = self.get_settings()
    
    # 2. Создаем словарь для удобного доступа
    settings_dict = {s.key: s for s in settings}
    
    # 3. Получаем значения настроек
    api_url = settings_dict["api_url"].get_value(tab_context)
    timeout = settings_dict["timeout"].get_value(tab_context)
    
    # 4. Используем настройки в логике
    # ...
```

### Альтернативный способ (прямое создание SettingItem)

```python
def execute(self, tab_context, console_output_fn, stop_flag=None):
    # Создаем SettingItem напрямую (менее удобно)
    api_url_setting = StringSetting("api_url", "API URL", "https://api.example.com")
    api_url = api_url_setting.get_value(tab_context)
    
    # ...
```

**Рекомендуется использовать первый способ** - он более надежный и использует те же объекты, что определены в `get_settings()`.

---

## Типы настроек

Библиотека поддерживает следующие типы настроек:

### 1. StringSetting - Текстовая строка

```python
from sa_ui_operations.settings import StringSetting

StringSetting(
    key="server_name",
    label="Имя сервера",
    default_value="localhost",
    description="Имя или адрес сервера"
)
```

### 2. PasswordSetting - Пароль (с маскированием)

```python
from sa_ui_operations.settings import PasswordSetting

PasswordSetting(
    key="password",
    label="Пароль",
    default_value="",
    description="Пароль для авторизации"
)
```

### 3. IntegerSetting - Целое число

```python
from sa_ui_operations.settings import IntegerSetting

IntegerSetting(
    key="port",
    label="Порт",
    default_value=8080,
    description="Номер порта сервера"
)
```

### 4. FloatSetting - Число с плавающей точкой

```python
from sa_ui_operations.settings import FloatSetting

FloatSetting(
    key="threshold",
    label="Порог",
    default_value=0.5,
    description="Пороговое значение (0.0 - 1.0)"
)
```

---

## Общие настройки

Общие настройки определяются при создании `MainWindow` и доступны всем плагинам:

```python
from sa_ui_operations import MainWindow, PluginRegistry
from sa_ui_operations.settings import StringSetting, IntegerSetting

# Определяем общие настройки
global_settings = [
    StringSetting(
        key="api_base_url",
        label="Базовый URL API",
        default_value="https://api.example.com",
        description="Общий базовый URL для всех API запросов"
    ),
    IntegerSetting(
        key="default_timeout",
        label="Таймаут по умолчанию (сек)",
        default_value=30,
        description="Общий таймаут для всех операций"
    ),
]

# Создаем окно с общими настройками
registry = PluginRegistry()
# ... регистрация плагинов ...
window = MainWindow(registry, "MyCompany", "MyApp", global_settings)
```

### Использование общих настроек в плагине

```python
def execute(self, tab_context, console_output_fn, stop_flag=None):
    # Получаем общую настройку
    api_base_url = tab_context.get_global_value(
        "settings/api_base_url", 
        "https://api.example.com", 
        type=str
    )
    
    default_timeout = tab_context.get_global_value(
        "settings/default_timeout", 
        30, 
        type=int
    )
    
    console_output_fn(f"Базовый URL: {api_base_url}")
    console_output_fn(f"Таймаут: {default_timeout} сек")
```

---

## Полный пример

Вот полный пример плагина со всеми возможностями:

```python
from sa_ui_operations import PluginInterface
from sa_ui_operations.settings import StringSetting, PasswordSetting, IntegerSetting
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread

class FullExamplePlugin(PluginInterface):
    """
    Полный пример плагина с настройками и длительной операцией.
    Демонстрирует все возможности библиотеки.
    """
    
    def get_key(self):
        return "full_example"
    
    def get_title(self):
        return "Полный пример плагина"
    
    def create_widget(self, tab_context):
        """
        Создает основное окно плагина.
        Может быть простым или содержать дополнительную информацию.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Полный пример плагина"))
        layout.addWidget(QLabel("Настройки доступны через кнопку ⚙"))
        layout.addStretch(1)
        return widget
    
    def get_settings(self):
        """
        Определяет настройки плагина.
        Форма создается автоматически библиотекой!
        """
        return [
            StringSetting(
                key="server_url",
                label="URL сервера",
                default_value="http://localhost:8080",
                description="Адрес сервера для подключения"
            ),
            PasswordSetting(
                key="password",
                label="Пароль",
                default_value="",
                description="Пароль для авторизации"
            ),
            IntegerSetting(
                key="timeout",
                label="Таймаут (сек)",
                default_value=30,
                description="Таймаут подключения в секундах"
            ),
            IntegerSetting(
                key="retry_count",
                label="Количество повторов",
                default_value=3,
                description="Сколько раз повторять запрос при ошибке"
            ),
        ]
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """
        Выполняет скрипт плагина.
        
        Args:
            tab_context: Контекст вкладки для доступа к настройкам
            console_output_fn: Функция для вывода текста в консоль
            stop_flag: Функция для проверки остановки (callable() -> bool)
        """
        # Получаем настройки
        settings = self.get_settings()
        settings_dict = {s.key: s for s in settings}
        
        server_url = settings_dict["server_url"].get_value(tab_context)
        password = settings_dict["password"].get_value(tab_context)
        timeout = settings_dict["timeout"].get_value(tab_context)
        retry_count = settings_dict["retry_count"].get_value(tab_context)
        
        # Выводим информацию
        console_output_fn("[RUN] Полный пример плагина")
        console_output_fn(f"  Server URL: {server_url}")
        console_output_fn(f"  Password: {'*' * len(password) if password else '(не задан)'}")
        console_output_fn(f"  Timeout: {timeout} сек")
        console_output_fn(f"  Retry count: {retry_count}")
        console_output_fn("")
        
        # Имитация работы с проверкой остановки
        for attempt in range(1, retry_count + 1):
            if stop_flag and stop_flag():
                console_output_fn(f"[STOPPED] Выполнение прервано на попытке {attempt}")
                return
            
            console_output_fn(f"Попытка {attempt}/{retry_count}...")
            
            # Имитация работы (неблокирующая пауза)
            for i in range(3):
                if stop_flag and stop_flag():
                    console_output_fn("[STOPPED] Выполнение прервано")
                    return
                
                QThread.msleep(500)  # 500мс пауза
                console_output_fn(f"  Шаг {i+1}/3")
            
            console_output_fn("  Попытка завершена")
        
        console_output_fn("[DONE] Все попытки выполнены")
```

---

## Регистрация плагина

После создания плагина его нужно зарегистрировать:

```python
from sa_ui_operations import MainWindow, PluginRegistry
from my_plugin import FullExamplePlugin

# Создаем реестр
registry = PluginRegistry()

# Регистрируем плагин
registry.register(FullExamplePlugin())

# Создаем окно
window = MainWindow(registry, "MyCompany", "MyApp")
window.show()
```

---

## Важные замечания

### 1. Использование stop_flag

Всегда проверяйте `stop_flag` в циклах и длительных операциях:

```python
def execute(self, tab_context, console_output_fn, stop_flag=None):
    for i in range(100):
        if stop_flag and stop_flag():
            console_output_fn("[STOPPED] Выполнение прервано")
            return
        
        # Ваша работа
        QThread.msleep(100)  # Используйте QThread.msleep() вместо time.sleep()
```

### 2. Неблокирующие паузы

Используйте `QThread.msleep()` вместо `time.sleep()` для пауз, чтобы не блокировать UI:

```python
from PySide6.QtCore import QThread

# Правильно
QThread.msleep(1000)  # 1 секунда

# Неправильно (заблокирует UI)
# import time
# time.sleep(1)
```

### 3. Автоматическое сохранение настроек

Настройки сохраняются автоматически при изменении. Не нужно вызывать методы сохранения вручную.

### 4. Визуальное разделение настроек

- **Общие настройки** отображаются в группе "Общие настройки"
- **Настройки плагина** отображаются в группе "Настройки плагина"
- Разделение происходит автоматически через QGroupBox

---

## Примеры в репозитории

Полные рабочие примеры плагинов можно найти в:
- `sa_ui_operations/plugins/hello_plugin.py` - пример с настройками
- `sa_ui_operations/plugins/other_plugin.py` - пример с паузой и остановкой

---

## Вопросы и поддержка

Если у вас возникли вопросы по созданию плагинов, проверьте:
1. Примеры плагинов в репозитории
2. Документацию API в `README.md`
3. Исходный код базовых классов в `sa_ui_operations/`

