"""
Точка входа для консольной команды sa-ui-operations
"""
import sys
from PySide6.QtWidgets import QApplication
from .base_ui import MainWindow
from .plugin_system import PluginRegistry
from .plugins.hello_plugin import HelloPlugin
from .plugins.other_plugin import OtherPlugin
from .settings import StringSetting, IntegerSetting


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
    
    # Определяем общие настройки для всех плагинов (опционально)
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
    
    # Создаем и запускаем приложение
    app = QApplication(sys.argv)
    
    # Создаем главное окно с уникальными именами для изоляции настроек
    window = MainWindow(registry, "SAUIOperations", "UniversalScriptsUI", global_settings)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
