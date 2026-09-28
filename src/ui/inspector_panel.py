"""
Инспектор для правой панели.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal


DTYPE_OPTIONS = [
    ("int64",          "🔢 Целое (int64)"),
    ("float64",        "🔢 Дробное (float64)"),
    ("str",            "📝 Строка (str)"),
    ("datetime64[ns]", "📅 Дата (datetime)"),
    ("bool",           "☑ Логический (bool)"),
]


class InspectorPanel(QWidget):
    """Инспектор справа: настройки колонки."""

    column_updated = Signal(str, str, bool)   # name, display_name, visible
    column_cast_requested = Signal(str, str)  # name, new_dtype
    column_split_requested = Signal(str)      # name

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._current_column = None

        self._build_ui()
        self.show_empty()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(10)

        self.main_layout.addWidget(self.content)

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_empty(self):
        self._clear_content()
        self._current_column = None

        hint = QLabel("Выберите колонку слева,\nчтобы увидеть её настройки.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 13px;
            padding: 40px 20px;
        """)
        self.content_layout.addWidget(hint)
        self.content_layout.addStretch()

    def show_column(self, col_info: dict):
        self._clear_content()
        self._current_column = col_info

        display_name = col_info.get("display_name", col_info["name"])
        dtype = col_info["dtype"]
        visible = col_info.get("visible", True)

        # ЗАГОЛОВОК
        header = QLabel(f"📊 {display_name}")
        header.setStyleSheet(f"""
            color: {self.theme.primary_dark};
            font-size: 15px;
            font-weight: bold;
            padding-bottom: 8px;
            border-bottom: 2px solid {self.theme.primary};
        """)
        self.content_layout.addWidget(header)

        # ИНФОРМАЦИЯ
        info_label = QLabel("── ИНФОРМАЦИЯ ──")
        info_label.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin-top: 6px;
        """)
        self.content_layout.addWidget(info_label)

        info_grid = QWidget()
        info_layout = QVBoxLayout(info_grid)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        self._add_info_row(info_layout, "Текущий тип:", dtype)
        self._add_info_row(info_layout, "Уникальных:", str(col_info["n_unique"]))
        nulls = col_info.get("n_nulls", col_info.get("n_nullS", 0))
        self._add_info_row(info_layout, "Пустых:", str(nulls))

        self.content_layout.addWidget(info_grid)

        # РАЗДЕЛИТЕЛЬ
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background: {self.theme.border}; max-height: 1px;")
        self.content_layout.addWidget(divider)

        # НАСТРОЙКИ
        settings_label = QLabel("── НАСТРОЙКИ ──")
        settings_label.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin-top: 6px;
        """)
        self.content_layout.addWidget(settings_label)

        # Отображаемое имя
        label_name = QLabel("Отображаемое имя:")
        label_name.setStyleSheet(f"color: {self.theme.text_main}; font-size: 12px;")
        self.content_layout.addWidget(label_name)

        self.edit_display_name = QLineEdit(display_name)
        self.edit_display_name.setPlaceholderText(col_info["name"])
        self.edit_display_name.setStyleSheet(self._input_style())
        self.content_layout.addWidget(self.edit_display_name)

        # Видимость
        self.check_visible = QCheckBox("Показывать в таблице")
        self.check_visible.setChecked(visible)
        self.check_visible.setStyleSheet(f"""
            QCheckBox {{
                color: {self.theme.text_main};
                font-size: 12px;
                padding: 6px 0;
            }}
        """)
        self.content_layout.addWidget(self.check_visible)

        # РАЗДЕЛИТЕЛЬ
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background: {self.theme.border}; max-height: 1px; margin-top: 6px;")
        self.content_layout.addWidget(divider2)

        # ТИП ДАННЫХ
        dtype_label = QLabel("── ТИП ДАННЫХ ──")
        dtype_label.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin-top: 6px;
        """)
        self.content_layout.addWidget(dtype_label)

        hint = QLabel("Преобразует значения колонки")
        hint.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 11px;")
        self.content_layout.addWidget(hint)

        self.combo_dtype = QComboBox()
        for dtype_key, dtype_title in DTYPE_OPTIONS:
            self.combo_dtype.addItem(dtype_title, dtype_key)
        idx = 0
        for i, (key, _) in enumerate(DTYPE_OPTIONS):
            if key in dtype or dtype in key:
                idx = i
                break
        self.combo_dtype.setCurrentIndex(idx)
        self.combo_dtype.setStyleSheet(self._input_style())
        self.content_layout.addWidget(self.combo_dtype)

        self.btn_cast = QPushButton("Преобразовать")
        self.btn_cast.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.bg_panel};
                color: {self.theme.primary_text};
                border: 1px solid {self.theme.primary};
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                margin-top: 4px;
            }}
            QPushButton:hover {{
                background: {self.theme.primary_hover};
                color: {self.theme.primary_dark};
            }}
        """)
        self.btn_cast.clicked.connect(self._on_cast)
        self.content_layout.addWidget(self.btn_cast)

        # РАЗДЕЛИТЕЛЬ
        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setStyleSheet(f"background: {self.theme.border}; max-height: 1px; margin-top: 6px;")
        self.content_layout.addWidget(divider3)

        # ОПЕРАЦИИ
        ops_label = QLabel("── ОПЕРАЦИИ ──")
        ops_label.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.5px;
            margin-top: 6px;
        """)
        self.content_layout.addWidget(ops_label)

        self.btn_split = QPushButton("✂️  Разделить колонку")
        self.btn_split.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.bg_panel};
                color: {self.theme.primary_text};
                border: 1px solid {self.theme.primary};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                margin-top: 4px;
            }}
            QPushButton:hover {{
                background: {self.theme.primary_hover};
                color: {self.theme.primary_dark};
            }}
        """)
        self.btn_split.clicked.connect(self._on_split)
        self.content_layout.addWidget(self.btn_split)

        # РАЗДЕЛИТЕЛЬ
        divider4 = QFrame()
        divider4.setFrameShape(QFrame.HLine)
        divider4.setStyleSheet(f"background: {self.theme.border}; max-height: 1px; margin-top: 6px;")
        self.content_layout.addWidget(divider4)

        # КНОПКИ
        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 6, 0, 0)
        buttons_layout.setSpacing(6)

        self.btn_apply = QPushButton("Применить")
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.primary};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #6ea800; }}
        """)
        self.btn_apply.clicked.connect(self._on_apply)
        buttons_layout.addWidget(self.btn_apply)

        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {self.theme.bg_panel};
                color: {self.theme.primary_text};
                border: 1px solid {self.theme.border};
                padding: 6px 12px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {self.theme.primary_hover}; }}
        """)
        self.btn_reset.clicked.connect(self._on_reset)
        buttons_layout.addWidget(self.btn_reset)

        self.content_layout.addWidget(buttons)
        self.content_layout.addStretch()

    def _add_info_row(self, layout, label: str, value: str):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 12px;")
        lbl.setFixedWidth(100)
        row_layout.addWidget(lbl)

        val = QLabel(value)
        val.setStyleSheet(f"color: {self.theme.primary_dark}; font-size: 12px; font-weight: 600;")
        row_layout.addWidget(val)
        row_layout.addStretch()

        layout.addWidget(row)

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background: {self.theme.bg_card};
                border: 1px solid {self.theme.border};
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                color: {self.theme.text_main};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {self.theme.primary};
            }}
            QComboBox::drop-down {{ border: none; padding-right: 6px; }}
            QComboBox QAbstractItemView {{
                background: {self.theme.bg_card};
                border: 1px solid {self.theme.border};
                selection-background-color: {self.theme.primary_hover};
                selection-color: {self.theme.primary_dark};
                padding: 4px;
            }}
        """

    def _on_apply(self):
        if self._current_column is None:
            return
        name = self._current_column["name"]
        display_name = self.edit_display_name.text().strip() or name
        visible = self.check_visible.isChecked()
        self.column_updated.emit(name, display_name, visible)

    def _on_cast(self):
        if self._current_column is None:
            return
        name = self._current_column["name"]
        new_dtype = self.combo_dtype.currentData()
        self.column_cast_requested.emit(name, new_dtype)

    def _on_split(self):
        if self._current_column is None:
            return
        name = self._current_column["name"]
        self.column_split_requested.emit(name)

    def _on_reset(self):
        if self._current_column is None:
            return
        col = self._current_column
        self.edit_display_name.setText(col.get("display_name", col["name"]))
        self.check_visible.setChecked(col.get("visible", True))