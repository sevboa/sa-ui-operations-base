"""
Система настроек для плагинов.
Базовые классы для определения настроек плагинов.
"""
from abc import ABC
from enum import Enum
from typing import Any, Optional


class SettingType(Enum):
    """Типы настроек"""
    STRING = "string"
    PASSWORD = "password"
    INTEGER = "integer"
    FLOAT = "float"


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
        
        if self.setting_type == SettingType.INTEGER:
            return tab_context.settings.value(settings_key, self.default_value, type=int)
        elif self.setting_type == SettingType.FLOAT:
            return tab_context.settings.value(settings_key, self.default_value, type=float)
        elif self.setting_type == SettingType.STRING:
            return tab_context.settings.value(settings_key, self.default_value, type=str)
        elif self.setting_type == SettingType.PASSWORD:
            return tab_context.settings.value(settings_key, self.default_value, type=str)
        else:
            return tab_context.settings.value(settings_key, self.default_value)
    
    def save_value(self, tab_context, value: Any):
        """
        Сохраняет значение настройки в контекст вкладки.
        
        Args:
            tab_context: Контекст вкладки (TabContext)
            value: Значение для сохранения
        """
        settings_key = tab_context.key(f"settings/{self.key}")
        tab_context.save_value(f"settings/{self.key}", value)


class StringSetting(SettingItem):
    """Настройка типа строка"""
    
    def __init__(self, key: str, label: str, default_value: str = "", description: Optional[str] = None):
        super().__init__(key, label, SettingType.STRING, default_value, description)


class PasswordSetting(SettingItem):
    """Настройка типа пароль (строка с маскированием)"""
    
    def __init__(self, key: str, label: str, default_value: str = "", description: Optional[str] = None):
        super().__init__(key, label, SettingType.PASSWORD, default_value, description)


class IntegerSetting(SettingItem):
    """Настройка типа целое число"""
    
    def __init__(self, key: str, label: str, default_value: int = 0, description: Optional[str] = None):
        super().__init__(key, label, SettingType.INTEGER, default_value, description)


class FloatSetting(SettingItem):
    """Настройка типа число с плавающей точкой"""
    
    def __init__(self, key: str, label: str, default_value: float = 0.0, description: Optional[str] = None):
        super().__init__(key, label, SettingType.FLOAT, default_value, description)



