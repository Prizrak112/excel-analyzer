"""
Кастомное дерево колонок с drag-n-drop.
Плоский список. Восстанавливает данные после drop.
"""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, Signal


class ColumnsTree(QTreeWidget):
    """Дерево колонок с drag-n-drop."""
    
    order_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setIndentation(0)
        self.setRootIsDecorated(False)
        
        self._edit_mode = False
        self._column_map = {}  # имя колонки → иконка
        
        # Drag по умолчанию выключен
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
    
    def set_edit_mode(self, enabled: bool):
        """Включает/выключает режим редактирования."""
        self._edit_mode = enabled
        
        if enabled:
            self.setDragDropMode(QAbstractItemView.InternalMove)
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDropIndicatorShown(True)
            self.setDefaultDropAction(Qt.MoveAction)
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setDragDropMode(QAbstractItemView.NoDragDrop)
            self.setDragEnabled(False)
            self.setAcceptDrops(False)
            self.setDropIndicatorShown(False)
            self.setCursor(Qt.ArrowCursor)
    
    def is_edit_mode(self) -> bool:
        return self._edit_mode
    
    def set_column_map(self, mapping: dict):
        """
        Устанавливает карту: имя колонки → иконка.
        mapping = {"Пробег": "🔢", "Тип_ТС": "📊", ...}
        """
        self._column_map = mapping or {}
    
    # ============================================================
    # Перехват drop
    # ============================================================
    
    def dropEvent(self, event):
        """Перехватываем drop, восстанавливаем данные, отправляем сигнал."""
        print("[dropEvent] Начало")
        
        source = self.currentItem()
        if source:
            print(f"[dropEvent] Source: text='{source.text(0)}', data='{source.data(0, Qt.UserRole)}'")
        
        # Qt делает перемещение
        super().dropEvent(event)
        
        # Восстанавливаем потерянные данные
        self._restore_all_data()
        
        # Собираем порядок
        new_order = self._collect_order()
        print(f"[dropEvent] Новый порядок: {new_order}")
        
        if new_order:
            self.order_changed.emit(new_order)
        
        print("[dropEvent] Конец")
    
    def _restore_all_data(self):
        """Восстанавливает data(0, Qt.UserRole) там, где Qt потерял его после drop."""
        restored_count = 0
        
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            col_data = item.data(0, Qt.UserRole)
            
            if col_data is None:
                # Ищем колонку по тексту
                text = item.text(0)
                # Убираем "⋮⋮ " и иконку
                clean = text.replace("⋮⋮ ", "").strip()
                # Убираем иконку (первый символ + пробел)
                # Попробуем найти в карте
                for col_name in self._column_map.keys():
                    if clean.endswith(col_name):
                        item.setData(0, Qt.UserRole, col_name)
                        restored_count += 1
                        print(f"[restore] Восстановлено: '{col_name}'")
                        break
        
        if restored_count == 0:
            print("[restore] Все данные на месте")
    
    # ============================================================
    # Сбор порядка
    # ============================================================
    
    def _collect_order(self) -> list[str]:
        order = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            col_name = item.data(0, Qt.UserRole)
            if col_name:
                order.append(col_name)
        return order
    
    def get_columns_order(self) -> list[str]:
        return self._collect_order()
    
    def update_item_display(self, item: QTreeWidgetItem, col_name: str, edit_mode: bool):
        if edit_mode:
            item.setText(0, f"⋮⋮ {col_name}")
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
        else:
            item.setText(0, col_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)