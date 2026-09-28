"""
Темы оформления приложения: светлая и тёмная.
"""

from dataclasses import dataclass, field


# ============================================================
# Базовая тема
# ============================================================

@dataclass
class Theme:
    """Базовый класс темы. Общие поля."""
    
    name: str = "Theme"
    is_dark: bool = False
    
    # Основные цвета
    primary: str = "#87C800"
    primary_dark: str = "#003F0B"
    primary_text: str = "#195532"
    primary_hover: str = "#e9f5e9"
    
    # Фоны
    bg_page: str = "#f5f7f9"
    bg_card: str = "#ffffff"
    bg_panel: str = "#fafafa"
    bg_hover: str = "#f5f5f5"
    
    # Границы
    border: str = "#e5e7eb"
    border_focus: str = "#87C800"
    
    # Текст
    text_main: str = "#333333"
    text_muted: str = "#888888"
    text_inverse: str = "#ffffff"
    
    # Формы
    border_radius: int = 12
    border_radius_small: int = 6
    
    # Типографика
    font_family: str = "Segoe UI"
    font_size_base: int = 13
    font_size_small: int = 11
    font_size_large: int = 16
    
    def to_qss(self) -> str:
        """Возвращает QSS-стиль (Qt Style Sheet)."""
        return self._build_qss()
    
    def _build_qss(self) -> str:
        return f"""
        QMainWindow, QWidget {{
            background-color: {self.bg_page};
            color: {self.text_main};
            font-family: "{self.font_family}";
            font-size: {self.font_size_base}px;
        }}
        
        QMenuBar {{
            background-color: {self.bg_card};
            border-bottom: 1px solid {self.border};
            color: {self.text_main};
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            background: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QMenu {{
            background-color: {self.bg_card};
            border: 1px solid {self.border};
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 24px;
            color: {self.text_main};
        }}
        
        QMenu::item:selected {{
            background-color: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QPushButton {{
            background-color: {self.primary};
            color: {self.text_inverse};
            border: none;
            padding: 8px 16px;
            border-radius: {self.border_radius_small}px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: #6ea800;
        }}
        
        QPushButton:pressed {{
            background-color: #5a8a00;
        }}
        
        QPushButton:disabled {{
            background-color: {self.border};
            color: {self.text_muted};
        }}
        
        QLabel {{
            color: {self.text_main};
        }}
        
        QTreeWidget {{
            background-color: {self.bg_card};
            border: 1px solid {self.border};
            border-radius: {self.border_radius}px;
            outline: none;
            color: {self.text_main};
        }}
        
        QTreeWidget::item {{
            padding: 4px;
            color: {self.text_main};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QTreeWidget::item:hover {{
            background-color: {self.bg_hover};
        }}
        
        QSplitter::handle {{
            background-color: {self.border};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        QStatusBar {{
            background-color: {self.bg_card};
            border-top: 1px solid {self.border};
            color: {self.text_muted};
        }}
        
        QToolBar {{
            background-color: {self.bg_card};
            border-bottom: 1px solid {self.border};
            padding: 4px;
            spacing: 4px;
        }}
        
        QToolBar QToolButton {{
            color: {self.text_main};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        QToolBar QToolButton:hover {{
            background-color: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QTabWidget::pane {{
            border: none;
            background-color: {self.bg_page};
        }}
        
        QTabBar::tab {{
            background: {self.bg_panel};
            color: {self.text_muted};
            padding: 8px 20px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 13px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background: {self.bg_card};
            color: {self.primary_dark};
            border-bottom: 2px solid {self.primary};
            font-weight: 700;
        }}
        
        QTabBar::tab:hover {{
            background: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QTableView {{
            background: {self.bg_card};
            alternate-background-color: {self.bg_panel};
            gridline-color: {self.border};
            color: {self.text_main};
            border: none;
        }}
        
        QHeaderView::section {{
            background: {self.bg_panel};
            color: {self.primary_dark};
            padding: 6px 8px;
            border: none;
            border-right: 1px solid {self.border};
            border-bottom: 1px solid {self.border};
            font-weight: 600;
        }}
        
        QLineEdit, QComboBox {{
            background: {self.bg_card};
            border: 1px solid {self.border};
            border-radius: 4px;
            padding: 5px 8px;
            color: {self.text_main};
        }}
        
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {self.primary};
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 6px;
        }}
        
        QComboBox QAbstractItemView {{
            background: {self.bg_card};
            border: 1px solid {self.border};
            selection-background-color: {self.primary_hover};
            selection-color: {self.primary_dark};
            color: {self.text_main};
            padding: 4px;
        }}
        
        QCheckBox {{
            color: {self.text_main};
            spacing: 6px;
        }}
        
        QListWidget {{
            background: {self.bg_card};
            border: 1px solid {self.border};
            border-radius: {self.border_radius}px;
            color: {self.text_main};
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 6px 8px;
            color: {self.text_main};
        }}
        
        QListWidget::item:selected {{
            background: {self.primary_hover};
            color: {self.primary_dark};
        }}
        
        QListWidget::item:hover {{
            background: {self.bg_hover};
        }}
        
        QScrollBar:vertical {{
            background: {self.bg_page};
            width: 10px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background: {self.border};
            border-radius: 5px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {self.primary};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background: {self.bg_page};
            height: 10px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {self.border};
            border-radius: 5px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: {self.primary};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        QDialog {{
            background: {self.bg_card};
        }}
        
        QToolTip {{
            background: {self.bg_card};
            color: {self.text_main};
            border: 1px solid {self.border};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        """


