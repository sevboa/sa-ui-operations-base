from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class PluginInterface(ABC):
    """
    Базовый интерфейс для плагинов скриптов.
    Каждый плагин должен реализовать этот интерфейс.
    """
    
    @abstractmethod
    def get_key(self) -> str:
        """
        Уникальный идентификатор плагина.
        Используется для сохранения настроек и идентификации плагина.
        """
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """
        Отображаемое название плагина.
        Показывается в выпадающем списке операций.
        """
        pass
    
    @abstractmethod
    def create_widget(self, tab_context):
        """
        Создает виджет настроек плагина.
        
        Args:
            tab_context: Контекст вкладки (TabContext) для доступа к настройкам
            
        Returns:
            QWidget: Виджет с настройками плагина
        """
        pass
    
    @abstractmethod
    def execute(self, tab_context, console_output_fn):
        """
        Выполняет скрипт плагина.
        
        Args:
            tab_context: Контекст вкладки (TabContext) для доступа к настройкам
            console_output_fn: Функция для вывода текста в консоль (callable(str))
        """
        pass


class PluginRegistry:
    """
    Реестр плагинов.
    Управляет регистрацией и доступом к плагинам.
    """
    
    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
    
    def register(self, plugin: PluginInterface):
        """
        Регистрирует плагин в реестре.
        
        Args:
            plugin: Экземпляр плагина, реализующий PluginInterface
        """
        key = plugin.get_key()
        if key in self._plugins:
            raise ValueError(f"Plugin with key '{key}' is already registered")
        self._plugins[key] = plugin
    
    def get_plugin(self, key: str) -> Optional[PluginInterface]:
        """
        Получает плагин по ключу.
        
        Args:
            key: Уникальный идентификатор плагина
            
        Returns:
            PluginInterface или None, если плагин не найден
        """
        return self._plugins.get(key)
    
    def get_all_plugins(self) -> List[PluginInterface]:
        """
        Возвращает список всех зарегистрированных плагинов.
        
        Returns:
            Список всех плагинов
        """
        return list(self._plugins.values())
    
    def has_plugin(self, key: str) -> bool:
        """
        Проверяет, зарегистрирован ли плагин с данным ключом.
        
        Args:
            key: Уникальный идентификатор плагина
            
        Returns:
            True, если плагин зарегистрирован
        """
        return key in self._plugins

