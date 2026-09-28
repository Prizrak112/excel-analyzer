"""
Виджет редактора данных на основе QTableView.
Быстрый просмотр и редактирование больших таблиц (50 000+ строк).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QAbstractItemView, QHeaderView, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor


class DataFrameModel(QAbstractTableModel):
    """Модель для QTableView на основе DataFrame."""
    
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self._df = df
        self._dtype_colors = {}
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._df)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            value = self._df.iat[row, col]
            if value is None:
                return ""
            # Проверка на NaN
            try:
                import pandas as pd
                if pd.isna(value):
                    return "—"
            except Exception:
                pass
            # Форматирование чисел
            if isinstance(value, float):
                if value == int(value):
                    return f"{int(value):,}"
                return f"{value:,.2f}"
            if isinstance(value, int):
                return f"{value:,}"
            return str(value)
        
        elif role == Qt.TextAlignmentRole:
            value = self._df.iat[row, col]
            if isinstance(value, (int, float)):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        
        elif role == Qt.ForegroundRole:
            value = self._df.iat[row, col]
            try:
                import pandas as pd
                if pd.isna(value):
                    return QColor("#b0b0b0")
            except Exception:
                pass
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(section + 1)
        
        elif role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)
        
        return None
    
    def update_dataframe(self, df):
        """Обновить DataFrame в модели."""
        self.beginResetModel()
        self._df = df
        self.endResetModel()


class DataViewerWidget(QWidget):
    """Виджет редактора данных."""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._model = None
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Панель сверху
        top_bar = QWidget()
        top_bar.setStyleSheet(f"""
            background: {self.theme.bg_card};
            border-bottom: 1px solid {self.theme.border};
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(8)
        
        self.label_info = QLabel("Данные не загружены")
        self.label_info.setStyleSheet(f"""
            color: {self.theme.text_muted};
            font-size: 12px;
        """)
        top_layout.addWidget(self.label_info)
        top_layout.addStretch()
        
        layout.addWidget(top_bar)
        
        # Таблица
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.verticalHeader().setMinimumWidth(50)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        
        self.table.setStyleSheet(f"""
            QTableView {{
                background: {self.theme.bg_card};
                alternate-background-color: {self.theme.bg_panel};
                gridline-color: {self.theme.border};
                color: {self.theme.text_main};
                font-size: 12px;
                border: none;
                selection-background-color: {self.theme.primary_hover};
                selection-color: {self.theme.primary};
            }}
            QTableView::corner {{
                background: {self.theme.bg_panel};
                border: none;
                border-right: 1px solid {self.theme.border};
                border-bottom: 1px solid {self.theme.border};
            }}
            QHeaderView::section {{
                background: {self.theme.bg_panel};
                color: {self.theme.primary};
                padding: 6px 8px;
                border: none;
                border-right: 1px solid {self.theme.border};
                border-bottom: 1px solid {self.theme.border};
                font-weight: 600;
                font-size: 12px;
            }}
            QHeaderView::section:hover {{
                background: {self.theme.primary_hover};
            }}
            QTableCornerButton::section {{
                background: {self.theme.bg_panel};
                border: none;
                border-right: 1px solid {self.theme.border};
                border-bottom: 1px solid {self.theme.border};
            }}
            
            /* ===== СКРОЛЛБАРЫ ===== */
            QScrollBar:vertical {{
                background: {self.theme.bg_panel};
                width: 12px;
                margin: 0;
                border: none;
                border-left: 1px solid {self.theme.border};
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme.border};
                min-height: 30px;
                border-radius: 5px;
                margin: 2px 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.theme.primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background: {self.theme.bg_panel};
                height: 12px;
                margin: 0;
                border: none;
                border-top: 1px solid {self.theme.border};
            }}
            QScrollBar::handle:horizontal {{
                background: {self.theme.border};
                min-width: 30px;
                border-radius: 5px;
                margin: 3px 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {self.theme.primary};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
                background: none;
                border: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        
        layout.addWidget(self.table, stretch=1)
    
    def set_data(self, df, info_text: str = ""):
        """Установить данные для отображения."""
        self._model = DataFrameModel(df, self.table)
        self.table.setModel(self._model)
        
        # Авто-ширина колонок (ограниченная)
        self.table.resizeColumnsToContents()
        for col in range(self.table.model().columnCount()):
            if self.table.columnWidth(col) > 300:
                self.table.setColumnWidth(col, 300)
        
        # Информация
        if not info_text:
            info_text = f"{len(df):,} строк × {len(df.columns)} колонок"
        self.label_info.setText(info_text)
    
    def clear(self):
        """Очистить таблицу."""
        self.table.setModel(None)
        self._model = None
        self.label_info.setText("Данные не загружены")