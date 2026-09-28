"""
Команды для Undo/Redo.
Каждая команда умеет do() и undo() и пишет операцию в историю файла.
"""

from src.core.history import Command


# ============================================================
# Утилита — запись операции
# ============================================================

def _log_operation(data, op_type: str, params: dict):
    """Записать операцию в историю файла (если есть)."""
    if data is None:
        return
    
    ops = getattr(data, "operations", None)
    if ops is None:
        return
    
    file_id = getattr(data, "file_id", "")
    ops.add_new(op_type, params, file_id)


# ============================================================
# Показать/скрыть колонку
# ============================================================

class ToggleColumnCommand(Command):
    """Показать или скрыть одну колонку."""
    
    def __init__(self, data, column: str, visible: bool, on_change):
        self._data = data
        self._column = column
        self._visible = visible
        self._on_change = on_change
        self._prev_visible = None
    
    def do(self):
        self._prev_visible = self._data.is_column_visible(self._column)
        self._data.toggle_column(self._column, self._visible)
        
        _log_operation(self._data, "toggle_column", {
            "column": self._column,
            "visible": self._visible,
        })
        
        self._data.invalidate_cache()
        self._on_change()
    
    def undo(self):
        if self._prev_visible is not None:
            self._data.toggle_column(self._column, self._prev_visible)
            ops = getattr(self._data, "operations", None)
            if ops:
                ops.pop_last()
            self._data.invalidate_cache()
            self._on_change()
    
    def description(self) -> str:
        action = "Показать" if self._visible else "Скрыть"
        name = self._data.get_display_name(self._column)
        return f"{action} колонку «{name}»"


# ============================================================
# Переименовать колонку
# ============================================================

class RenameColumnCommand(Command):
    """Изменить отображаемое имя колонки."""
    
    def __init__(self, data, column: str, new_name: str, on_change):
        self._data = data
        self._column = column
        self._new_name = new_name
        self._on_change = on_change
        self._prev_name = None
    
    def do(self):
        self._prev_name = self._data.get_display_name(self._column)
        self._data.set_display_name(self._column, self._new_name)
        
        _log_operation(self._data, "rename_column", {
            "column": self._column,
            "new_name": self._new_name,
            "prev_name": self._prev_name,
        })
        
        self._data.invalidate_cache()
        self._on_change()
    
    def undo(self):
        if self._prev_name is not None:
            if self._prev_name == self._column:
                if self._column in self._data.column_meta:
                    self._data.column_meta[self._column].pop("display_name", None)
            else:
                self._data.set_display_name(self._column, self._prev_name)
            
            ops = getattr(self._data, "operations", None)
            if ops:
                ops.pop_last()
            self._data.invalidate_cache()
            self._on_change()
    
    def description(self) -> str:
        return f"Переименовать колонку «{self._prev_name or self._column}» → «{self._new_name}»"


# ============================================================
# Сменить тип данных
# ============================================================

class CastColumnCommand(Command):
    """Преобразовать тип данных колонки."""
    
    def __init__(self, data, column: str, new_dtype: str, on_change):
        self._data = data
        self._column = column
        self._new_dtype = new_dtype
        self._on_change = on_change
        self._backup_series = None
        self._backup_dtype = None
        self._ok = False
        self._message = ""
    
    def do(self):
        self._backup_series = self._data.dataframe[self._column].copy()
        self._backup_dtype = self._data.dtypes.get(self._column, "")
        
        self._ok, self._message = self._data.cast_column(self._column, self._new_dtype)
        
        if self._ok:
            _log_operation(self._data, "cast_column", {
                "column": self._column,
                "new_dtype": self._new_dtype,
                "prev_dtype": self._backup_dtype,
            })
            
            self._data.invalidate_cache()
            self._on_change()
        else:
            # Откат значений при неудаче
            self._data.dataframe[self._column] = self._backup_series
            self._data.dtypes[self._column] = self._backup_dtype
            self._data.invalidate_cache()
    
    def undo(self):
        if not self._ok or self._backup_series is None:
            return
        
        self._data.dataframe[self._column] = self._backup_series
        self._data.dtypes[self._column] = self._backup_dtype
        
        ops = getattr(self._data, "operations", None)
        if ops:
            ops.pop_last()
        
        self._data.invalidate_cache()
        self._on_change()
    
    def description(self) -> str:
        name = self._data.get_display_name(self._column)
        return f"Преобразовать тип «{name}» в {self._new_dtype}"
    
    @property
    def was_successful(self) -> bool:
        return self._ok
    
    @property
    def message(self) -> str:
        return self._message


