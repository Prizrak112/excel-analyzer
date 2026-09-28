"""
Главное окно приложения Excel Analyzer.
"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QSplitter, QStackedWidget, QListWidget, QListWidgetItem,
    QTabWidget, QStatusBar, QToolBar, QFileDialog, QMessageBox, QInputDialog,
    QStyle, QFileIconProvider,
)
from PySide6.QtCore import Qt, QSize, QFileInfo
from PySide6.QtGui import QAction, QIcon

from src.config.theme import (
    get_theme, set_theme, toggle_theme,
    LIGHT_THEME, DARK_THEME,
)
from src.config.app_info import APP_WINDOW_TITLE
from src.config.settings import get_settings
from src.ui.columns_tree import ColumnsTree
from src.ui.inspector_panel import InspectorPanel
from src.ui.side_rail import SideRail
from src.ui.toast import ToastManager
from src.ui.split_dialog import SplitDialog
from src.ui.data_viewer import DataViewerWidget
from src.ui.code_editor import CodeEditorWidget
from src.core.code_generator import generate_script
from src.core.data_loader import DataLoader
from src.core.report_model import Report
from src.core.history import HistoryManager
from src.core.file_manager import FileManager
from src.core.commands import (
    ToggleColumnCommand,
    RenameColumnCommand,
    CastColumnCommand,
    ReorderColumnsCommand,
    SplitColumnCommand,
)


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.theme = get_theme()
        self.settings = get_settings()
        self.current_data = None
        self._edit_mode = False
        self._selected_column = None
        self._content_visible = False
        self.report = Report()
        self.history = HistoryManager(max_size=50)
        self.file_manager = FileManager()
        
        self.setWindowTitle(APP_WINDOW_TITLE)
        self.resize(1400, 900)
        
        self._build_menu()
        self._build_toolbar()
        self._build_ui()
        self._build_statusbar()
        
        self.setStyleSheet(self.theme.to_qss())
    
    # ============================================================
    # Меню
    # ============================================================
    
    def _build_menu(self):
        menubar = self.menuBar()
        
        # Правка
        edit_menu = menubar.addMenu("Правка")
        
        self.action_undo = QAction("↶  Отменить", self)
        self.action_undo.setShortcut("Ctrl+Z")
        self.action_undo.setEnabled(False)
        self.action_undo.triggered.connect(self._on_undo)
        edit_menu.addAction(self.action_undo)
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        action_open = QAction("Открыть Excel...", self)
        action_open.setShortcut("Ctrl+O")
        action_open.triggered.connect(self.open_file)
        file_menu.addAction(action_open)
        
        action_close = QAction("Закрыть файл", self)
        action_close.setShortcut("Ctrl+W")
        action_close.triggered.connect(self._close_active_file)
        file_menu.addAction(action_close)
        
        file_menu.addSeparator()
        
        action_save = QAction("Сохранить", self)
        action_save.setShortcut("Ctrl+S")
        file_menu.addAction(action_save)
        
        action_save_as = QAction("Сохранить как...", self)
        action_save_as.setShortcut("Ctrl+Shift+S")
        file_menu.addAction(action_save_as)
        
        file_menu.addSeparator()
        
        action_export = QAction("Экспорт в HTML", self)
        action_export.setShortcut("Ctrl+E")
        file_menu.addAction(action_export)
        
        file_menu.addSeparator()
        
        action_exit = QAction("Выход", self)
        action_exit.setShortcut("Alt+F4")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        # Данные
        data_menu = menubar.addMenu("Данные")
        
        action_load = QAction("Загрузить Excel...", self)
        action_load.triggered.connect(self.open_file)
        data_menu.addAction(action_load)
        
        data_menu.addSeparator()
        
        action_edit = QAction("Изменить порядок колонок", self)
        action_edit.triggered.connect(self._toggle_edit_mode)
        data_menu.addAction(action_edit)
        
        action_show_all = QAction("Показать все колонки", self)
        action_show_all.triggered.connect(self._show_all_columns)
        data_menu.addAction(action_show_all)
        
        action_hide_all = QAction("Скрыть все колонки", self)
        action_hide_all.triggered.connect(self._hide_all_columns)
        data_menu.addAction(action_hide_all)
        
        # Вид
        view_menu = menubar.addMenu("Вид")
        
        action_toggle_theme = QAction("🌓 Переключить тему", self)
        action_toggle_theme.setShortcut("Ctrl+T")
        action_toggle_theme.triggered.connect(self._on_toggle_theme)
        view_menu.addAction(action_toggle_theme)
        
        # Справка
        help_menu = menubar.addMenu("Справка")
        help_menu.addAction(QAction("О программе", self))
    
    def _build_toolbar(self):
        toolbar = QToolBar("Основные")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        action_open_tb = QAction("📂 Открыть", self)
        action_open_tb.triggered.connect(self.open_file)
        toolbar.addAction(action_open_tb)
        
        toolbar.addAction("💾 Сохранить")
        toolbar.addSeparator()
        
        self.action_undo_tb = QAction("↶ Отменить", self)
        self.action_undo_tb.setToolTip("Отменить последнее действие (Ctrl+Z)")
        self.action_undo_tb.setEnabled(False)
        self.action_undo_tb.triggered.connect(self._on_undo)
        toolbar.addAction(self.action_undo_tb)
        
        toolbar.addSeparator()
        
        toolbar.addAction("📊 Данные")
        toolbar.addAction("📈 График")
        toolbar.addAction("🔢 KPI")
        toolbar.addAction("📝 Текст")
        toolbar.addSeparator()
        toolbar.addAction("🌐 Экспорт HTML")
    
    # ============================================================
    # UI
    # ============================================================
    
    def _build_ui(self):
        main_splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self._build_left_panel()
        main_splitter.addWidget(left_panel)
        
        right_container = self._build_right_container()
        main_splitter.addWidget(right_container)
        
        main_splitter.setSizes([300, 1100])
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        
        self.main_splitter = main_splitter
        self.setCentralWidget(main_splitter)
    
    def _build_left_panel(self) -> QWidget:
        """Левая панель редактора: Файлы + Колонки."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # ==================== ФАЙЛЫ ====================
        files_header = QWidget()
        files_header_layout = QHBoxLayout(files_header)
        files_header_layout.setContentsMargins(0, 0, 0, 0)
        files_header_layout.setSpacing(4)
        
        label_files = QLabel("📁 ФАЙЛЫ")
        label_files.setStyleSheet(f"font-weight: bold; color: {self.theme.primary};")
        files_header_layout.addWidget(label_files)
        files_header_layout.addStretch()
        
        self.btn_add_file = QPushButton("＋")
        self.btn_add_file.setFixedSize(26, 26)
        self.btn_add_file.setToolTip("Открыть файл")
        self.btn_add_file.setCursor(Qt.PointingHandCursor)
        self.btn_add_file.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.primary};
                color: {self.theme.text_inverse};
                border: none;
                border-radius: 4px;
                font-family: "Segoe UI Symbol";
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{ background: #6ea800; }}
        """)
        self.btn_add_file.clicked.connect(self.open_file)
        files_header_layout.addWidget(self.btn_add_file)
        
        layout.addWidget(files_header)
        
        # Список файлов
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(120)
        self.files_list.setMaximumHeight(240)
        # Размер системных иконок
        self.files_list.setIconSize(QSize(20, 20))
        self.files_list.setStyleSheet(f"""
            QListWidget {{
                background: {self.theme.bg_card};
                border: 1px solid {self.theme.border};
                border-radius: 6px;
                color: {self.theme.text_main};
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
                color: {self.theme.text_main};
                min-height: 24px;
            }}
            QListWidget::item:selected {{
                background: {self.theme.primary_hover};
                color: {self.theme.primary};
            }}
            QListWidget::item:hover {{
                background: {self.theme.bg_hover};
            }}
        """)
        self.files_list.itemClicked.connect(self._on_file_clicked)
        self.files_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_list.customContextMenuRequested.connect(self._on_files_context_menu)
        layout.addWidget(self.files_list)
        
        # ==================== КОЛОНКИ ====================
        columns_header = QWidget()
        columns_header_layout = QHBoxLayout(columns_header)
        columns_header_layout.setContentsMargins(0, 0, 0, 0)
        columns_header_layout.setSpacing(4)
        
        label_cols = QLabel("📊 КОЛОНКИ ДАННЫХ")
        label_cols.setStyleSheet(f"font-weight: bold; color: {self.theme.primary};")
        columns_header_layout.addWidget(label_cols)
        columns_header_layout.addStretch()
        
        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.setFixedHeight(24)
        self._update_btn_edit_style()
        self.btn_edit.clicked.connect(self._toggle_edit_mode)
        columns_header_layout.addWidget(self.btn_edit)
        
        btn_show_all = QPushButton("Все")
        btn_show_all.setFixedHeight(24)
        btn_show_all.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.primary};
                color: {self.theme.text_inverse};
                border: none;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: #6ea800; }}
        """)
        btn_show_all.clicked.connect(self._show_all_columns)
        columns_header_layout.addWidget(btn_show_all)
        
        btn_reset = QPushButton("Сбросить")
        btn_reset.setFixedHeight(24)
        btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.bg_panel};
                color: {self.theme.text_main};
                border: 1px solid {self.theme.border};
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {self.theme.primary_hover}; }}
        """)
        btn_reset.clicked.connect(self._hide_all_columns)
        columns_header_layout.addWidget(btn_reset)
        
        layout.addWidget(columns_header)
        
        self.tree_columns = ColumnsTree()
        self.tree_columns.itemChanged.connect(self._on_column_item_changed)
        self.tree_columns.itemClicked.connect(self._on_column_clicked)
        self.tree_columns.order_changed.connect(self._on_columns_reordered)
        layout.addWidget(self.tree_columns, stretch=1)
        
        return widget
    
    def _build_center_panel(self) -> QWidget:
        """Центральная панель с вкладками: Редактор / Конструктор / Экспорт."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {self.theme.bg_page};
            }}
            QTabBar::tab {{
                background: {self.theme.bg_panel};
                color: {self.theme.text_muted};
                padding: 8px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {self.theme.bg_card};
                color: {self.theme.primary};
                border-bottom: 2px solid {self.theme.primary};
                font-weight: 700;
            }}
            QTabBar::tab:hover {{
                background: {self.theme.primary_hover};
                color: {self.theme.primary};
            }}
        """)
        
        # Вкладка 1: Редактор данных
        self.data_viewer = DataViewerWidget(self.theme)
        self.center_tabs.addTab(self.data_viewer, "📊  Редактор")
        
        # Вкладка 2: Конструктор
        constructor_stub = QLabel("🎨  Конструктор отчётов\n\nБудет здесь позже.")
        constructor_stub.setAlignment(Qt.AlignCenter)
        constructor_stub.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 14px;
            background: {self.theme.bg_card};
        """)
        self.center_tabs.addTab(constructor_stub, "🎨  Конструктор")
        
        # Вкладка 3: Код
        self.code_editor = CodeEditorWidget(self.theme)
        self.code_editor.btn_refresh.clicked.connect(self._refresh_code)
        self.code_editor.btn_copy.clicked.connect(self.code_editor.copy_to_clipboard)
        self.code_editor.btn_save.clicked.connect(self._save_code)
        self.center_tabs.addTab(self.code_editor, "🐍  Код")
        
        # Вкладка 4: Экспорт
        export_stub = QLabel("📤  Экспорт отчёта\n\nБудет здесь позже.")
        export_stub.setAlignment(Qt.AlignCenter)
        export_stub.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 14px;
            background: {self.theme.bg_card};
        """)
        self.center_tabs.addTab(export_stub, "📤  Экспорт")
        
        # Смена вкладки — обновляем левую панель
        self.center_tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.center_tabs)
        
        return widget
    
    def _build_right_container(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.center_panel = self._build_center_panel()
        layout.addWidget(self.center_panel, stretch=1)
        
        self.right_content = QStackedWidget()
        self.right_content.setMinimumWidth(280)
        self.right_content.setMaximumWidth(320)
        
        self.inspector = InspectorPanel(self.theme)
        self.inspector.column_updated.connect(self._on_inspector_apply)
        self.inspector.column_cast_requested.connect(self._on_column_cast)
        self.inspector.column_split_requested.connect(self._on_column_split)
        self.right_content.addWidget(self._wrap_with_title(self.inspector, "⚙️ ИНСПЕКТОР"))
        
        data_stub = QLabel("📊 Раздел «Данные»\n\nБудет здесь позже.")
        data_stub.setAlignment(Qt.AlignCenter)
        data_stub.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 13px; padding: 40px;")
        self.right_content.addWidget(self._wrap_with_title(data_stub, "📊 ДАННЫЕ"))
        
        links_stub = QLabel("🔗 Раздел «Связи»\n\nБудет здесь позже.")
        links_stub.setAlignment(Qt.AlignCenter)
        links_stub.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 13px; padding: 40px;")
        self.right_content.addWidget(self._wrap_with_title(links_stub, "🔗 СВЯЗИ"))
        
        style_stub = QLabel("🎨 Раздел «Стиль»\n\nБудет здесь позже.")
        style_stub.setAlignment(Qt.AlignCenter)
        style_stub.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 13px; padding: 40px;")
        self.right_content.addWidget(self._wrap_with_title(style_stub, "🎨 СТИЛЬ"))
        
        self.right_content.setCurrentIndex(0)
        self.right_content.hide()
        
        layout.addWidget(self.right_content)
        
        self.rail = SideRail(self.theme)
        self.rail.section_selected.connect(self._on_rail_section_selected)
        self.rail.theme_toggled.connect(self._on_toggle_theme)
        layout.addWidget(self.rail)
        
        self.right_container = container
        return container
    
    def _wrap_with_title(self, widget: QWidget, title: str) -> QWidget:
        container = QWidget()
        container.setObjectName("right_panel_container")
        
        container.setStyleSheet(f"""
            #right_panel_container {{
                background: {self.theme.bg_card};
                border: 1px solid {self.theme.border};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)
        
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        label = QLabel(title)
        label.setStyleSheet(f"""
            font-weight: bold;
            color: {self.theme.primary};
            font-size: 13px;
        """)
        header_layout.addWidget(label)
        header_layout.addStretch()
        
        btn_close = QPushButton("Свернуть")
        btn_close.setFixedHeight(26)
        btn_close.setMinimumWidth(90)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.primary};
                color: {self.theme.text_inverse};
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background: #6ea800; }}
        """)
        btn_close.clicked.connect(self._hide_content)
        header_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        layout.addWidget(widget, stretch=1)
        
        return container
    
    def _build_statusbar(self):
        status = QStatusBar()
        status.showMessage("✅ Готово.")
        self.setStatusBar(status)
    
    def closeEvent(self, event):
        """Обработка закрытия окна с плавным завершением Qt."""
        print("[MainWindow] Закрытие приложения...")
        
        if hasattr(self, '_close_timer'):
            try:
                self._close_timer.stop()
            except Exception:
                pass
        
        # Закрываем web_view корректно (если есть)
        if hasattr(self, 'web_view'):
            try:
                self.web_view.stop()
                self.web_view.page().deleteLater()
                self.web_view.deleteLater()
            except Exception:
                pass
        
        event.accept()
        
        # Даём Qt 100мс завершить потоки, потом форсированный выход
        from PySide6.QtCore import QTimer
        import os
        QTimer.singleShot(100, lambda: os._exit(0))
    
    # ============================================================
    # Файлы
    # ============================================================
    
    def _refresh_files_list(self):
        """Обновить список файлов с системными иконками Windows."""
        self.files_list.clear()
        
        active_id = self.file_manager.get_active_id()
        
        # Провайдер системных иконок
        icon_provider = QFileIconProvider()
        
        for entry in self.file_manager.get_all():
            # Системная иконка файла (Windows покажет Excel-иконку для .xlsx)
            file_info = QFileInfo(entry.data.source_path)
            icon = icon_provider.icon(file_info)
            
            # Fallback — если иконка не получена
            if icon.isNull():
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            
            # Активный / изменённый маркер
            marker = "● " if entry.id == active_id else "○ "
            modified = " *" if entry.is_modified else ""
            text = f"{marker}{entry.display_name}{modified}"
            
            item = QListWidgetItem(text)
            item.setIcon(icon)
            item.setData(Qt.UserRole, entry.id)
            item.setToolTip(entry.data.source_path)
            
            self.files_list.addItem(item)
    
    def _on_file_clicked(self, item):
        """Клик по файлу — переключение."""
        file_id = item.data(Qt.UserRole)
        if file_id is None:
            return
        
        self._switch_to_file(file_id)
    
    def _switch_to_file(self, file_id: str):
        """Переключиться на файл."""
        if not self.file_manager.set_active(file_id):
            return
        
        entry = self.file_manager.get_file(file_id)
        if entry is None:
            return
        
        # Обновляем текущие ссылки
        self.current_data = entry.data
        self.history = entry.history
        
        # Обновляем UI
        self._update_columns_tree(self.current_data)
        self._update_data_viewer(self.current_data)
        self._update_undo_buttons()
        self._refresh_files_list()
        
        self.statusBar().showMessage(
            f"📊 {entry.display_name}: {entry.data.rows_count:,} строк, "
            f"{entry.data.cols_count} колонок"
        )
    
    def _on_files_context_menu(self, position):
        """Контекстное меню для списка файлов."""
        from PySide6.QtWidgets import QMenu
        
        item = self.files_list.itemAt(position)
        if item is None:
            return
        
        file_id = item.data(Qt.UserRole)
        if file_id is None:
            return
        
        entry = self.file_manager.get_file(file_id)
        if entry is None:
            return
        
        menu = QMenu(self)
        action_close = menu.addAction(f"✕  Закрыть «{entry.display_name}»")
        
        action = menu.exec(self.files_list.mapToGlobal(position))
        
        if action == action_close:
            self._close_file(file_id)
    
    def _close_active_file(self):
        """Закрыть активный файл."""
        file_id = self.file_manager.get_active_id()
        if file_id:
            self._close_file(file_id)
    
    def _close_file(self, file_id: str):
        """Закрыть файл с подтверждением."""
        entry = self.file_manager.get_file(file_id)
        if entry is None:
            return
        
        # Спрашиваем, если есть изменения
        if entry.is_modified:
            reply = QMessageBox.question(
                self, "Закрыть файл?",
                f"Файл «{entry.display_name}» был изменён.\n"
                f"Закрыть без сохранения?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Удаляем
        self.file_manager.remove_file(file_id)
        
        # Если ещё есть файлы — переключаемся на активный
        active = self.file_manager.get_active()
        if active:
            self.current_data = active.data
            self.history = active.history
            self._update_columns_tree(self.current_data)
            self._update_data_viewer(self.current_data)
        else:
            self.current_data = None
            self.history = HistoryManager(max_size=50)
            self.tree_columns.clear()
            self.data_viewer.clear()
        
        self._update_undo_buttons()
        self._refresh_files_list()
        
        ToastManager.info("Файл закрыт", f"«{entry.display_name}»", self.theme)
    
    def _on_tab_changed(self, index: int):
        """Смена вкладки."""
        print(f"[UI] Активная вкладка: {index}")
        
        # Вкладка «Код» — обновляем скрипт
        if index == 2:
            self._refresh_code()
    
    def _refresh_code(self):
        """Перегенерировать Python-скрипт из истории операций."""
        if self.current_data is None:
            self.code_editor.set_code(
                "# Файл не загружен\n"
                "# Загрузите XLSX-файл и сделайте изменения — скрипт появится здесь"
            )
            return
        
        try:
            # Получаем операции активного файла
            entry = self.file_manager.get_active()
            if entry is None:
                return
            
            operations = entry.operations.get_all()
            
            if not operations:
                self.code_editor.set_code(
                    "# Операций пока нет\n"
                    "# Сделайте какие-нибудь действия с данными — они появятся здесь"
                )
                return
            
            # Генерируем скрипт
            from pathlib import Path
            source_path = entry.data.source_path
            sheet_name = entry.data.sheet_name or "Sheet1"
            
            code = generate_script(
                operations=operations,
                file_name=source_path,
                sheet_name=sheet_name,
                reset_index=False,
            )
            
            self.code_editor.set_code(code)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.code_editor.set_code(f"# Ошибка генерации:\n# {type(e).__name__}: {e}")
    
    def _save_code(self):
        """Сохранить сгенерированный скрипт в файл."""
        if self.current_data is None:
            return
        
        entry = self.file_manager.get_active()
        if entry is None:
            return
        
        # Имя по умолчанию — на основе исходного файла
        from pathlib import Path
        stem = Path(entry.data.source_path).stem
        default_name = f"{stem}_processed.py"
        
        self.code_editor.save_to_file(default_name)
    
    # ============================================================
    # Тема
    # ============================================================
    
    def _on_toggle_theme(self):
        """Переключить тему с плавной анимацией."""
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        
        if hasattr(self, '_theme_animating') and self._theme_animating:
            return
        self._theme_animating = True
        
        was_content_visible = self._content_visible
        selected_column = self._selected_column
        active_tab = self.center_tabs.currentIndex() if hasattr(self, 'center_tabs') else 0
        active_rail_section = self.rail.get_active_section() if hasattr(self, 'rail') else "inspector"
        
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        
        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutCubic)
        
        self._fade_out_anim = fade_out
        self._fade_effect = effect
        
        self._theme_phase2_data = {
            "was_content_visible": was_content_visible,
            "selected_column": selected_column,
            "active_tab": active_tab,
            "active_rail_section": active_rail_section,
        }
        
        fade_out.finished.connect(self._theme_phase2)
        fade_out.start()
    
    def _theme_phase2(self):
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        
        data = self._theme_phase2_data
        
        new_theme = toggle_theme()
        self.theme = new_theme
        print(f"[UI] Тема переключена: {new_theme.name}")
        
        name = "dark" if new_theme.is_dark else "light"
        self.settings.set_theme_name(name)
        
        self._rebuild_ui()
        
        self._content_visible = data["was_content_visible"]
        self._selected_column = data["selected_column"]
        
        if data["was_content_visible"]:
            self.right_content.show()
        
        if hasattr(self, 'center_tabs'):
            self.center_tabs.setCurrentIndex(data["active_tab"])
        
        if hasattr(self, 'rail'):
            self.rail.set_active_section(data["active_rail_section"])
        
        if self.current_data:
            self._update_columns_tree(self.current_data)
            self._update_data_viewer(self.current_data)
            
            if data["selected_column"] and data["was_content_visible"]:
                col_info = self.current_data.get_column_info(data["selected_column"])
                if col_info:
                    self.inspector.show_column(col_info)
        
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        
        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(150)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InCubic)
        
        self._fade_in_anim = fade_in
        fade_in.finished.connect(self._theme_phase3)
        fade_in.start()
    
    def _theme_phase3(self):
        self.setGraphicsEffect(None)
        self._theme_animating = False
        
        theme_name = "тёмная" if self.theme.is_dark else "светлая"
        ToastManager.info("Тема изменена", f"Включена {theme_name} тема", self.theme)
    
    def _rebuild_ui(self):
        """Полная пересборка UI с новой темой."""
        from PySide6.QtWidgets import QToolBar
        
        self.setStyleSheet(self.theme.to_qss())
        
        self.menuBar().clear()
        for toolbar in self.findChildren(QToolBar):
            self.removeToolBar(toolbar)
            toolbar.deleteLater()
        
        self._build_menu()
        self._build_toolbar()
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self._build_left_panel()
        main_splitter.addWidget(left_panel)
        
        right_container = self._build_right_container()
        main_splitter.addWidget(right_container)
        
        main_splitter.setSizes([300, 1100])
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        
        self.main_splitter = main_splitter
        
        old = self.centralWidget()
        self.setCentralWidget(main_splitter)
        if old:
            old.deleteLater()
        
        # Восстанавливаем список файлов
        self._refresh_files_list()
    
    # ============================================================
    # Undo
    # ============================================================
    
    def _on_undo(self):
        if not self.history.can_undo():
            return
        
        ok, description = self.history.undo()
        
        if ok:
            ToastManager.info("Отменено", description, self.theme)
            self.statusBar().showMessage(f"↶ Отменено: {description}")
            
            # Помечаем файл как изменённый
            active_id = self.file_manager.get_active_id()
            if active_id:
                self.file_manager.mark_modified(active_id)
                self._refresh_files_list()
        
        self._update_undo_buttons()
    
    def _update_undo_buttons(self):
        can = self.history.can_undo()
        self.action_undo.setEnabled(can)
        self.action_undo_tb.setEnabled(can)
        
        if can:
            desc = self.history.get_last_description()
            self.action_undo.setToolTip(f"Отменить: {desc}")
            self.action_undo_tb.setToolTip(f"Отменить: {desc}")
        else:
            self.action_undo.setToolTip("Нечего отменять")
            self.action_undo_tb.setToolTip("Нечего отменять")
    
    # ============================================================
    # Открытие файла
    # ============================================================
    
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Открыть Excel-файл", "",
            "Excel файлы (*.xlsx *.xls);;Все файлы (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            # Проверяем, не открыт ли уже
            for entry in self.file_manager.get_all():
                if entry.data.source_path == filepath:
                    self._switch_to_file(entry.id)
                    ToastManager.info("Файл уже открыт", f"«{entry.display_name}»", self.theme)
                    return
            
            sheets = DataLoader.get_excel_sheets(filepath)
            
            if len(sheets) > 1:
                sheet, ok = QInputDialog.getItem(
                    self, "Выбор листа",
                    f"Файл содержит {len(sheets)} листов.\nВыберите лист:",
                    sheets, 0, False
                )
                if not ok:
                    return
                sheet_name = sheet
            else:
                sheet_name = sheets[0] if sheets else 0
            
            data = DataLoader.load(filepath, sheet_name)
            
            # Добавляем в менеджер
            file_id = self.file_manager.add_file(data)
            
            # ← СВЯЗЫВАЕМ file_id с data
            data.file_id = file_id
            data.operations = self.file_manager.get_file(file_id).operations
            
            # Обновляем ссылки
            entry = self.file_manager.get_active()
            self.current_data = entry.data
            self.history = entry.history
            
            self._update_columns_tree(self.current_data)
            self._update_data_viewer(self.current_data)
            self._update_undo_buttons()
            self._refresh_files_list()
            
            self.statusBar().showMessage(
                f"✅ Загружено: {data.rows_count:,} строк, {data.cols_count} колонок"
            )
            ToastManager.success("Файл загружен", f"«{entry.display_name}»", self.theme)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "Ошибка загрузки",
                f"Не удалось загрузить файл:\n\n{type(e).__name__}: {e}"
            )
    
    def _update_data_viewer(self, data):
        if data is None:
            self.data_viewer.clear()
            return
        
        visible = data.visible_columns if data.visible_columns else list(data.columns)
        df = data.dataframe[visible].copy()
        
        rename_map = {c: data.get_display_name(c) for c in df.columns}
        df = df.rename(columns=rename_map)
        
        info = f"{data.rows_count:,} строк × {data.cols_count} колонок"
        self.data_viewer.set_data(df, info)
    
    # ============================================================
    # События изменений
    # ============================================================
    
    def _on_columns_changed(self):
        if self.current_data:
            self._update_columns_tree(self.current_data)
            self._update_data_viewer(self.current_data)
            
            # Помечаем изменённым
            active_id = self.file_manager.get_active_id()
            if active_id:
                self.file_manager.mark_modified(active_id)
                self._refresh_files_list()
            
            # ← Обновляем код, если открыта вкладка «Код»
            if hasattr(self, 'center_tabs') and self.center_tabs.currentIndex() == 2:
                self._refresh_code()
            
            if self._selected_column and self.right_content.isVisible():
                col_info = self.current_data.get_column_info(self._selected_column)
                if col_info:
                    self.inspector.show_column(col_info)
    
    def _on_column_meta_changed(self, name: str):
        self._on_columns_changed()
    
    # ============================================================
    # Рельса и контент
    # ============================================================
    
    def _on_rail_section_selected(self, key: str):
        index_map = {"inspector": 0, "data": 1, "links": 2, "style": 3}
        idx = index_map.get(key, 0)
        self.right_content.setCurrentIndex(idx)
        
        if key == "inspector" and self._selected_column and self.current_data:
            col_info = self.current_data.get_column_info(self._selected_column)
            if col_info:
                self.inspector.show_column(col_info)
        
        self._show_content()
    
    def _show_content(self):
        if self._content_visible:
            return
        self._content_visible = True
        self.right_content.show()
    
    def _hide_content(self):
        if not self._content_visible:
            return
        self._content_visible = False
        self.right_content.hide()
    
    # ============================================================
    # Режим редактирования колонок
    # ============================================================
    
    def _toggle_edit_mode(self):
        self._edit_mode = not self._edit_mode
        self.tree_columns.set_edit_mode(self._edit_mode)
        self._update_columns_display()
        self._update_btn_edit_style()
    
    def _update_btn_edit_style(self):
        if self._edit_mode:
            self.btn_edit.setText("Готово")
            self.btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background: {self.theme.primary};
                    color: {self.theme.text_inverse};
                    border: none;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background: #6ea800; }}
            """)
        else:
            self.btn_edit.setText("Изменить")
            self.btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background: {self.theme.bg_panel};
                    color: {self.theme.text_main};
                    border: 1px solid {self.theme.border};
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background: {self.theme.primary_hover}; }}
            """)
    
    def _update_columns_display(self):
        if self.current_data is None:
            return
        self._update_columns_tree(self.current_data)
    
    # ============================================================
    # Дерево колонок
    # ============================================================
    
    def _update_columns_tree(self, data):
        self.tree_columns.blockSignals(True)
        self.tree_columns.clear()
        
        if data is None:
            self.tree_columns.blockSignals(False)
            return
        
        columns_info = data.get_columns_info()
        info_by_name = {c["name"]: c for c in columns_info}
        
        # Роли убраны — иконка одна для всех колонок
        column_map = {col_name: "📊" for col_name in data.column_order}
        self.tree_columns.set_column_map(column_map)
        
        for col_name in data.column_order:
            info = info_by_name.get(col_name)
            if not info:
                continue
            
            visible = info["visible"]
            display_name = info["display_name"]
            icon = "📊"
            
            if self._edit_mode:
                text = f"⋮⋮ {icon} {display_name}"
            else:
                text = f"{icon} {display_name}"
            
            item = QTreeWidgetItem([text])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            state = Qt.Checked if visible else Qt.Unchecked
            item.setCheckState(0, state)
            item.setData(0, Qt.UserRole, col_name)
            
            self.tree_columns.addTopLevelItem(item)
        
        self.tree_columns.blockSignals(False)
    
    def _on_column_item_changed(self, item, column):
        if self._edit_mode:
            return
        col_name = item.data(0, Qt.UserRole)
        if col_name is None:
            return
        
        is_checked = item.checkState(0) == Qt.Checked
        
        cmd = ToggleColumnCommand(
            data=self.current_data,
            column=col_name,
            visible=is_checked,
            on_change=self._on_columns_changed,
        )
        
        self.history.execute(cmd)
        self._update_undo_buttons()
    
    def _on_column_clicked(self, item, column):
        # Защита от клика по пустому месту
        if item is None:
            return
        if self._edit_mode:
            return
        
        col_name = item.data(0, Qt.UserRole)
        if col_name is None:
            return
        
        self._selected_column = col_name
        
        if self.current_data and self.right_content.isVisible():
            col_info = self.current_data.get_column_info(col_name)
            if col_info:
                self.inspector.show_column(col_info)
    
    def _on_columns_reordered(self, new_order: list):
        if self.current_data is None:
            return
        
        cmd = ReorderColumnsCommand(
            data=self.current_data,
            new_order=new_order,
            on_change=self._on_columns_changed,
        )
        
        self.history.execute(cmd)
        self._update_undo_buttons()
    
    # ============================================================
    # Обработчики инспектора
    # ============================================================
    
    def _on_inspector_apply(self, name: str, display_name: str, visible: bool):
        if self.current_data is None:
            return
        
        changes = []
        
        prev_display = self.current_data.get_display_name(name)
        if display_name and display_name != prev_display:
            cmd = RenameColumnCommand(
                data=self.current_data,
                column=name,
                new_name=display_name,
                on_change=self._on_columns_changed,
            )
            self.history.execute(cmd)
            changes.append("имя")
        
        prev_visible = self.current_data.is_column_visible(name)
        if visible != prev_visible:
            cmd = ToggleColumnCommand(
                data=self.current_data,
                column=name,
                visible=visible,
                on_change=self._on_columns_changed,
            )
            self.history.execute(cmd)
            changes.append("видимость")
        
        self._update_undo_buttons()
        
        if changes:
            ToastManager.success(
                "Изменения применены",
                f"Колонка «{display_name}»: {', '.join(changes)}",
                self.theme
            )
        else:
            ToastManager.info("Нечего применять", "Изменений не было", self.theme)
    
    def _on_column_cast(self, name: str, new_dtype: str):
        if self.current_data is None:
            return
        
        old_dtype = "unknown"
        display_name = name
        info = self.current_data.get_column_info(name)
        if info:
            old_dtype = info["dtype"]
            display_name = info["display_name"]
        
        cmd = CastColumnCommand(
            data=self.current_data,
            column=name,
            new_dtype=new_dtype,
            on_change=self._on_columns_changed,
        )
        
        self.history.execute(cmd)
        
        if cmd.was_successful:
            info = self.current_data.get_column_info(name)
            if info:
                display_name = info["display_name"]
                new_dtype_actual = info["dtype"]
                self.inspector.show_column(info)
            
            pretty_old = self._format_dtype(old_dtype)
            pretty_new = self._format_dtype(new_dtype_actual)
            
            msg = f"«{display_name}»\n{pretty_old} → {pretty_new}"
            self.statusBar().showMessage(f"✅ «{display_name}»: {pretty_old} → {pretty_new}")
            ToastManager.success("Тип данных изменён", msg, self.theme)
        else:
            ToastManager.error(
                "Ошибка преобразования",
                f"«{display_name}»\n{cmd.message}",
                self.theme
            )
        
        self._update_undo_buttons()
    
    def _on_column_split(self, name: str):
        if self.current_data is None:
            return
        
        dialog = SplitDialog(self.current_data, name, self.theme, self)
        
        if dialog.exec() != SplitDialog.Accepted or not dialog.result_data:
            return
        
        rd = dialog.result_data
        mode = rd["mode"]
        
        if mode == "visual":
            rules = rd.get("rules", [])
            new_names = rd["new_names"]
            
            if not rules:
                ToastManager.error("Нет правил", "Правила не были определены", self.theme)
                return
            
            n_cols = len(rules) + 1
            if len(new_names) < n_cols:
                base = new_names[0] if new_names else name
                new_names = [f"{base}_{i+1}" for i in range(n_cols)]
            else:
                new_names = new_names[:n_cols]
            
            params = {"rules": rules}
        else:
            new_names = rd["new_names"]
            params = rd["params"]
        
        cmd = SplitColumnCommand(
            data=self.current_data,
            column=name,
            mode=mode,
            params=params,
            new_names=new_names,
            delete_original=rd["delete_original"],
            on_change=self._on_columns_changed,
        )
        
        self.history.execute(cmd)
        
        if cmd.was_successful:
            ToastManager.success("Колонка разделена", cmd.message, self.theme)
        else:
            ToastManager.error("Ошибка разделения", cmd.message, self.theme)
        
        self._update_undo_buttons()
    
    def _format_dtype(self, dtype: str) -> str:
        mapping = {
            "int64":          "🔢 Целое (int64)",
            "float64":        "🔢 Дробное (float64)",
            "str":            "📝 Строка (str)",
            "object":         "📝 Строка (str)",
            "datetime64[ns]": "📅 Дата (datetime)",
            "bool":           "☑ Логический (bool)",
        }
        key = dtype.replace("'", "").replace('"', "").strip()
        return mapping.get(key, f"❔ {dtype}")
    
    # ============================================================
    # Кнопки видимости
    # ============================================================
    
    def _show_all_columns(self):
        if self.current_data is None:
            return
        self.tree_columns.blockSignals(True)
        self._set_all_checkboxes(Qt.Checked)
        self.tree_columns.blockSignals(False)
        self.current_data.show_all_columns()
        self._on_columns_changed()
    
    def _hide_all_columns(self):
        if self.current_data is None:
            return
        self.tree_columns.blockSignals(True)
        self._set_all_checkboxes(Qt.Unchecked)
        self.tree_columns.blockSignals(False)
        self.current_data.hide_all_columns()
        self._on_columns_changed()
    
    def _set_all_checkboxes(self, state):
        for i in range(self.tree_columns.topLevelItemCount()):
            item = self.tree_columns.topLevelItem(i)
            item.setCheckState(0, state)