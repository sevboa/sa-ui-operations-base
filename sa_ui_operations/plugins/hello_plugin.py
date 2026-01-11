from ..plugin_system import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QSpinBox, QHBoxLayout


class HelloPlugin(PluginInterface):
    """
    Пример плагина - Hello / demo.
    Демонстрирует базовую функциональность плагина.
    """
    
    def get_key(self):
        return "hello"
    
    def get_title(self):
        return "Hello / demo"
    
    def create_widget(self, tab_context):
        return HelloWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn):
        """
        Выполняет скрипт плагина Hello.
        Получает настройки из контекста и выполняет работу.
        """
        # Получаем настройки из контекста
        verbose = tab_context.settings.value(
            tab_context.key("hello/verbose"), False, type=bool
        )
        count = tab_context.settings.value(
            tab_context.key("hello/count"), 10, type=int
        )
        
        # Выполняем скрипт
        console_output_fn(f"[RUN] Hello plugin: count={count}, verbose={verbose}")
        
        if verbose:
            console_output_fn("Verbose mode enabled")
        
        for i in range(count):
            console_output_fn(f"  Step {i+1}/{count}")
        
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

