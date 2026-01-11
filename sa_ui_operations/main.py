"""
Точка входа для консольной команды sa-ui-operations
"""
import sys
from PySide6.QtWidgets import QApplication
from .base_ui import MainWindow
from .plugin_system import PluginRegistry
from .plugins.hello_plugin import HelloPlugin
from .plugins.other_plugin import OtherPlugin


def main():
    """
    Главная функция для запуска приложения с примерами плагинов.
    Для использования в своих проектах создайте свою функцию main()
    и зарегистрируйте свои плагины.
    """
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
