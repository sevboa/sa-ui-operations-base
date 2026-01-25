"""
Система настроек для плагинов.
Базовые классы для определения настроек плагинов.
"""
from abc import ABC
from enum import Enum
from typing import Any, Optional, List


class SettingType(Enum):
    """Типы настроек"""
    STRING = "string"
    PASSWORD = "password"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING_LIST = "string_list"
    FILE_PATH = "file_path"
    GROUP = "group"


class SettingItem(ABC):
    """
    Базовый класс для настройки плагина.
    Каждая настройка должна наследоваться от этого класса.
    """
    
    def __init__(
        self,
        key: str,
        label: str,
        setting_type: SettingType,
        default_value: Any = None,
        description: Optional[str] = None
    ):
        """
        Args:
            key: Уникальный ключ настройки (используется для сохранения в базе)
            label: Отображаемое имя настройки в форме
            setting_type: Тип настройки (SettingType)
            default_value: Значение по умолчанию
            description: Описание настройки (опционально)
        """
        self.key = key
        self.label = label
        self.setting_type = setting_type
        self.default_value = default_value
        self.description = description
    
    def get_value(self, tab_context) -> Any:
        """
        Получает значение настройки из контекста вкладки.
        
        Args:
            tab_context: Контекст вкладки (TabContext)
            
        Returns:
            Значение настройки или значение по умолчанию
        """
        settings_key = tab_context.key(f"settings/{self.key}")
        type_map = {
            SettingType.INTEGER: int,
            SettingType.FLOAT: float,
            SettingType.STRING: str,
            SettingType.PASSWORD: str,
            SettingType.BOOLEAN: bool,
            SettingType.STRING_LIST: str,
            SettingType.FILE_PATH: str,
        }
        value_type = type_map.get(self.setting_type)
        if value_type:
            return tab_context.settings.value(settings_key, self.default_value, type=value_type)
        return tab_context.settings.value(settings_key, self.default_value)
    
    def save_value(self, tab_context, value: Any):
        """
        Сохраняет значение настройки в контекст вкладки.
        
        Args:
            tab_context: Контекст вкладки (TabContext)
            value: Значение для сохранения
        """
        tab_context.save_value(f"settings/{self.key}", value)


class StringSetting(SettingItem):
    """Настройка типа строка"""
    
    def __init__(
        self,
        key: str,
        label: str,
        default_value: str = "",
        description: Optional[str] = None,
        regex_pattern: Optional[str] = None,
    ):
        super().__init__(key, label, SettingType.STRING, default_value, description)
        self.regex_pattern = regex_pattern


class PasswordSetting(SettingItem):
    """Настройка типа пароль (строка с маскированием)"""
    
    def __init__(self, key: str, label: str, default_value: str = "", description: Optional[str] = None):
        super().__init__(key, label, SettingType.PASSWORD, default_value, description)


class IntegerSetting(SettingItem):
    """Настройка типа целое число"""
    
    def __init__(
        self,
        key: str,
        label: str,
        default_value: int = 0,
        description: Optional[str] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        super().__init__(key, label, SettingType.INTEGER, default_value, description)
        self.min_value = min_value
        self.max_value = max_value


class FloatSetting(SettingItem):
    """Настройка типа число с плавающей точкой"""
    
    def __init__(
        self,
        key: str,
        label: str,
        default_value: float = 0.0,
        description: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        super().__init__(key, label, SettingType.FLOAT, default_value, description)
        self.min_value = min_value
        self.max_value = max_value


class BooleanSetting(SettingItem):
    """Настройка типа булево значение"""
    
    def __init__(self, key: str, label: str, default_value: bool = False, description: Optional[str] = None):
        super().__init__(key, label, SettingType.BOOLEAN, default_value, description)


class StringListSetting(SettingItem):
    """Настройка выбора значения из списка строк"""
    
    def __init__(
        self,
        key: str,
        label: str,
        options: List[str],
        default_value: Optional[str] = None,
        description: Optional[str] = None,
    ):
        if default_value is None and options:
            default_value = options[0]
        self.options = options
        super().__init__(key, label, SettingType.STRING_LIST, default_value, description)


class FilePathSetting(SettingItem):
    """Настройка выбора пути к файлу"""
    
    def __init__(
        self,
        key: str,
        label: str,
        default_value: str = "",
        description: Optional[str] = None,
    ):
        super().__init__(key, label, SettingType.FILE_PATH, default_value, description)


class GroupSetting(SettingItem):
    """Настройка-группа с дочерними настройками и наборами значений по режимам"""

    def __init__(
        self,
        key: str,
        label: str,
        modes: List[str],
        group_settings: List[SettingItem],
        default_mode: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.modes = modes
        self.group_settings = group_settings
        self.default_mode = default_mode or (modes[0] if modes else "default")
        super().__init__(key, label, SettingType.GROUP, self.default_mode, description)

    def get_active_mode(self, tab_context, is_global: bool = False) -> str:
        return tab_context.get_group_mode(self.key, self.default_mode, is_global=is_global)

    def get_values_for_mode(self, tab_context, mode: str, is_global: bool = False):
        values = {}
        for setting in self.group_settings:
            value_type = self._value_type(setting)
            values[setting.key] = tab_context.get_grouped_value(
                self.key,
                mode,
                setting.key,
                setting.default_value,
                value_type=value_type,
                is_global=is_global,
            )
        return values

    def get_active_values(self, tab_context, is_global: bool = False):
        return self.get_values_for_mode(
            tab_context,
            self.get_active_mode(tab_context, is_global=is_global),
            is_global=is_global,
        )

    def get_all_values(self, tab_context, is_global: bool = False):
        return {
            mode: self.get_values_for_mode(tab_context, mode, is_global=is_global)
            for mode in self.modes
        }

    @staticmethod
    def _value_type(setting: SettingItem):
        type_map = {
            SettingType.INTEGER: int,
            SettingType.FLOAT: float,
            SettingType.STRING: str,
            SettingType.PASSWORD: str,
            SettingType.BOOLEAN: bool,
            SettingType.STRING_LIST: str,
            SettingType.FILE_PATH: str,
        }
        return type_map.get(setting.setting_type)



