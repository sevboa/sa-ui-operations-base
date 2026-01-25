import re
import uuid
from typing import List, Tuple, Dict
from PySide6.QtCore import Qt, QSettings, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar,
    QToolButton, QPushButton, QComboBox, QLineEdit,
    QLabel, QStackedWidget, QPlainTextEdit, QFrame,
    QSizePolicy, QMainWindow, QDoubleSpinBox,
    QSpinBox, QGroupBox, QFileDialog, QCheckBox
)
from .settings import SettingItem, SettingType, GroupSetting


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

    def group_mode_key(self, group_key: str, is_global: bool) -> str:
        local_key = f"settings_groups_meta/{group_key}/mode"
        return self.global_key(local_key) if is_global else self.key(local_key)

    def get_group_mode(self, group_key: str, default_mode: str, is_global: bool = False) -> str:
        return self.settings.value(self.group_mode_key(group_key, is_global), default_mode, type=str)

    def save_group_mode(self, group_key: str, mode: str, is_global: bool = False):
        local_key = f"settings_groups_meta/{group_key}/mode"
        if is_global:
            self.save_global_value(local_key, mode)
        else:
            self.save_value(local_key, mode)

    def grouped_value_key(self, group_key: str, mode: str, setting_key: str, is_global: bool) -> str:
        local_key = f"settings_groups/{group_key}/{mode}/{setting_key}"
        return self.global_key(local_key) if is_global else self.key(local_key)

    def get_grouped_value(
        self,
        group_key: str,
        mode: str,
        setting_key: str,
        default_value,
        value_type=None,
        is_global: bool = False,
    ):
        settings_key = self.grouped_value_key(group_key, mode, setting_key, is_global)
        if value_type:
            return self.settings.value(settings_key, default_value, type=value_type)
        return self.settings.value(settings_key, default_value)

    def save_grouped_value(self, group_key: str, mode: str, setting_key: str, value, is_global: bool = False):
        local_key = f"settings_groups/{group_key}/{mode}/{setting_key}"
        if is_global:
            self.save_global_value(local_key, value)
        else:
            self.save_value(local_key, value)

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
    TEXT_MIN_WIDTH = 100
    TEXT_MAX_WIDTH = 500
    TEXT_PREFERRED_WIDTH = 500
    FILE_BUTTON_WIDTH = 28
    FILE_BUTTON_SPACING = 6
    COMBOBOX_MIN_WIDTH = 100

    class _PreferredLineEdit(QLineEdit):
        def __init__(self, preferred_width: int, min_width: int, parent=None):
            super().__init__(parent)
            self._preferred_width = preferred_width
            self._min_width = min_width

        def sizeHint(self):
            hint = super().sizeHint()
            hint.setWidth(self._preferred_width)
            return hint

        def minimumSizeHint(self):
            hint = super().minimumSizeHint()
            hint.setWidth(self._min_width)
            return hint
    
    def __init__(
        self,
        tab_context,
        plugin_settings_list: List[SettingItem],
        global_settings_list: List[SettingItem] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.tab_context = tab_context
        self.plugin_settings_list = plugin_settings_list or []
        self.global_settings_list = global_settings_list or []
        self._widgets = {}  # key -> widget mapping
        self._group_widgets: Dict[Tuple[str, str], QWidget] = {}
        
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
            if isinstance(setting, GroupSetting):
                self._add_group_setting(group_layout, setting, is_global)
                continue

            row = QHBoxLayout()
            
            label = QLabel(setting.label + ":")
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            row.addWidget(label)
            
            widget = self._create_setting_widget(setting)
            if widget:
                self._widgets[setting.key] = widget
                row.addWidget(widget)
                
                # Восстанавливаем значение
                if is_global:
                    value = self._get_global_value(setting)
                else:
                    value = setting.get_value(self.tab_context)
                self._set_widget_value(widget, setting.setting_type, value)
                self._apply_string_validation_state(widget, setting)
                
                # Подключаем автосохранение
                if is_global:
                    self._connect_autosave_global(widget, setting)
                else:
                    self._connect_autosave(widget, setting)
            
            if setting.description:
                row.addWidget(self._create_info_label(setting.description))

            row.addStretch(1)
            
            group_layout.addLayout(row)
        
        return group

    def _add_group_setting(self, group_layout: QVBoxLayout, setting: GroupSetting, is_global: bool):
        group_key = setting.key

        header = QHBoxLayout()
        label = QLabel(setting.label + ":")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(label)

        combo = QComboBox()
        for mode in setting.modes:
            combo.addItem(mode)
        header.addWidget(combo)

        if setting.description:
            header.addWidget(self._create_info_label(setting.description))

        header.addStretch(1)
        group_layout.addLayout(header)

        default_mode = setting.default_mode
        selected_mode = self.tab_context.get_group_mode(group_key, default_mode, is_global=is_global)
        if setting.modes:
            if selected_mode not in setting.modes:
                selected_mode = setting.modes[0]
        combo.setCurrentText(selected_mode)
        self.tab_context.save_group_mode(group_key, selected_mode, is_global=is_global)

        combo.currentTextChanged.connect(
            lambda mode: self._on_group_changed(setting, is_global, mode)
        )

        for child in setting.group_settings:
            row = QHBoxLayout()
            row.addSpacing(12)
            child_label = QLabel(child.label + ":")
            child_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            row.addWidget(child_label)

            widget = self._create_setting_widget(child)
            if widget:
                self._group_widgets[(group_key, child.key)] = widget
                row.addWidget(widget)

                value = self._get_grouped_value(child, group_key, selected_mode, is_global)
                self._set_widget_value(widget, child.setting_type, value)
                self._apply_string_validation_state(widget, child)

                self._connect_autosave_grouped(widget, child, group_key, is_global, default_mode)

            if child.description:
                row.addWidget(self._create_info_label(child.description))

            row.addStretch(1)
            group_layout.addLayout(row)

    def _on_group_changed(self, setting: GroupSetting, is_global: bool, mode: str):
        group_key = setting.key
        self.tab_context.save_group_mode(group_key, mode, is_global=is_global)
        for child in setting.group_settings:
            widget = self._group_widgets.get((group_key, child.key))
            if widget:
                value = self._get_grouped_value(child, group_key, mode, is_global)
                self._set_widget_value(widget, child.setting_type, value)
                self._apply_string_validation_state(widget, child)
    
    def _get_global_value(self, setting: SettingItem):
        """Получает значение глобальной настройки"""
        settings_key = self.tab_context.global_key(f"settings/{setting.key}")
        type_map = {
            SettingType.INTEGER: int,
            SettingType.FLOAT: float,
            SettingType.STRING: str,
            SettingType.PASSWORD: str,
            SettingType.BOOLEAN: bool,
            SettingType.STRING_LIST: str,
            SettingType.FILE_PATH: str,
        }
        value_type = type_map.get(setting.setting_type)
        if value_type:
            return self.tab_context.settings.value(settings_key, setting.default_value, type=value_type)
        return self.tab_context.settings.value(settings_key, setting.default_value)

    def _get_grouped_value(self, setting: SettingItem, group_key: str, mode: str, is_global: bool):
        value_type = self._setting_value_type(setting)
        return self.tab_context.get_grouped_value(
            group_key,
            mode,
            setting.key,
            setting.default_value,
            value_type=value_type,
            is_global=is_global,
        )

    def _save_grouped_value(self, setting: SettingItem, group_key: str, mode: str, value, is_global: bool):
        self.tab_context.save_grouped_value(group_key, mode, setting.key, value, is_global=is_global)
    
    def _create_setting_widget(self, setting: SettingItem):
        """Создает виджет для настройки в зависимости от типа"""
        if setting.setting_type == SettingType.STRING:
            return self._create_text_input()
        elif setting.setting_type == SettingType.PASSWORD:
            return self._create_text_input(is_password=True)
        elif setting.setting_type == SettingType.INTEGER:
            widget = QSpinBox()
            min_value = getattr(setting, "min_value", None)
            max_value = getattr(setting, "max_value", None)
            widget.setRange(
                min_value if min_value is not None else -2147483647,
                max_value if max_value is not None else 2147483647
            )
            widget.setFixedWidth(self._spinbox_width(widget, max_value))
            return widget
        elif setting.setting_type == SettingType.FLOAT:
            widget = QDoubleSpinBox()
            min_value = getattr(setting, "min_value", None)
            max_value = getattr(setting, "max_value", None)
            widget.setRange(
                min_value if min_value is not None else -1e10,
                max_value if max_value is not None else 1e10
            )
            widget.setDecimals(6)
            widget.setFixedWidth(self._spinbox_width(widget, max_value))
            return widget
        elif setting.setting_type == SettingType.BOOLEAN:
            widget = QCheckBox()
            return widget
        elif setting.setting_type == SettingType.STRING_LIST:
            widget = QComboBox()
            options = getattr(setting, "options", [])
            for option in options:
                widget.addItem(option)
            if not options:
                widget.setEnabled(False)
            widget.setFixedWidth(self._combobox_width(widget, options))
            return widget
        elif setting.setting_type == SettingType.FILE_PATH:
            return self._create_file_path_widget()
        return None
    
    def _set_widget_value(self, widget, setting_type: SettingType, value):
        """Устанавливает значение в виджет"""
        if setting_type == SettingType.STRING or setting_type == SettingType.PASSWORD:
            widget.setText(str(value) if value is not None else "")
        elif setting_type == SettingType.INTEGER:
            widget.setValue(int(value) if value is not None else 0)
        elif setting_type == SettingType.FLOAT:
            widget.setValue(float(value) if value is not None else 0.0)
        elif setting_type == SettingType.BOOLEAN and isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif setting_type == SettingType.STRING_LIST and isinstance(widget, QComboBox):
            text_value = "" if value is None else str(value)
            index = widget.findText(text_value)
            if index == -1 and widget.count() > 0:
                index = 0
            if index >= 0:
                widget.setCurrentIndex(index)
        elif setting_type == SettingType.FILE_PATH:
            line_edit = self._get_file_path_edit(widget)
            if line_edit:
                line_edit.setText(str(value) if value is not None else "")
    
    def _connect_autosave(self, widget, setting: SettingItem):
        """Подключает автосохранение при изменении значения (для настроек плагина)"""
        if isinstance(widget, QLineEdit):
            if setting.setting_type == SettingType.STRING and getattr(setting, "regex_pattern", None):
                def _on_text_changed(v: str):
                    if self._apply_string_validation_state(widget, setting):
                        setting.save_value(self.tab_context, v)
                widget.textChanged.connect(_on_text_changed)
            else:
                widget.textChanged.connect(lambda v: setting.save_value(self.tab_context, v))
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(lambda v: setting.save_value(self.tab_context, v))
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(lambda v: setting.save_value(self.tab_context, bool(v)))
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda v: setting.save_value(self.tab_context, v))
        else:
            line_edit = self._get_file_path_edit(widget)
            if line_edit:
                line_edit.textChanged.connect(lambda v: setting.save_value(self.tab_context, v))

    def _connect_autosave_grouped(
        self,
        widget,
        setting: SettingItem,
        group_key: str,
        is_global: bool,
        default_mode: str,
    ):
        def current_mode() -> str:
            return self.tab_context.get_group_mode(group_key, default_mode, is_global=is_global)

        if isinstance(widget, QLineEdit):
            if setting.setting_type == SettingType.STRING and getattr(setting, "regex_pattern", None):
                def _on_text_changed(v: str):
                    if self._apply_string_validation_state(widget, setting):
                        self._save_grouped_value(setting, group_key, current_mode(), v, is_global)
                widget.textChanged.connect(_on_text_changed)
            else:
                widget.textChanged.connect(
                    lambda v: self._save_grouped_value(setting, group_key, current_mode(), v, is_global)
                )
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(
                lambda v: self._save_grouped_value(setting, group_key, current_mode(), v, is_global)
            )
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(
                lambda v: self._save_grouped_value(setting, group_key, current_mode(), bool(v), is_global)
            )
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(
                lambda v: self._save_grouped_value(setting, group_key, current_mode(), v, is_global)
            )
        else:
            line_edit = self._get_file_path_edit(widget)
            if line_edit:
                line_edit.textChanged.connect(
                    lambda v: self._save_grouped_value(setting, group_key, current_mode(), v, is_global)
                )
    
    def _connect_autosave_global(self, widget, setting: SettingItem):
        """Подключает автосохранение при изменении значения (для глобальных настроек)"""
        if isinstance(widget, QLineEdit):
            if setting.setting_type == SettingType.STRING and getattr(setting, "regex_pattern", None):
                def _on_text_changed(v: str):
                    if self._apply_string_validation_state(widget, setting):
                        self.tab_context.save_global_value(f"settings/{setting.key}", v)
                widget.textChanged.connect(_on_text_changed)
            else:
                widget.textChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", bool(v)))
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))
        else:
            line_edit = self._get_file_path_edit(widget)
            if line_edit:
                line_edit.textChanged.connect(lambda v: self.tab_context.save_global_value(f"settings/{setting.key}", v))

    def _apply_string_validation_state(self, widget, setting: SettingItem) -> bool:
        """Проверяет строку по regex и обновляет подсветку"""
        if not isinstance(widget, QLineEdit):
            return True
        if setting.setting_type != SettingType.STRING:
            return True
        pattern = getattr(setting, "regex_pattern", None)
        if not pattern:
            widget.setStyleSheet("")
            return True
        try:
            is_valid = re.fullmatch(pattern, widget.text() or "") is not None
        except re.error:
            is_valid = True
        if is_valid:
            widget.setStyleSheet("")
        else:
            widget.setStyleSheet("background-color: #ffdddd;")
        return is_valid

    def _get_file_path_edit(self, widget):
        if isinstance(widget, QWidget):
            line_edit = widget.property("line_edit")
            if isinstance(line_edit, QLineEdit):
                return line_edit
        return None

    def _setting_value_type(self, setting: SettingItem):
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

    def _spinbox_width(self, widget, max_value) -> int:
        if max_value is None:
            text = "0" * 5
        else:
            text = str(max_value)
        metrics = widget.fontMetrics()
        return metrics.horizontalAdvance(text) + 40

    def _combobox_width(self, widget, options) -> int:
        metrics = widget.fontMetrics()
        if not options:
            return self.COMBOBOX_MIN_WIDTH
        longest = max(options, key=len)
        return metrics.horizontalAdvance(longest) + 44

    def _create_text_input(self, is_password: bool = False) -> QLineEdit:
        widget = self._PreferredLineEdit(self.TEXT_PREFERRED_WIDTH, self.TEXT_MIN_WIDTH)
        if is_password:
            widget.setEchoMode(QLineEdit.Password)
        widget.setMinimumWidth(self.TEXT_MIN_WIDTH)
        widget.setMaximumWidth(self.TEXT_MAX_WIDTH)
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        return widget

    def _create_file_path_widget(self) -> QWidget:
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(self.FILE_BUTTON_SPACING)
        line_edit = self._create_text_input()
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(self.FILE_BUTTON_WIDTH)
        container_layout.addWidget(line_edit, 1)
        container_layout.addWidget(browse_btn, 0)

        def _choose_file():
            start_dir = line_edit.text() or ""
            path, _ = QFileDialog.getOpenFileName(self, "Выбор файла", start_dir)
            if path:
                line_edit.setText(path)

        browse_btn.clicked.connect(_choose_file)
        container.setProperty("line_edit", line_edit)
        container.setMinimumWidth(self.TEXT_MIN_WIDTH + self.FILE_BUTTON_WIDTH + self.FILE_BUTTON_SPACING)
        container.setMaximumWidth(self.TEXT_MAX_WIDTH + self.FILE_BUTTON_WIDTH + self.FILE_BUTTON_SPACING)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        return container

    def _create_info_label(self, text: str) -> QLabel:
        info_label = QLabel("ℹ️")
        info_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        info_label.setToolTip(text)
        return info_label


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
        
        # При смене операции закрываем настройки и возвращаемся к основному виду
        if self.settings_btn.isChecked():
            self.settings_btn.setChecked(False)

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
                self.global_settings,
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

