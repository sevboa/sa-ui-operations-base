from ..plugin_system import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class OtherPlugin(PluginInterface):
    """
    Пример плагина - Other / placeholder.
    Простой плагин-заглушка.
    """
    
    def get_key(self):
        return "other"
    
    def get_title(self):
        return "Other / placeholder"
    
    def create_widget(self, tab_context):
        return OtherWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn):
        """
        Выполняет скрипт плагина Other.
        """
        console_output_fn("[RUN] Other plugin")
        console_output_fn("This is a placeholder plugin")
        console_output_fn("[DONE]")


class OtherWidget(QWidget):
    """
    Виджет настроек для плагина Other.
    """
    def __init__(self, tab_ctx, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Another operation UI placeholder"))
        layout.addStretch(1)

