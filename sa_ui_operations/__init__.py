"""
SA UI Operations Base - Универсальная библиотека для создания GUI приложений с плагинами
"""

__version__ = "0.1.0"

from .base_ui import (
    MainWindow,
    ScriptTab,
    TabContext,
    CollapsibleConsole,
    DebouncedWriter,
)
from .plugin_system import (
    PluginInterface,
    PluginRegistry,
)

__all__ = [
    "MainWindow",
    "ScriptTab",
    "TabContext",
    "CollapsibleConsole",
    "DebouncedWriter",
    "PluginInterface",
    "PluginRegistry",
    "__version__",
]

