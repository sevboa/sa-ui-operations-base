import uuid
from typing import List
from PySide6.QtCore import Qt, QSettings, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar,
    QToolButton, QPushButton, QComboBox, QLineEdit,
    QLabel, QStackedWidget, QPlainTextEdit, QFrame,
    QSizePolicy, QMainWindow, QDoubleSpinBox,
    QSpinBox, QGroupBox
)
from .settings import SettingItem, SettingType


# ----------------------------
# Utilities: debounced settings writes
# ----------------------------
class DebouncedWriter(QObject):
    """
    Collects frequent "save" calls and flushes them after a short delay
    to avoid hammering disk while user drags sliders etc.
    """
    def __init__(self, flush_fn, delay_ms=250, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(flush_fn)

    def schedule(self):
        self._timer.start()


# ----------------------------
# Per-tab context to namespace settings keys
# ----------------------------
class TabContext(QObject):
    def __init__(self, settings: QSettings, tab_id: str, save_scheduler: DebouncedWriter, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.tab_id = tab_id
        self._save_scheduler = save_scheduler

    def key(self, local_key: str) -> str:
        # namespacing under tabs/<tab_id>/...
        return f"tabs/{self.tab_id}/{local_key}"
    
    def global_key(self, local_key: str) -> str:
        # Глобальные настройки (общие для всех вкладок)
        return f"global/{local_key}"

    def save_value(self, local_key: str, value):
        self.settings.setValue(self.key(local_key), value)
        self._save_scheduler.schedule()
    
    def save_global_value(self, local_key: str, value):
        """Сохраняет глобальную настройку (общую для всех вкладок)"""
        self.settings.setValue(self.global_key(local_key), value)
        self._save_scheduler.schedule()
    
    def get_global_value(self, local_key: str, default_value=None, value_type=None):
        """
        Получает значение глобальной настройки (общей для всех вкладок)
        
        Args:
            local_key: Локальный ключ настройки
            default_value: Значение по умолчанию
            value_type: Тип значения (int, str, bool, float)
        
        Returns:
            Значение настройки или значение по умолчанию
        """
        settings_key = self.global_key(local_key)
        if value_type:
            return self.settings.value(settings_key, default_value, type=value_type)
        else:
            return self.settings.value(settings_key, default_value)


# ----------------------------
# Collapsible console widget
# ----------------------------
class CollapsibleConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.btn = QToolButton()
        self.btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn.setArrowType(Qt.RightArrow)
        self.btn.setText("Console output")
        self.btn.setCheckable(True)
        self.btn.toggled.connect(self.set_expanded)

        header.addWidget(self.btn)
        header.addStretch(1)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        self.console.setMaximumBlockCount(5000)  # avoid unbounded memory growth
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        # A subtle top line separator (optional)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        root.addWidget(line)
        root.addLayout(header)
        root.addWidget(self.console)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.console.setVisible(expanded)
        self.btn.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)

    def append_text(self, text: str):
        self.console.appendPlainText(text.rstrip("\n"))


# ----------------------------
# Settings widget - автоматическое создание формы настроек
# ----------------------------
class SettingsWidget(QWidget):
    """
    Виджет для автоматического отображения настроек плагина.
    Создает форму на основе списка SettingItem.
    Поддерживает разделение на общие настройки и настройки конкретного плагина.
    """
    
    def __init__(self, tab_context, plugin_settings_list: List[SettingItem], 
                 global_settings_list: List[SettingItem] = None, parent=None):
        super().__init__(parent)
        self.tab_context = tab_context
        self.plugin_settings_list = plugin_settings_list or []
        self.global_settings_list = global_settings_list or []
        self._widgets = {}  # key -> widget mapping
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Если нет настроек вообще
        if not self.global_settings_list and not self.plugin_settings_list:
            layout.addWidget(QLabel("Нет настроек для этого плагина"))
            layout.addStretch(1)
            return
        
        # Общие настройки (если есть)
        if self.global_settings_list:
            global_group = self._create_settings_group(
                "Общие настройки", 
                self.global_settings_list, 
                is_global=True
            )
            layout.addWidget(global_group)
        
        # Настройки плагина (если есть)
        if self.plugin_settings_list:
            plugin_group = self._create_settings_group(
                "Настройки плагина", 
                self.plugin_settings_list, 
                is_global=False
            )
            layout.addWidget(plugin_group)
        
        layout.addStretch(1)
    
    def _create_settings_group(self, title: str, settings_list: List[SettingItem], is_global: bool):
        """Создает группу настроек с заголовком"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(15, 15, 15, 15)
        
        # Создаем виджеты для каждой настройки
        for setting in settings_list:
            row = QHBoxLayout()
            
            label = QLabel(setting.label + ":")
            label.setMinimumWidth(150)
            row.addWidget(label)
            
            widget = self._create_setting_widget(setting)
            if widget:
                self._widgets[setting.key] = widget
                row.addWidget(widget, 1)
                
                # Восстанавливаем значение
                if is_global:
                    value = self._get_global_value(setting)
                else:
                    value = setting.get_value(self.tab_context)
                self._set_widget_value(widget, setting.setting_type, value)
                
                # Подключаем автосохранение
                if is_global:
                    self._connect_autosave_global(widget, setting)
                else:
                    self._connect_autosave(widget, setting)
            
            if setting.description:
                desc_label = QLabel(setting.description)
                desc_label.setStyleSheet("color: gray; font-size: 9pt;")
                row.addWidget(desc_label)
            
            group_layout.addLayout(row)
        
        return group
    
    def _get_global_value(self, setting: SettingItem):
        """Получает значение глобальной настройки"""
        settings_key = self.tab_context.global_key(f"settings/{setting.key}")
        
        if setting.setting_type == SettingType.INTEGER:
            return self.tab_context.settings.value(settings_key, setting.default_value, type=int)
        elif setting.setting_type == SettingType.FLOAT:
            return self.tab_context.settings.value(settings_key, setting.default_value, type=float)
        elif setting.setting_type == SettingType.STRING:
            return self.tab_context.settings.value(settings_key, setting.default_value, type=str)
        elif setting.setting_type == SettingType.PASSWORD:
            return self.tab_context.settings.value(settings_key, setting.default_value, type=str)
        else:
            return self.tab_context.settings.value(settings_key, setting.default_value)
    
    def _create_setting_widget(self, setting: SettingItem):
        """Создает виджет для настройки в зависимости от типа"""
        if setting.setting_type == SettingType.STRING:
            widget = QLineEdit()
            return widget
        elif setting.setting_type == SettingType.PASSWORD:
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.Password)
            return widget
        elif setting.setting_type == SettingType.INTEGER:
            widget = QSpinBox()
            widget.setRange(-2147483647, 2147483647)  # Qt int range
            return widget
        elif setting.setting_type == SettingType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(-1e10, 1e10)
            widget.setDecimals(6)
            return widget
        return None
    
    def _set_widget_value(self, widget, setting_type: SettingType, value):
        """Устанавливает значение в виджет"""
        if setting_type == SettingType.STRING or setting_type == SettingType.PASSWORD:
            widget.setText(str(value) if value is not None else "")
        elif setting_type == SettingType.INTEGER:
            widget.setValue(int(value) if value is not None else 0)
        elif setting_type == SettingType.FLOAT:
            widget.setValue(float(value) if value is not None else 0.0)
    
    def _connect_autosave(self, widget, setting: SettingItem):
        """Подключает автосохранение при изменении значения (для настроек плагина)"""
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda v: setting.save_value(self.tab_context, v))
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(lambda v: setting.save_value(self.tab_context, v))
    
    def _connect_autosave_global(self, widget, setting: SettingItem):
        """Подключает автосохранение при изменении значения (для глобальных настроек)"""
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))


# ----------------------------
# Worker thread for plugin execution
# ----------------------------
class PluginWorker(QThread):
    """
    Поток для выполнения плагина в фоновом режиме.
    Позволяет не блокировать UI во время выполнения скрипта.
    """
    output = Signal(str)  # Сигнал для вывода текста в консоль
    finished = Signal()   # Сигнал о завершении выполнения
    
    def __init__(self, plugin, tab_context, stop_flag_ref, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.tab_context = tab_context
        self.stop_flag_ref = stop_flag_ref  # Ссылка на флаг остановки
    
    def run(self):
        """Выполняет плагин в отдельном потоке"""
        try:
            # Создаем функцию для безопасного вывода через сигнал
            def safe_output(text: str):
                self.output.emit(text)
            
            # Выполняем плагин
            self.plugin.execute(
                self.tab_context,
                safe_output,
                lambda: self.stop_flag_ref[0]  # Доступ к флагу через список для изменяемости
            )
        except Exception as e:
            self.output.emit(f"[ERROR] {str(e)}")
        finally:
            self.finished.emit()


# ----------------------------
# Single tab widget - базовый универсальный интерфейс
# ----------------------------
class ScriptTab(QWidget):
    """
    Базовый универсальный интерфейс вкладки.
    Содержит только верхнюю панель управления (выбор скрипта, имя, запуск)
    и консоль. Содержимое вкладки загружается через систему плагинов.
    """
    request_rename = Signal(str)  # emitted when user changes tab name

    def __init__(self, settings: QSettings, tab_id: str, plugin_registry, 
                 global_settings: List[SettingItem] = None, parent=None):
        super().__init__(parent)

        # Debounced flush is useful for frequent setting writes.
        self._save_scheduler = DebouncedWriter(self._flush_settings, delay_ms=250, parent=self)
        self.ctx = TabContext(settings, tab_id, self._save_scheduler, parent=self)
        self.plugin_registry = plugin_registry
        self.global_settings = global_settings or []  # Общие настройки для всех плагинов
        
        # Флаг остановки скрипта (используем список для передачи в поток)
        self._stop_flag = [False]
        self._is_running = False
        self._worker_thread = None  # Поток выполнения плагина

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Top bar (первая строчка: выбор скрипта, имя, запуск, остановка, настройки)
        top = QHBoxLayout()
        top.setSpacing(8)

        self.op_combo = QComboBox()
        for plugin in plugin_registry.get_all_plugins():
            self.op_combo.addItem(plugin.get_title(), plugin.get_key())

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Tab name")

        # Индикатор статуса выполнения (квадратик)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("background-color: #808080; border-radius: 2px;")
        self.status_indicator.setToolTip("Статус выполнения")
        
        # Кнопка Run/Stop (меняет текст в зависимости от состояния)
        self.run_stop_btn = QPushButton("Run")
        self.run_stop_btn.setDefault(True)
        
        # Кнопка настроек (шестеренка)
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙")
        self.settings_btn.setToolTip("Настройки")
        self.settings_btn.setCheckable(True)
        self.settings_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        top.addWidget(QLabel("Operation:"))
        top.addWidget(self.op_combo, 2)
        top.addWidget(QLabel("Name:"))
        top.addWidget(self.name_edit, 2)
        top.addWidget(self.status_indicator, 0)
        top.addWidget(self.run_stop_btn, 0)
        top.addWidget(self.settings_btn, 0)

        # --- Main content area = stacked widgets для плагинов и настроек
        # Двойной стек: первый уровень - плагин/настройки, второй - виджеты плагинов
        self.main_stack = QStackedWidget()
        
        # Виджет плагина (может быть заменен на виджет настроек)
        self.plugin_stack = QStackedWidget()
        self._op_key_to_index = {}
        
        # Виджет настроек
        self.settings_widget = None
        
        # Создаем виджеты плагинов
        for idx, plugin in enumerate(plugin_registry.get_all_plugins()):
            w = plugin.create_widget(self.ctx)
            self.plugin_stack.addWidget(w)
            self._op_key_to_index[plugin.get_key()] = idx
        
        # Добавляем виджет плагина в главный стек
        self.main_stack.addWidget(self.plugin_stack)
        
        # Виджет настроек будет добавлен динамически при первом переключении

        # --- Console at bottom (collapsible)
        self.console = CollapsibleConsole()

        root.addLayout(top)
        root.addWidget(self.main_stack, 1)
        root.addWidget(self.console, 0)

        # Restore per-tab state
        self._restore()

        # Hook up signals for auto-save
        self.op_combo.currentIndexChanged.connect(self._on_operation_changed)
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.run_stop_btn.clicked.connect(self._on_run_stop)
        self.settings_btn.toggled.connect(self._on_settings_toggled)

    def _restore(self):
        # Name
        name = self.ctx.settings.value(self.ctx.key("meta/name"), "New tab", type=str)
        self.name_edit.setText(name)

        # Operation selection
        plugins = self.plugin_registry.get_all_plugins()
        default_key = plugins[0].get_key() if plugins else ""
        op_key = self.ctx.settings.value(self.ctx.key("meta/operation"), default_key, type=str)
        combo_index = self.op_combo.findData(op_key)
        if combo_index < 0:
            combo_index = 0
            op_key = default_key
        self.op_combo.setCurrentIndex(combo_index)

        # Apply to stack
        self.plugin_stack.setCurrentIndex(self._op_key_to_index.get(op_key, 0))
        
        # Всегда начинаем с основного окна плагина (не запоминаем состояние кнопки настроек)
        self.settings_btn.setChecked(False)
        self.main_stack.setCurrentIndex(0)

        # Console expanded? (по умолчанию открыта)
        expanded = self.ctx.settings.value(self.ctx.key("meta/console_expanded"), True, type=bool)
        self.console.btn.setChecked(expanded)
        self.console.set_expanded(expanded)

        # Keep console expanded state in sync
        self.console.btn.toggled.connect(lambda v: self.ctx.save_value("meta/console_expanded", v))

    def _on_operation_changed(self):
        op_key = self.op_combo.currentData()
        self.plugin_stack.setCurrentIndex(self._op_key_to_index.get(op_key, 0))
        self.ctx.save_value("meta/operation", op_key)
        
        # Обновляем виджет настроек при смене плагина
        if self.settings_btn.isChecked():
            self._update_settings_widget()

    def _on_name_changed(self, text: str):
        self.ctx.save_value("meta/name", text)
        self.request_rename.emit(text)

    def _on_run_stop(self):
        """Обработчик кнопки Run/Stop - переключает между запуском и остановкой"""
        if self._is_running:
            # Останавливаем выполнение
            self._stop_flag[0] = True
            self.console.append_text("[STOP] Остановка скрипта...")
        else:
            # Запускаем выполнение
            self._start_execution()
    
    def _start_execution(self):
        """Запускает выполнение скрипта в отдельном потоке"""
        # Получаем текущий плагин
        op_key = self.op_combo.currentData()
        
        plugin = self.plugin_registry.get_plugin(op_key)
        if plugin:
            self._is_running = True
            self._stop_flag[0] = False
            
            # Обновляем UI для состояния "выполняется"
            self._set_running_state(True)
            
            # Очищаем консоль перед запуском
            self.console.console.clear()
            
            # Создаем и настраиваем поток выполнения
            self._worker_thread = PluginWorker(plugin, self.ctx, self._stop_flag, self)
            
            # Подключаем сигналы потока
            self._worker_thread.output.connect(self.console.append_text)
            self._worker_thread.finished.connect(self._on_execution_finished)
            
            # Запускаем поток
            self._worker_thread.start()
        else:
            self.console.append_text(f"[ERROR] Plugin '{op_key}' not found")
    
    def _on_execution_finished(self):
        """Вызывается когда выполнение плагина завершено"""
        self._is_running = False
        # Обновляем UI для состояния "остановлено"
        self._set_running_state(False)
        
        # Очищаем ссылку на поток
        if self._worker_thread:
            self._worker_thread.wait()  # Ждем завершения потока
            self._worker_thread.deleteLater()  # Удаляем поток
            self._worker_thread = None
    
    def cleanup(self):
        """Очистка ресурсов при закрытии вкладки"""
        if self._is_running and self._worker_thread:
            # Останавливаем выполнение
            self._stop_flag[0] = True
            # Ждем завершения потока (максимум 2 секунды)
            if self._worker_thread.isRunning():
                self._worker_thread.wait(2000)
            if self._worker_thread.isRunning():
                # Принудительно завершаем поток если он не завершился
                self._worker_thread.terminate()
                self._worker_thread.wait()
            self._worker_thread.deleteLater()
            self._worker_thread = None
    
    def _set_running_state(self, running: bool):
        """Обновляет UI в зависимости от состояния выполнения"""
        if running:
            # Состояние "выполняется"
            self.run_stop_btn.setText("Stop")
            self.run_stop_btn.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; }")
            self.status_indicator.setStyleSheet("background-color: #4caf50; border-radius: 2px;")
            self.status_indicator.setToolTip("Выполняется")
            self.op_combo.setEnabled(False)
        else:
            # Состояние "остановлено"
            self.run_stop_btn.setText("Run")
            self.run_stop_btn.setStyleSheet("")  # Возвращаем стандартный стиль
            self.status_indicator.setStyleSheet("background-color: #808080; border-radius: 2px;")
            self.status_indicator.setToolTip("Остановлено")
            self.op_combo.setEnabled(True)
    
    def _on_settings_toggled(self, checked: bool):
        """Переключает между виджетом плагина и настройками"""
        # Не сохраняем состояние кнопки - всегда начинаем с основного окна плагина
        
        if checked:
            self._update_settings_widget()
            if self.settings_widget:
                # Удаляем старый виджет настроек, если он есть
                old_index = self.main_stack.indexOf(self.settings_widget)
                if old_index >= 0:
                    old_widget = self.main_stack.widget(old_index)
                    self.main_stack.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                # Добавляем новый виджет настроек
                self.main_stack.addWidget(self.settings_widget)
                self.main_stack.setCurrentWidget(self.settings_widget)
        else:
            self.main_stack.setCurrentWidget(self.plugin_stack)
    
    def _update_settings_widget(self):
        """Обновляет виджет настроек для текущего плагина"""
        op_key = self.op_combo.currentData()
        plugin = self.plugin_registry.get_plugin(op_key)
        
        if plugin:
            plugin_settings_list = plugin.get_settings()
            self.settings_widget = SettingsWidget(
                self.ctx, 
                plugin_settings_list, 
                self.global_settings
            )
        else:
            self.settings_widget = SettingsWidget(self.ctx, [], self.global_settings)

    def _flush_settings(self):
        # QSettings writes are generally buffered; sync ensures physical flush.
        # Use sparingly; that's why debounced.
        self.ctx.settings.sync()


# ----------------------------
# Main window with tabs + add tab button
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self, plugin_registry, organization_name: str, application_name: str, 
                 global_settings: List[SettingItem] = None):
        """
        Создает главное окно приложения.
        
        Args:
            plugin_registry: Реестр плагинов (PluginRegistry)
            organization_name: Имя организации (используется для изоляции настроек)
            application_name: Имя приложения (используется для изоляции настроек)
            global_settings: Список общих настроек для всех плагинов (опционально)
            
        Пример:
            from sa_ui_operations.settings import StringSetting, IntegerSetting
            
            global_settings = [
                StringSetting("api_base_url", "Базовый URL API", "https://api.example.com"),
                IntegerSetting("timeout", "Таймаут по умолчанию (сек)", 30),
            ]
            window = MainWindow(registry, "MyCompany", "MyApp", global_settings)
        """
        super().__init__()

        if not organization_name or not application_name:
            raise ValueError(
                "organization_name и application_name обязательны для изоляции настроек между приложениями. "
                "Пример: MainWindow(registry, 'MyCompany', 'MyApp')"
            )

        self.settings = QSettings(organization_name, application_name)
        self.global_settings = global_settings or []  # Общие настройки для всех плагинов
        self._plus_tab = None
        self._handling_plus_click = False
        self.plugin_registry = plugin_registry

        self.setWindowTitle("Universal Scripts UI")
        self.resize(1100, 700)

        # Central: top row with tabs and [+]
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_current_tab_changed)

        root.addWidget(self.tabs, 1)

        # Menu actions (optional)
        act_new = QAction("New Tab", self)
        act_new.triggered.connect(self._create_tab)
        self.addAction(act_new)
        act_new.setShortcut("Ctrl+T")

        # Restore or create default tabs
        self._restore_tabs()
        self._ensure_plus_tab()

        # Restore window geometry
        geom = self.settings.value("window/geometry")
        if geom is not None:
            self.restoreGeometry(geom)

    def closeEvent(self, event):
        # Save window geometry
        self.settings.setValue("window/geometry", self.saveGeometry())
        self._persist_tabs_list()
        self.settings.sync()
        super().closeEvent(event)

    def _restore_tabs(self):
        tab_ids = self.settings.value("tabs/_order", [], type=list)
        if not tab_ids:
            # Create one default tab
            self._create_tab()
            return

        for tab_id in tab_ids:
            self._create_tab(tab_id=tab_id, focus=False)

        # restore active tab index
        idx = self.settings.value("tabs/_active_index", 0, type=int)
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)

    def _on_active_tab_changed(self, idx: int):
        self.settings.setValue("tabs/_active_index", idx)

    def _plus_index(self) -> int:
        if self._plus_tab is None:
            return -1
        return self.tabs.indexOf(self._plus_tab)

    def _is_plus_index(self, idx: int) -> bool:
        return idx >= 0 and idx == self._plus_index()

    def _ensure_plus_tab(self):
        if self._plus_tab is None:
            self._plus_tab = QWidget()
            self._plus_tab.setObjectName("PlusTab")
            # Keep it minimal; it's never meant to be "real" content.
            QVBoxLayout(self._plus_tab).addStretch(1)

        idx = self._plus_index()
        if idx < 0:
            idx = self.tabs.addTab(self._plus_tab, "+")
        # Hide close button for the [+] tab (QTabWidget puts it on the tabBar)
        bar = self.tabs.tabBar()
        bar.setTabButton(idx, QTabBar.LeftSide, None)
        bar.setTabButton(idx, QTabBar.RightSide, None)

    def _on_current_tab_changed(self, idx: int):
        # If user clicked the [+] tab -> create a new real tab and switch to it.
        if self._handling_plus_click:
            return
        if self._is_plus_index(idx):
            self._handling_plus_click = True
            try:
                new_idx = self._create_tab(focus=False)
                if new_idx is not None:
                    self.tabs.setCurrentIndex(new_idx)
            finally:
                self._handling_plus_click = False
            return

        # Persist active index among real tabs (exclude [+] if it exists)
        plus = self._plus_index()
        if plus >= 0 and idx > plus:
            # shouldn't happen, but be safe
            idx = plus - 1
        self._on_active_tab_changed(idx)

    def _create_tab(self, tab_id: str | None = None, focus=True):
        if tab_id is None:
            tab_id = uuid.uuid4().hex

        tab = ScriptTab(self.settings, tab_id, self.plugin_registry, self.global_settings)
        tab.request_rename.connect(lambda name, t=tab: self._rename_tab_widget(t, name))

        # initial title from settings
        title = self.settings.value(f"tabs/{tab_id}/meta/name", "New tab", type=str)
        plus = self._plus_index()
        insert_at = plus if plus >= 0 else self.tabs.count()
        i = self.tabs.insertTab(insert_at, tab, title)
        self._ensure_plus_tab()

        if focus:
            self.tabs.setCurrentIndex(i)

        self._persist_tabs_list()
        return i

    def _rename_tab_widget(self, tab_widget: QWidget, name: str):
        idx = self.tabs.indexOf(tab_widget)
        if idx >= 0:
            self.tabs.setTabText(idx, name.strip() or "Unnamed")

    def _close_tab(self, index: int):
        if self._is_plus_index(index):
            return
        w = self.tabs.widget(index)
        
        # Очищаем ресурсы вкладки (останавливаем потоки если есть)
        if hasattr(w, 'cleanup'):
            w.cleanup()

        self.tabs.removeTab(index)
        w.deleteLater()

        # Optional: decide whether to delete settings for closed tab.
        # I recommend NOT deleting by default (safer), but you can implement cleanup.
        # If you want cleanup: iterate keys under f"tabs/{tab_id}/" and remove.

        self._persist_tabs_list()
        self._ensure_plus_tab()

        if self.tabs.count() == 0:
            self._create_tab()

    def _persist_tabs_list(self):
        # Persist order by reading current widgets' tab_id
        ids = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w is self._plus_tab:
                continue
            if hasattr(w, "ctx"):
                ids.append(w.ctx.tab_id)
        self.settings.setValue("tabs/_order", ids)

        # Keep active index
        idx = self.tabs.currentIndex()
        if self._is_plus_index(idx):
            # store last real tab
            idx = max(0, idx - 1)
        self.settings.setValue("tabs/_active_index", idx)

