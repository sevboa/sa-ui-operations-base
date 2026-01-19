from ..plugin_system import PluginInterface
from ..settings import StringSetting, PasswordSetting, IntegerSetting
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread


class OtherPlugin(PluginInterface):
    """
    Пример плагина - Other / placeholder.
    Простой плагин-заглушка.
    """
    
    def get_key(self):
        return "other"
    
    def get_title(self):
        return "Other / placeholder"
    
    def get_settings(self):
        """Возвращает список настроек для плагина"""
        return [
            StringSetting(
                key="server_url",
                label="URL сервера",
                default_value="http://localhost:8080",
                description="Адрес сервера для подключения"
            ),
            PasswordSetting(
                key="password",
                label="Пароль",
                default_value="",
                description="Пароль для авторизации"
            ),
            IntegerSetting(
                key="timeout",
                label="Таймаут (сек)",
                default_value=30,
                description="Таймаут подключения в секундах"
            ),
            IntegerSetting(
                key="pause_duration",
                label="Пауза выполнения (сек)",
                default_value=5,
                description="Длительность паузы для тестирования остановки скрипта"
            ),
        ]
    
    def create_widget(self, tab_context):
        return OtherWidget(tab_context)
    
    def execute(self, tab_context, console_output_fn, stop_flag=None):
        """
        Выполняет скрипт плагина Other.
        Включает длительную паузу для тестирования функциональности остановки.
        """
        # Получаем настройки через систему настроек
        settings = self.get_settings()
        settings_dict = {s.key: s for s in settings}
        
        server_url = settings_dict.get("server_url", StringSetting("server_url", "URL сервера", "http://localhost:8080")).get_value(tab_context)
        password = settings_dict.get("password", PasswordSetting("password", "Пароль", "")).get_value(tab_context)
        timeout = settings_dict.get("timeout", IntegerSetting("timeout", "Таймаут", 30)).get_value(tab_context)
        pause_duration = settings_dict.get("pause_duration", IntegerSetting("pause_duration", "Пауза", 5)).get_value(tab_context)
        
        console_output_fn("[RUN] Other plugin")
        console_output_fn(f"  Server URL: {server_url}")
        console_output_fn(f"  Password: {'*' * len(password) if password else '(не задан)'}")
        console_output_fn(f"  Timeout: {timeout} сек")
        console_output_fn(f"  Пауза выполнения: {pause_duration} сек")
        console_output_fn("")
        console_output_fn("Начинаю выполнение с паузой...")
        console_output_fn("(Используйте кнопку Stop для прерывания)")
        
        # Выполняем паузу с периодической проверкой флага остановки
        # Используем QThread.msleep() вместо time.sleep() для неблокирующей паузы
        elapsed = 0
        check_interval_ms = 100  # Проверяем каждые 100мс
        
        while elapsed < pause_duration:
            if stop_flag and stop_flag():
                console_output_fn(f"[STOPPED] Выполнение прервано пользователем на {elapsed:.1f} сек")
                return
            
            QThread.msleep(check_interval_ms)
            elapsed += check_interval_ms / 1000.0
            
            # Выводим прогресс каждую секунду
            if int(elapsed) != int(elapsed - check_interval_ms / 1000.0):
                remaining = pause_duration - elapsed
                console_output_fn(f"  Осталось: {remaining:.1f} сек...")
        
        console_output_fn("Пауза завершена")
        console_output_fn("[DONE]")


class OtherWidget(QWidget):
    """
    Виджет настроек для плагина Other.
    """
    def __init__(self, tab_ctx, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Another operation UI placeholder"))
        layout.addStretch(1)

