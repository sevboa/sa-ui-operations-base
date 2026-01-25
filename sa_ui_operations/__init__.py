"""
SA UI Operations Base - Универсальная библиотека для создания GUI приложений с плагинами
"""

__version__ = "1.2.0"

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
from .settings import (
    SettingItem,
    SettingType,
    StringSetting,
    PasswordSetting,
    IntegerSetting,
    FloatSetting,
    BooleanSetting,
    StringListSetting,
    FilePathSetting,
    GroupSetting,
)

__all__ = [
    "MainWindow",
    "ScriptTab",
    "TabContext",
    "CollapsibleConsole",
    "DebouncedWriter",
    "PluginInterface",
    "PluginRegistry",
    "SettingItem",
    "SettingType",
    "StringSetting",
    "PasswordSetting",
    "IntegerSetting",
    "FloatSetting",
    "BooleanSetting",
    "StringListSetting",
    "FilePathSetting",
    "GroupSetting",
    "__version__",
]