# ============================================================
# Светлая тема (текущая)
# ============================================================

@dataclass
class LightTheme(Theme):
    """Светлая тема с зелёным акцентом."""
    
    name: str = "Светлая"
    is_dark: bool = False
    
    primary: str = "#87C800"
    primary_dark: str = "#003F0B"
    primary_text: str = "#195532"
    primary_hover: str = "#e9f5e9"
    
    bg_page: str = "#f5f7f9"
    bg_card: str = "#ffffff"
    bg_panel: str = "#fafafa"
    bg_hover: str = "#f5f5f5"
    
    border: str = "#e5e7eb"
    border_focus: str = "#87C800"
    
    text_main: str = "#333333"
    text_muted: str = "#888888"
    text_inverse: str = "#ffffff"


# ============================================================
# Тёмная тема (Airbnb-style с зелёным акцентом)
# ============================================================

@dataclass
class DarkTheme(Theme):
    """Тёмная тема в стиле Airbnb с зелёным акцентом."""
    
    name: str = "Тёмная"
    is_dark: bool = True
    
    # Акцент — наш зелёный, но чуть ярче для тёмного фона
    primary: str = "#87C800"
    primary_dark: str = "#E8EAED"       # В тёмной теме "тёмный" = светлый (для текста)
    primary_text: str = "#87C800"
    primary_hover: str = "#2D3A1F"      # Тёмно-зелёный для hover
    
    # Фоны
    bg_page: str = "#1A1D21"             # Основной фон (Airbnb dark)
    bg_card: str = "#252A30"             # Карточки
    bg_panel: str = "#20242A"            # Панели
    bg_hover: str = "#2D3238"            # Hover
    
    # Границы
    border: str = "#353A42"
    border_focus: str = "#87C800"
    
    # Текст
    text_main: str = "#E8EAED"
    text_muted: str = "#8B929A"
    text_inverse: str = "#1A1D21"        # Тёмный текст на зелёных кнопках


# ============================================================
# Глобальные экземпляры и переключение
# ============================================================

LIGHT_THEME = LightTheme()
DARK_THEME = DarkTheme()

_current_theme: Theme = LIGHT_THEME


def get_theme() -> Theme:
    """Получить текущую тему."""
    return _current_theme


def set_theme(theme: Theme):
    """Установить текущую тему."""
    global _current_theme
    _current_theme = theme


def toggle_theme() -> Theme:
    """Переключить между светлой и тёмной."""
    global _current_theme
    if _current_theme.is_dark:
        _current_theme = LIGHT_THEME
    else:
        _current_theme = DARK_THEME
    return _current_theme


# Для обратной совместимости — старая переменная `default_theme`
default_theme = LIGHT_THEME