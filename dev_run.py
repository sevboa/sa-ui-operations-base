#!/usr/bin/env python3
"""
Отладочный скрипт для запуска приложения без установки.
Используйте этот скрипт для разработки и отладки с брейкпоинтами.

Запуск:
    python dev_run.py
    или
    python -m pdb dev_run.py  # для отладки через pdb
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
# Это позволяет импортировать модули напрямую из исходников
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Теперь можно импортировать модули напрямую
from PySide6.QtWidgets import QApplication
from sa_ui_operations.base_ui import MainWindow
from sa_ui_operations.plugin_system import PluginRegistry
from sa_ui_operations.plugins.hello_plugin import HelloPlugin
from sa_ui_operations.plugins.other_plugin import OtherPlugin
from sa_ui_operations.settings import StringSetting, IntegerSetting


def main():
    """
    Главная функция для запуска приложения в режиме разработки.
    """
    print("=" * 60)
    print("Запуск в режиме разработки (без установки)")
    print(f"Корневая директория: {project_root}")
    print(f"Python путь: {sys.executable}")
    print("=" * 60)
    
    # Создаем реестр плагинов
    registry = PluginRegistry()
    
    # Регистрируем плагины
    registry.register(HelloPlugin())
    registry.register(OtherPlugin())
    
    print(f"Зарегистрировано плагинов: {len(registry.get_all_plugins())}")
    for plugin in registry.get_all_plugins():
        print(f"  - {plugin.get_title()} ({plugin.get_key()})")
    
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
    # В режиме разработки используем отдельное имя, чтобы не мешать с установленной версией
    window = MainWindow(registry, "SAUIOperations", "UniversalScriptsUI_Dev", global_settings)
    window.show()
    
    print("\nПриложение запущено. Закройте окно для завершения.")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