# ============================================================
# Изменить порядок колонок
# ============================================================

class ReorderColumnsCommand(Command):
    """Изменить порядок видимых колонок."""
    
    def __init__(self, data, new_order: list, on_change):
        self._data = data
        self._new_order = list(new_order)
        self._on_change = on_change
        self._prev_order = None
    
    def do(self):
        self._prev_order = list(self._data.visible_columns)
        self._data.reorder_visible_columns(self._new_order)
        
        _log_operation(self._data, "reorder_columns", {
            "new_order": self._new_order,
            "prev_order": self._prev_order,
        })
        
        self._data.invalidate_cache()
        self._on_change()
    
    def undo(self):
        if self._prev_order is not None:
            self._data.reorder_visible_columns(self._prev_order)
            ops = getattr(self._data, "operations", None)
            if ops:
                ops.pop_last()
            self._data.invalidate_cache()
            self._on_change()
    
    def description(self) -> str:
        return "Изменить порядок колонок"


# ============================================================
# Разделить колонку
# ============================================================

class SplitColumnCommand(Command):
    """Разделить колонку. Сохраняет backup DataFrame."""
    
    def __init__(self, data, column: str, mode: str, params: dict,
                 new_names: list, delete_original: bool, on_change):
        self._data = data
        self._column = column
        self._mode = mode
        self._params = params
        self._new_names = list(new_names)
        self._delete_original = delete_original
        self._on_change = on_change
        
        self._backup_df = None
        self._backup_columns = None
        self._backup_dtypes = None
        self._backup_meta = None
        self._backup_column_order = None
        self._backup_visible = None
        
        self._ok = False
        self._message = ""
    
    def do(self):
        self._backup_df = self._data.dataframe.copy()
        self._backup_columns = list(self._data.columns)
        self._backup_dtypes = dict(self._data.dtypes)
        self._backup_meta = {k: dict(v) for k, v in self._data.column_meta.items()}
        self._backup_column_order = list(self._data.column_order)
        self._backup_visible = list(self._data.visible_columns)
        
        if self._mode == "visual":
            self._ok, self._message = self._data.split_by_rules(
                self._column, self._params.get("rules", []),
                self._new_names, self._delete_original,
            )
        else:
            self._ok, self._message = self._data.split_column(
                self._column, self._mode, self._params,
                self._new_names, self._delete_original,
            )
        
        if self._ok:
            _log_operation(self._data, "split_column", {
                "column": self._column,
                "mode": self._mode,
                "params": self._params,
                "new_names": self._new_names,
                "delete_original": self._delete_original,
            })
            self._data.invalidate_cache()
            self._on_change()
    
    def undo(self):
        if not self._ok or self._backup_df is None:
            return
        
        self._data.dataframe = self._backup_df
        self._data.columns = self._backup_columns
        self._data.dtypes = self._backup_dtypes
        self._data.column_meta = self._backup_meta
        self._data.column_order = self._backup_column_order
        self._data.visible_columns = self._backup_visible
        self._data.cols_count = len(self._backup_columns)
        
        ops = getattr(self._data, "operations", None)
        if ops:
            ops.pop_last()
        
        self._data.invalidate_cache()
        self._on_change()
    
    def description(self) -> str:
        return f"Разделить колонку «{self._column}» на {len(self._new_names)} частей"
    
    @property
    def was_successful(self) -> bool:
        return self._ok
    
    @property
    def message(self) -> str:
        return self._message