# Быстрый старт

## Установка

```bash
# Из локальной папки
pip install -e .

# Или из PyPI (после публикации)
pip install sa-ui-operations-base
```

## Минимальный пример

Создайте файл `my_app.py`:

```python
import sys
from PySide6.QtWidgets import QApplication
from sa_ui_operations import MainWindow, PluginRegistry

# Создайте свой плагин
from sa_ui_operations import PluginInterface
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyPlugin(PluginInterface):
    def get_key(self):
        return "my_plugin"
    
    def get_title(self):
        return "Мой плагин"
    
    def create_widget(self, tab_context):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Привет из плагина!"))
        layout.addStretch(1)
        return widget
    
    def execute(self, tab_context, console_output_fn):
        console_output_fn("[RUN] Мой плагин выполняется")
        console_output_fn("[DONE]")

# Запуск приложения
def main():
    registry = PluginRegistry()
    registry.register(MyPlugin())
    
    app = QApplication(sys.argv)
    window = MainWindow(registry)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

Запустите:

```bash
python my_app.py
```

## Использование консольной команды

После установки доступна команда:

```bash
sa-ui-operations
```

Она запустит приложение с примерами плагинов.

