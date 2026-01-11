"""
Пример использования библиотеки sa-ui-operations-base

Этот файл демонстрирует базовое использование библиотеки
с примерами плагинов.
"""
import sys
from PySide6.QtWidgets import QApplication
from sa_ui_operations import MainWindow, PluginRegistry
from sa_ui_operations.plugins.hello_plugin import HelloPlugin
from sa_ui_operations.plugins.other_plugin import OtherPlugin


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

