import sys
import uuid
from PySide6.QtCore import Qt, QSettings, QTimer, Signal, QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar,
    QToolButton, QPushButton, QComboBox, QLineEdit,
    QLabel, QStackedWidget, QPlainTextEdit, QFrame,
    QSizePolicy, QMainWindow, QApplication
)


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

    def save_value(self, local_key: str, value):
        self.settings.setValue(self.key(local_key), value)
        self._save_scheduler.schedule()


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
# Single tab widget - базовый универсальный интерфейс
# ----------------------------
class ScriptTab(QWidget):
    """
    Базовый универсальный интерфейс вкладки.
    Содержит только верхнюю панель управления (выбор скрипта, имя, запуск)
    и консоль. Содержимое вкладки загружается через систему плагинов.
    """
    request_rename = Signal(str)  # emitted when user changes tab name

    def __init__(self, settings: QSettings, tab_id: str, plugin_registry, parent=None):
        super().__init__(parent)

        # Debounced flush is useful for frequent setting writes.
        self._save_scheduler = DebouncedWriter(self._flush_settings, delay_ms=250, parent=self)
        self.ctx = TabContext(settings, tab_id, self._save_scheduler, parent=self)
        self.plugin_registry = plugin_registry

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Top bar (первая строчка: выбор скрипта, имя, запуск)
        top = QHBoxLayout()
        top.setSpacing(8)

        self.op_combo = QComboBox()
        for plugin in plugin_registry.get_all_plugins():
            self.op_combo.addItem(plugin.get_title(), plugin.get_key())

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Tab name")

        self.run_btn = QPushButton("Run")
        self.run_btn.setDefault(True)

        top.addWidget(QLabel("Operation:"))
        top.addWidget(self.op_combo, 2)
        top.addWidget(QLabel("Name:"))
        top.addWidget(self.name_edit, 2)
        top.addWidget(self.run_btn, 0)

        # --- Main content area = stacked widgets для плагинов
        self.stack = QStackedWidget()
        self._op_key_to_index = {}

        for idx, plugin in enumerate(plugin_registry.get_all_plugins()):
            w = plugin.create_widget(self.ctx)
            self.stack.addWidget(w)
            self._op_key_to_index[plugin.get_key()] = idx

        # --- Console at bottom (collapsible)
        self.console = CollapsibleConsole()

        root.addLayout(top)
        root.addWidget(self.stack, 1)
        root.addWidget(self.console, 0)

        # Restore per-tab state
        self._restore()

        # Hook up signals for auto-save
        self.op_combo.currentIndexChanged.connect(self._on_operation_changed)
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.run_btn.clicked.connect(self._on_run)

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
        self.stack.setCurrentIndex(self._op_key_to_index.get(op_key, 0))

        # Console expanded?
        expanded = self.ctx.settings.value(self.ctx.key("meta/console_expanded"), False, type=bool)
        self.console.btn.setChecked(expanded)
        self.console.set_expanded(expanded)

        # Keep console expanded state in sync
        self.console.btn.toggled.connect(lambda v: self.ctx.save_value("meta/console_expanded", v))

    def _on_operation_changed(self):
        op_key = self.op_combo.currentData()
        self.stack.setCurrentIndex(self._op_key_to_index.get(op_key, 0))
        self.ctx.save_value("meta/operation", op_key)

    def _on_name_changed(self, text: str):
        self.ctx.save_value("meta/name", text)
        self.request_rename.emit(text)

    def _on_run(self):
        # Получаем текущий плагин и запускаем его
        op_key = self.op_combo.currentData()
        tab_name = self.name_edit.text().strip() or "Unnamed"
        
        plugin = self.plugin_registry.get_plugin(op_key)
        if plugin:
            plugin.execute(self.ctx, self.console.append_text)
        else:
            self.console.append_text(f"[ERROR] Plugin '{op_key}' not found")

    def _flush_settings(self):
        # QSettings writes are generally buffered; sync ensures physical flush.
        # Use sparingly; that's why debounced.
        self.ctx.settings.sync()


# ----------------------------
# Main window with tabs + add tab button
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self, plugin_registry):
        super().__init__()

        self.settings = QSettings("RequiemTools", "UniversalScriptsUI")
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

        tab = ScriptTab(self.settings, tab_id, self.plugin_registry)
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

