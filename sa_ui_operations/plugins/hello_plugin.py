from ..plugin_system import PluginInterface
from ..settings import StringSetting, IntegerSetting
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QSpinBox, QHBoxLayout
from PySide6.QtCore import QThread


class HelloPlugin(PluginInterface):
    """
    Пример плагина - Hello / demo.
    Демонстрирует базовую функциональность плагина.
    """
    
    def get_key(self):
        return "hello"
    
    def get_title(self):
        return "Hello / demo"
    
    def get_settings(self):
        """Возвращает список настроек для плагина"""
        return [
            StringSetting(
                key="api_url",
                label="API URL",
                default_value="https://api.example.com",
                description="Базовый URL API"
            ),
            StringSetting(
                key="api_token",
                label="API Token",
                default_value="",
                description="Токен авторизации"
            ),
            IntegerSetting(
                key="delay",
                label="Задержка (мс)",
                default_value=1000,
                description="Задержка между запросами в миллисекундах"
            ),
            IntegerSetting(
                key="count",
                label="Количество итераций",
                default_value=10,
                description="Количество повторений"
            ),
        ]
    
    def create_widget(self, tab_context):
        return HelloWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """
        Выполняет скрипт плагина Hello.
        Получает настройки из контекста и выполняет работу.
        """
        # Получаем настройки через систему настроек
        settings = self.get_settings()
        settings_dict = {s.key: s for s in settings}
        
        # Получаем значения настроек
        api_url = settings_dict.get("api_url", StringSetting("api_url", "API URL", "")).get_value(tab_context)
        api_token = settings_dict.get("api_token", StringSetting("api_token", "API Token", "")).get_value(tab_context)
        delay = settings_dict.get("delay", IntegerSetting("delay", "Задержка", 1000)).get_value(tab_context)
        count = settings_dict.get("count", IntegerSetting("count", "Количество", 10)).get_value(tab_context)
        
        # Получаем старые настройки для обратной совместимости
        verbose = tab_context.settings.value(
            tab_context.key("hello/verbose"), False, type=bool
        )
        
        # Выполняем скрипт
        console_output_fn(f"[RUN] Hello plugin")
        console_output_fn(f"  API URL: {api_url}")
        console_output_fn(f"  API Token: {'*' * len(api_token) if api_token else '(не задан)'}")
        console_output_fn(f"  Задержка: {delay} мс")
        console_output_fn(f"  Количество итераций: {count}")
        
        if verbose:
            console_output_fn("Verbose mode enabled")
        
        for i in range(count):
            if stop_flag and stop_flag():
                console_output_fn("[STOPPED] Выполнение прервано пользователем")
                return
            
            console_output_fn(f"  Step {i+1}/{count}")
            QThread.msleep(delay)  # Используем QThread.msleep() для неблокирующей паузы
        
        console_output_fn("[DONE]")


class HelloWidget(QWidget):
    """
    Виджет настроек для плагина Hello.
    """
    def __init__(self, tab_ctx, parent=None):
        super().__init__(parent)
        self.tab_ctx = tab_ctx

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hello operation UI"))
        
        self.chk = QCheckBox("Verbose output")
        self.spin = QSpinBox()
        self.spin.setRange(0, 100)
        self.spin.setValue(10)

        row = QHBoxLayout()
        row.addWidget(self.chk)
        row.addWidget(QLabel("Count:"))
        row.addWidget(self.spin)
        row.addStretch(1)

        layout.addLayout(row)
        layout.addStretch(1)

        # Restore operation-specific settings
        s = self.tab_ctx.settings
        self.chk.setChecked(s.value(self.tab_ctx.key("hello/verbose"), False, type=bool))
        self.spin.setValue(s.value(self.tab_ctx.key("hello/count"), 10, type=int))

        # Auto-save on change
        self.chk.toggled.connect(lambda v: self.tab_ctx.save_value("hello/verbose", v))
        self.spin.valueChanged.connect(lambda v: self.tab_ctx.save_value("hello/count", v))

